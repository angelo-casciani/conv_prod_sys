import datetime
import json
import os

from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig, AutoConfig
from torch import bfloat16

import llm_factory_interface as factory_interface
from oracle import AnswerVerificationOracle
import uppaal_interface
from utility import log_to_file, retrieve_automata, retrieve_factory, load_csv_questions

class LLMPipeline:
    MODELS = {
        'metaai': ['meta-llama/Meta-Llama-3-8B-Instruct', 'meta-llama/Meta-Llama-3.1-8B-Instruct',
                   'meta-llama/Llama-3.2-1B-Instruct', 'meta-llama/Llama-3.2-3B-Instruct'],
        'mistral': ['mistralai/Mistral-7B-Instruct-v0.2', 'mistralai/Mistral-7B-Instruct-v0.3',
                    'mistralai/Mistral-Nemo-Instruct-2407', 'mistralai/Ministral-8B-Instruct-2410'],
        'qwen': ['Qwen/Qwen2.5-7B-Instruct'],
        'google': ['google/gemma-2-9b-it'],
        'microsoft': ['microsoft/phi-4'],
        'deepseek': ['deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', 'deepseek-ai/DeepSeek-R1-Distill-Llama-8B'],
        'openai': ['gpt-4o-mini']
    }
    TERMINATOR_TOKENS = {
        'metaai': "<|eot_id|>",
        'mistral': "[/INST]]",
        'qwen': "<|im_end|>",
        'microsoft': "<|im_sep|>"
    }
    TEMPLATE_MAPPING = {
        'metaai': 'template-llama_instruct',
        'mistral': 'template-mistral',
        'qwen': 'template-qwen',
        'microsoft': 'template-phi',
        'deepseek': 'template-deepseek'
    }
    RESPONSE_DELIMITERS = {
        'metaai': '<|start_header_id|>assistant<|end_header_id|>',
        'mistral': '[/INST]',
        'qwen': '<|im_start|>assistant',
        'microsoft': '<|im_start|>assistant<|im_sep|>',
        'deepseek': 'Assistant: '
    }

    def __init__(self, model_id_gateway, model_id_simulation, model_id_verification, hf_token, openai_auth, max_new_tokens):
        self.model_id_gateway = model_id_gateway
        self.model_id_simulation = model_id_simulation
        self.model_id_verification = model_id_verification
        self.hf_token = hf_token
        self.openai_auth = openai_auth
        self.max_new_tokens = max_new_tokens
        self.path_prompts = os.path.join(os.path.dirname(__file__), 'prompts.json')
        with open(self.path_prompts, 'r') as prompt_file:
            self.prompts = json.load(prompt_file)
        self.chain_simulation = self.initialize_chain(model_id_simulation)
        self.chain_verification = self.initialize_chain(model_id_verification)
        self.chain_gateway = self.initialize_chain(model_id_gateway)


    def initialize_model(self):
        """
        Initializes a transformer pipeline for text generation using the specified language model.
        
        Returns:
            generate_text: The configured text generation pipeline.
        """
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=bfloat16
        )
        model_config = AutoConfig.from_pretrained(
            self.model_id,
            token=self.hf_token
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            attn_implementation='flash_attention_2',
            config=model_config,
            quantization_config=bnb_config,
            device_map='auto',
            token=self.hf_token
        )
        model.eval()

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            token=self.hf_token
        )

        model_family = self.get_model_family()
        pipeline_params = {
            "model": model,
            "tokenizer": tokenizer,
            "return_full_text": True,
            "task": "text-generation",
            "do_sample": True,
            "max_new_tokens": self.max_new_tokens,
            "repetition_penalty": 1.1
        }

        if model_family in LLMPipeline.TERMINATOR_TOKENS:
            special_token = LLMPipeline.TERMINATOR_TOKENS[model_family]
            terminators = [
                tokenizer.eos_token_id,
                tokenizer.convert_tokens_to_ids(special_token)
            ]
            pipeline_params.update({
                "eos_token_id": terminators,
                "pad_token_id": tokenizer.eos_token_id
            })

        generate_text = pipeline(**pipeline_params)
        return generate_text


    def get_model_family(self):
        for family, models in LLMPipeline.MODELS.items():
            if self.model_id in models:
                return family
        return None


    def generate_prompt_template(self):
        model_family = self.get_model_family()
        template_key = LLMPipeline.TEMPLATE_MAPPING.get(model_family, 'template-generic')
        template = self.prompts.get(template_key, '')

        if "{conversation_history}" in template:
            return PromptTemplate.from_template(template, partial_variables={"conversation_history": ""})
        else:
            return PromptTemplate.from_template(template)


    def initialize_chain(self, model_id):
        if model_id not in LLMPipeline.MODELS['openai']:
            generate_text = self.initialize_model()
            hf_pipeline = HuggingFacePipeline(pipeline=generate_text)
            prompt = self.generate_prompt_template()
            chain = prompt | hf_pipeline
        else:
            chain = OpenAI(
                api_key=self.openai_auth,
            )

        return chain


    def parse_llm_answer(self, compl_answer):
        model_family = self.get_model_family()
        delimiter = LLMPipeline.RESPONSE_DELIMITERS.get(model_family, 'Answer:')

        index = compl_answer.find(delimiter)
        if index == -1:  # Delimiter not found
            return "", compl_answer

        prompt = compl_answer[:index + len(delimiter)]
        answer = compl_answer[index + len(delimiter):]

        return prompt, answer


    def produce_answer_gateway(self, question, answer_phase):
        prompt, answer = ('', '')
        if self.model_id_gateway not in LLMPipeline.MODELS['openai']:
            if answer_phase == 'routing':
                sys_mess = self.prompts.get('system_message_routing', '')
                context = self.prompts.get('context_routing', '')
            elif answer_phase == 'negative_response':
                sys_mess = self.prompts.get('system_message_negative', '')
                context = ''
            complete_answer = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt, answer = self.parse_llm_answer(complete_answer)
        else:
            if answer_phase == 'routing':
                sys_mess = self.prompts.get('system_message_routing', '')
                context = self.prompts.get('context_routing', '')
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.chat.completions.create(
                    model = self.model_id_gateway,
                    messages = [
                        {"role": "system", "content": f'{sys_mess}\nHere is the context: {context}\n'},
                        {"role": "user", "content": f'Here is the user question: {question}\nAnswer: '},
                    ]
                )
                answer = completion.choices[0].message.content.strip()
            elif answer_phase == 'negative_response':
                sys_mess = self.prompts.get('system_message_negative', '')
                context = ''
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.chat.completions.create(
                    model = self.model_id_gateway,
                    messages = [
                        {"role": "system", "content": f'{sys_mess}\nHere is the context: {context}\n'},
                        {"role": "user", "content": f'Here is the user question: {question}\nAnswer: '},
                    ]
                )
                answer = completion.choices[0].message.content.strip()

        return prompt, answer


    def produce_answer_simulation(self, question, modality):
        factory_data = retrieve_factory()
        station_names = ', '.join([station for station in factory_data['stations']])
        if self.model_id_simulation not in LLMPipeline.MODELS['openai']:
            sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
            context = self.prompts.get('context_simulation', '').replace('LABELS', station_names)
            complete_answer = self.chain_simulation.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt, answer = self.parse_llm_answer(complete_answer)
            #print(complete_answer)

            if 'evaluation' not in modality:
                results = factory_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results_sim', '')
                context = f"The labels for the stations are: {station_names}\nResults from the simulation: {results}"
                complete_answer = self.chain_gateway.invoke({"question": question,
                                                    "context": context,
                                                    "system_message": sys_mess})
                prompt, answer = self.parse_llm_answer(complete_answer)
        else:
            sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
            context = self.prompts.get('context_simulation', '').replace('LABELS', station_names)
            prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
            completion = self.chain_simulation.chat.completions.create(
                model = self.model_id_simulation,
                messages = [
                    {"role": "system", "content": f'{sys_mess}\nHere is the context: {context}\n'},
                    {"role": "user", "content": f'Here is the user question: {question}\nAnswer: '},
                ]
            )
            answer = completion.choices[0].message.content.strip()
            print(prompt + '\n' + answer)

            if 'evaluation' not in modality:
                results = factory_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results_sim', '')
                context = f"The labels for the stations are: {station_names}\nResults from the simulation: {results}"
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\n'
                completion = self.chain_gateway.chat.completions.create(
                    model = self.model_id_gateway,
                    messages = [
                        {"role": "system", "content": f'{sys_mess}\nHere is the context: {context}\n'},
                        {"role": "user", "content": f'Here is the user question: {question}\nAnswer: '},
                    ]
                )
                answer = completion.choices[0].message.content.strip()

        return prompt, answer


    def produce_answer_verification(self, question, modality):
        automata_data = retrieve_automata()
        if self.model_id_verification not in LLMPipeline.MODELS['openai']:
            sys_mess = self.prompts.get('system_message_verification', '') + self.prompts.get('shots_verification', '')
            context = self.prompts.get('context_verification', '').replace('STATES', str(list(automata_data['transitions'].keys())))
            complete_answer = self.chain_verification.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt, answer = self.parse_llm_answer(complete_answer)
            #print(complete_answer)

            if 'evaluation' not in modality:
                results = uppaal_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results', '')
                context = f'Results from Uppaal: {results}'
                complete_answer = self.chain_gateway.invoke({"question": question,
                                                    "context": context,
                                                    "system_message": sys_mess})
                prompt, answer = self.parse_llm_answer(complete_answer)
        else:
            sys_mess = self.prompts.get('system_message_verification', '') + self.prompts.get('shots_verification', '')
            context = self.prompts.get('context_verification', '').replace('STATES', str(list(automata_data['transitions'].keys())))
            prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
            completion = self.chain_verification.chat.completions.create(
                model = self.model_id_verification,
                messages = [
                    {"role": "system", "content": f'{sys_mess}\nHere is the context: {context}\n'},
                    {"role": "user", "content": f'Here is the user question: {question}\nAnswer: '},
                ]
            )
            answer = completion.choices[0].message.content.strip()
            print(prompt + '\n' + answer)

            if 'evaluation' not in modality:
                results = uppaal_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results', '')
                context = f'Results from Uppaal: {results}'
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.chat.completions.create(
                    model = self.model_id_gateway,
                    messages = [
                        {"role": "system", "content": f'{sys_mess}\nHere is the context: {context}\n'},
                        {"role": "user", "content": f'Here is the user question: {question}\nAnswer: '},
                    ]
                )
                answer = completion.choices[0].message.content.strip()
        return prompt, answer
    

    def generate_response(self, question, curr_datetime, info_run):
        complete_prompt, answer = self.produce_answer_gateway(question, 'routing')
        print(f'Prompt: {complete_prompt}\n')
        print(f'{answer}\n')
        print('--------------------------------------------------')

        if 'uppaal_verification' in answer.lower():
            complete_prompt, answer = self.produce_answer_verification(question, 'live')
        elif 'factory_simulation' in answer.lower():
            complete_prompt, answer = self.produce_answer_simulation(question, 'live')
        else:
            complete_prompt, answer = self.produce_answer_gateway(question, 'negative_response')

        print(f'Prompt: {complete_prompt}\n')
        print(f'{answer}\n')
        print('--------------------------------------------------')

        log_to_file(f'Query: {complete_prompt}\n\n{answer}\n\n##########################\n\n',
                    curr_datetime, info_run)


    def live_prompting(self, info_run):
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        while True:
            query = input('Insert the query you want to ask (type "quit" to exit): ')

            if query.lower() == 'quit':
                print("Exiting the chat.")
                break
            
            self.generate_response(query, current_datetime, info_run)
            print()


    def evaluate_performance(self, test_filename, info_run):
        questions = load_csv_questions(test_filename)
        oracle = AnswerVerificationOracle(info_run)
        count = 0
        prompt, answer = '', ''
        for el in questions:
            question = el[0]
            expected_answer = el[1]
            oracle.add_question_expected_answer_pair(question, expected_answer)
            if test_filename == 'simulation.csv':
                prompt, answer = self.produce_answer_simulation(question, 'evaluation-simulation')
            elif test_filename == 'verification.csv':
                prompt, answer = self.produce_answer_verification(question, 'evaluation-verification')
            elif test_filename == 'routing.csv':
                prompt, answer = self.produce_answer_gateway(question, 'routing')
            oracle.verify_answer(prompt, question, answer)
            count += 1
            print(f'Processing answer for question {count} of {len(questions)}...')

        print('Validation process completed. Check the output file.')
        oracle.write_results_to_file()