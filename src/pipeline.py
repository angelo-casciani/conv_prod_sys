import datetime
import json
import os
from typing import Dict, Tuple

from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig, AutoConfig
from torch import bfloat16

import llm_factory_interface as factory_interface
from oracle import AnswerVerificationOracle
import uppaal_interface
from utility import log_to_file, retrieve_automata, retrieve_factory, load_csv_questions
import pddl_interface
import tempfile

class LLMPipeline:
    MODELS = {
        'api': {
            'openai': ['gpt-4o-mini'],
            'google_genai': ['gemini-2.0-flash'],
            'anthropic': [],
        },
        'local': {
            'metaai': ['meta-llama/Meta-Llama-3-8B-Instruct', 'meta-llama/Meta-Llama-3.1-8B-Instruct',
                       'meta-llama/Llama-3.2-1B-Instruct', 'meta-llama/Llama-3.2-3B-Instruct'],
            'mistral': ['mistralai/Mistral-7B-Instruct-v0.2', 'mistralai/Mistral-7B-Instruct-v0.3',
                        'mistralai/Mistral-Nemo-Instruct-2407', 'mistralai/Ministral-8B-Instruct-2410'],
            'qwen': ['Qwen/Qwen2.5-7B-Instruct'],
            'google_genai': ['google/gemma-2-9b-it'],
            'microsoft': ['microsoft/phi-4'],
            'deepseek': ['deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', 'deepseek-ai/DeepSeek-R1-Distill-Llama-8B'],
        }
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
        self.model_family_gateway, self.model_type_gateway = self._get_model_family_type(self.model_id_gateway)
        self.model_family_simulation, self.model_type_simulation = self._get_model_family_type(model_id_simulation)
        self.model_family_verification, self.model_type_verification = self._get_model_family_type(model_id_verification)
        self.hf_token = hf_token
        self.openai_auth = openai_auth
        self.max_new_tokens = max_new_tokens
        self.path_prompts = os.path.join(os.path.dirname(__file__), 'prompts.json')
        self.factory_model = os.path.join(os.path.dirname(__file__), '..','models', 'lego_factory.json')
        self.pddl_domain = os.path.join(os.path.dirname(__file__), 'pddl', 'domain.pddl')
        with open(self.path_prompts, 'r') as prompt_file:
            self.prompts = json.load(prompt_file)
        with open(self.factory_model, 'r') as factory_file:
            self.factory_model = json.load(factory_file)
        self.chain_simulation = self._initialize_chain(model_id_simulation, self.model_family_simulation, self.model_type_simulation)
        self.chain_verification = self._initialize_chain(model_id_verification,self.model_family_simulation, self.model_type_simulation)
        self.chain_gateway = self._initialize_chain(model_id_gateway,self.model_family_simulation, self.model_type_simulation)


    def _initialize_local_model(self, model_id):
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
            model_id,
            token=self.hf_token
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            config=model_config,
            quantization_config=bnb_config,
            device_map='auto',
            token=self.hf_token
        )
        model.eval()

        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            token=self.hf_token
        )

        model_family = self._get_model_family_type()
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


    def _get_model_family_type(self, model_id):
        for model_type, families in LLMPipeline.MODELS.items():
            for family, models_in_family in families.items():
                if model_id in models_in_family:
                    return family, model_type
        return None, None


    def _generate_prompt_template(self, model_family):
        template_key = LLMPipeline.TEMPLATE_MAPPING.get(model_family, 'template-generic')
        template = self.prompts.get(template_key, '')

        return PromptTemplate.from_template(template)
    

    def _initialize_chain(self, model_id, model_family, model_type):
        if model_type == 'local':
            generate_text = self._initialize_local_model(model_id)
            model = HuggingFacePipeline(pipeline=generate_text)
        else:
            model = init_chat_model(model_id, model_provider=model_family, max_tokens = self.max_new_tokens)

        prompt = self._generate_prompt_template(model_family)
        chain = prompt | model

        return chain


    def _parse_llm_answer(self, complete_answer: str, model_type: str) -> Tuple[str, str]:
        if model_type == 'local':
            delimiter = LLMPipeline.RESPONSE_DELIMITERS.get(self.model_family, 'Answer:')

            index = complete_answer.find(delimiter)
            if index == -1:  # Delimiter not found
                return "", complete_answer

            prompt = complete_answer[:index + len(delimiter)]
            answer = complete_answer[index + len(delimiter):]
        else:
            answer = complete_answer
            prompt = ''

        return prompt, answer


    def _produce_answer_gateway(self, question, answer_phase):
        prompt, answer = ('', '')
        if self.model_type_gateway == 'local':
            if answer_phase == 'routing':
                sys_mess = self.prompts.get('system_message_routing', '')
                context = self.prompts.get('context_routing', '')
            elif answer_phase == 'negative_response':
                sys_mess = self.prompts.get('system_message_negative', '')
                context = ''
            elif answer_phase == 'factory_info':
                sys_mess = self.prompts.get('system_message_info', '') + self.prompts.get('shots_info', '')
                context = self.factory_model
            complete_answer = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt, answer = self._parse_llm_answer(complete_answer, self.model_type_gateway)
        else:
            if answer_phase == 'routing':
                sys_mess = self.prompts.get('system_message_routing', '')
                context = self.prompts.get('context_routing', '')
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
                answer = completion.content
            elif answer_phase == 'negative_response':
                sys_mess = self.prompts.get('system_message_negative', '')
                context = ''
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
                answer = completion.content
            elif answer_phase == 'factory_info':
                sys_mess = self.prompts.get('system_message_info', '') + self.prompts.get('shots_info', '')
                context = self.factory_model
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess}
                    )
                answer = completion.content
                return prompt, answer
        return prompt, answer


    def _produce_answer_simulation(self, question, modality):
        factory_data = retrieve_factory()
        station_names = ', '.join([station for station in factory_data['stations']])
        if self.model_id_simulation == 'local':
            sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
            context = self.prompts.get('context_simulation', '').replace('LABELS', station_names)
            complete_answer = self.chain_simulation.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt, answer = self._parse_llm_answer(complete_answer, self.model_type_simulation)

            if 'evaluation' not in modality:
                results = factory_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results_sim', '')
                context = f"The labels for the stations are: {station_names}\nResults from the simulation: {results}"
                complete_answer = self.chain_gateway.invoke({"question": question,
                                                    "context": context,
                                                    "system_message": sys_mess})
                prompt, answer = self._parse_llm_answer(complete_answer, self.model_type_gateway)
        else:
            sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
            context = self.prompts.get('context_simulation', '').replace('LABELS', station_names)
            prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
            completion = self.chain_simulation.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            answer = completion.content
            print(prompt + '\n' + answer)

            if 'evaluation' not in modality:
                results = factory_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results_sim', '')
                context = f"The labels for the stations are: {station_names}\nResults from the simulation: {results}"
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\n'
                completion = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
                answer = completion.content

        return prompt, answer


    def _produce_answer_verification(self, question, modality):
        automata_data = retrieve_automata()
        if self.model_id_verification == 'local':
            sys_mess = self.prompts.get('system_message_verification', '') + self.prompts.get('shots_verification', '')
            context = self.prompts.get('context_verification', '').replace('STATES', str(list(automata_data['transitions'].keys())))
            complete_answer = self.chain_verification.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt, answer = self._parse_llm_answer(complete_answer, self.model_type_verification)

            if 'evaluation' not in modality:
                results = uppaal_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results', '')
                context = f'Results from Uppaal: {results}'
                complete_answer = self.chain_gateway.invoke({"question": question,
                                                    "context": context,
                                                    "system_message": sys_mess})
                prompt, answer = self._parse_llm_answer(complete_answer, self.model_type_gateway)
        else:
            sys_mess = self.prompts.get('system_message_verification', '') + self.prompts.get('shots_verification', '')
            context = self.prompts.get('context_verification', '').replace('STATES', str(list(automata_data['transitions'].keys())))
            prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
            completion = self.chain_verification.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            answer = completion.content
            print(prompt + '\n' + answer)

            if 'evaluation' not in modality:
                results = uppaal_interface.interface_with_llm(answer)
                sys_mess = self.prompts.get('system_message_results', '')
                context = f'Results from Uppaal: {results}'
                prompt = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
                completion = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
                answer = completion.content
        return prompt, answer

    def _produce_answer_hybrid(self, question, modality):
        if self.model_type_gateway == 'local':
            sys_mess = self.prompts.get('system_message_hybrid', '') + self.prompts.get('shots_hybrid', '')
            context = self.pddl_domain
            complete_answer = self.chain_gateway.invoke({"question": question,
                                                "context": context,
                                                "system_message": sys_mess})
            prompt_gateway, answer_gateway = self._parse_llm_answer(complete_answer, self.model_type_gateway)
        else: 
            sys_mess = self.prompts.get('system_message_hybrid', '') + self.prompts.get('shots_hybrid', '')
            context = self.pddl_domain
            prompt_gateway = f'{sys_mess}\nHere is the context: {context}\n' + f'Here is the user question: {question}\nAnswer: '
            completion = self.chain_gateway.invoke({"question": question,
                                            "context": context,
                                            "system_message": sys_mess}
                )
            answer_gateway = completion.content
        question_json = json.loads(answer_gateway)

        questions = question_json.get("questions", answer_gateway)
        
        problem_string = question_json.get("pddl_problem", answer_gateway)
        #print(problem_string)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".pddl") as temp_file:
            temp_file.write(problem_string)
            problem_path = temp_file.name
        plan = pddl_interface.run_planner(problem_path)
        
        if len(plan) != len(questions):
            raise ValueError("Mismatch between number of plan steps and provided questions.")
        
        prompts = ""
        answers = ""
        i = 0
        for (action, question) in zip(plan, questions):
            print(f"\n\nAction: {action},\nQuestion: {question}")
            if "simulator" in action:
                prompt_simulation, answer_simulation = self._produce_answer_simulation(question, modality)
                prompts += f"\n{i+1}. Prompt simulation: \n{prompt_simulation}\n\n"
                answers += f"{i+1}. Answer simulation: \n{answer_simulation}\n\n"
            elif "validator" in action:
                prompt_verification, answer_verification = self._produce_answer_verification(question, modality)
                prompts += f"\n{i+1}. Prompt verification: \n{prompt_verification}\n\n"
                answers += f"{i+1}. Answer verification: \n{answer_verification}\n\n"
            else:
                raise RuntimeError("An error occurred during execution due to a problem in reasoner plan.")
            i += 1
        
        return prompts, answers
    

    def _generate_response(self, question, curr_datetime, info_run):
        complete_prompt, answer = self._produce_answer_gateway(question, 'routing')
        print(f'\n\nPrompt: {complete_prompt}\n')
        print(f'{answer}\n')
        print('--------------------------------------------------')

        if 'uppaal_verification' in answer.lower():
            complete_prompt, answer = self._produce_answer_verification(question, 'live')
        elif 'factory_simulation' in answer.lower():
            complete_prompt, answer = self._produce_answer_simulation(question, 'live')
        elif 'factory_info' in answer.lower():
            complete_prompt, answer = self._produce_answer_gateway(question, 'factory_info')
        elif 'hybrid' in answer.lower():
            complete_prompt, answer = self._produce_answer_hybrid(answer, 'live')
        else:
            complete_prompt, answer = self._produce_answer_gateway(question, 'negative_response')

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
            
            self._generate_response(query, current_datetime, info_run)
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
                prompt, answer = self._produce_answer_simulation(question, 'evaluation-simulation')
            elif test_filename == 'verification.csv':
                prompt, answer = self._produce_answer_verification(question, 'evaluation-verification')
            elif test_filename == 'routing.csv':
                prompt, answer = self._produce_answer_gateway(question, 'routing')
            oracle.verify_answer(prompt, question, answer)
            count += 1
            print(f'Processing answer for question {count} of {len(questions)}...')

        print('Validation process completed. Check the output file.')
        oracle.write_results_to_file()
