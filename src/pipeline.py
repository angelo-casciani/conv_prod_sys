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
import failure_maintenance
import ast
import re

def clean_json_block(text: str) -> str:
    if text.startswith("```"):
        lines = text.strip().splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            return "\n".join(lines[1:-1]).strip()
    return text.strip()

def explicit_deadlock_free(qjson, plan):
    questions = qjson.get("questions", [])

    has_validation = any(q["type"] == "validation" for q in questions)
    
    if any("validate_deadlock" in a for a in plan) and not has_validation:
        questions.append({
            "question": "Is the system deadlock free during production?",
            "type": "validation"
        })

    qjson["questions"] = questions
    return qjson
class LLMPipeline:
    MODELS = {
        'api': {
            'openai': ['gpt-4o-mini', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4.1', 'gpt-4o'],
            'google_genai': ['gemini-2.0-flash', 'gemini-2.5-flash-preview-05-20'],
            'deepseek': ['deepseek-chat', 'deepseek-reasoner'],
            'anthropic': [],
        },
        'local': {
            'metaai': ['meta-llama/Meta-Llama-3-8B-Instruct', 'meta-llama/Meta-Llama-3.1-8B-Instruct',
                       'meta-llama/Llama-3.2-1B-Instruct', 'meta-llama/Llama-3.2-3B-Instruct'],
            'mistral': ['mistralai/Mistral-7B-Instruct-v0.2','mistralai/Mistral-7B-Instruct-v0.3', 
                        'mistralai/Mistral-Nemo-Instruct-2407', 'mistralai/Ministral-8B-Instruct-2410'],
            'qwen': ['Qwen/Qwen2.5-7B-Instruct'],
            'google_genai': ['google/gemma-2-9b-it'],
            'microsoft': ['microsoft/phi-4'],
            'deepseek': ['deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', 'deepseek-ai/DeepSeek-R1-Distill-Llama-8B']
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

    def __init__(self, model_id_gateway, model_id_simulation, model_id_verification, hf_token, max_new_tokens):
        self.model_id_gateway = model_id_gateway
        self.model_id_simulation = model_id_simulation
        self.model_id_verification = model_id_verification
        self.model_family_gateway, self.model_type_gateway = self._get_model_family_type(self.model_id_gateway)
        self.model_family_simulation, self.model_type_simulation = self._get_model_family_type(model_id_simulation)
        self.model_family_verification, self.model_type_verification = self._get_model_family_type(model_id_verification)
        self.hf_token = hf_token
        self.max_new_tokens = max_new_tokens
        self.path_prompts = os.path.join(os.path.dirname(__file__), 'prompts.json')
        self.factory_model = os.path.join(os.path.dirname(__file__), '..','models', 'lego_factory.json')
        self.factory_model_with_failure = os.path.join(os.path.dirname(__file__), '..','models', 'lego_factory_with_failure.json')
        self.pddl_domain = os.path.join(os.path.dirname(__file__), 'pddl', 'domain.pddl')
        with open(self.path_prompts, 'r') as prompt_file:
            self.prompts = json.load(prompt_file)
        with open(self.factory_model, 'r') as factory_file:
            self.factory_model = json.load(factory_file)
        with open(self.factory_model_with_failure, 'r') as factory_file:
            self.factory_model_with_failure = json.load(factory_file)
        self.chain_simulation = self._initialize_chain(model_id_simulation, self.model_family_simulation, self.model_type_simulation)
        self.chain_verification = self._initialize_chain(model_id_verification,self.model_family_verification, self.model_type_verification)
        self.chain_gateway = self._initialize_chain(model_id_gateway,self.model_family_gateway, self.model_type_gateway)
        self.chain_failure = self._initialize_chain(model_id_gateway, self.model_family_gateway, self.model_type_gateway)
        self.chain_rewrite_answer = self._initialize_chain(model_id_gateway, self.model_family_gateway, self.model_type_gateway)
        self.failure_module = failure_maintenance.FailureMaintenanceModule(factory_model_path="lego_factory_with_failure.json")


    def _initialize_local_model(self):
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

        pipeline_params = {
            "model": model,
            "tokenizer": tokenizer,
            "return_full_text": True,
            "task": "text-generation",
            "do_sample": True, 
            "temperature": 0.1,
            "max_new_tokens": self.max_new_tokens,
            "repetition_penalty": 1.1
        }
    
        model_family_key = self.model_family.lower() if self.model_family else None
        if model_family_key and model_family_key in LLMPipeline.TERMINATOR_TOKENS:
            special_token_str = LLMPipeline.TERMINATOR_TOKENS[model_family_key] 
            terminators_ids = [tokenizer.eos_token_id]
            if isinstance(special_token_str, str):
                if special_token_str in tokenizer.get_vocab():
                    terminators_ids.append(tokenizer.convert_tokens_to_ids(special_token_str))
            elif isinstance(special_token_str, list):
                 for tok_str in special_token_str:
                      if tok_str in tokenizer.get_vocab():
                           terminators_ids.append(tokenizer.convert_tokens_to_ids(tok_str))
            pipeline_params.update({
                "eos_token_id": terminators_ids, # A list of token IDs
                "pad_token_id": tokenizer.eos_token_id 
            })

        generate_text = pipeline(**pipeline_params)
        return generate_text


    def _get_model_family_type(self, model_id):
        model_id_lower = model_id.lower()
        for model_type, families in LLMPipeline.MODELS.items():
            for family, models_in_family in families.items():
                if any(m.lower() == model_id_lower for m in models_in_family): 
                    return family, model_type
        return None, None


    def _generate_prompt_template(self, model_family):
        template_key = LLMPipeline.TEMPLATE_MAPPING.get(model_family, 'template-generic')
        template = self.prompts.get(template_key, '')

        return PromptTemplate.from_template(template)
    

    def _initialize_chain(self, model_id, model_family, model_type):
        prompt_template_structure = self._generate_prompt_template(model_family)
        if model_type == 'local':
            generate_text = self._initialize_local_model() 
            model = HuggingFacePipeline(pipeline=generate_text)
        elif model_type == 'api':
            model_family_for_provider = model_family
            model = init_chat_model(
                model_id, 
                model_provider=model_family_for_provider, 
                temperature=0.1,
                max_tokens=self.max_new_tokens
            )
        else:
            raise ValueError(f"Unsupported model_type: {model_type}. Must be 'local' or 'api'.") 
        
        chain = prompt_template_structure | model
        return chain


    def _produce_answer_gateway(self, question, answer_phase):
        prompt, answer = ('', '')
        if answer_phase == 'routing':
            sys_mess = self.prompts.get('system_message_routing', '')
            context = self.prompts.get('context_routing', '')            
        elif answer_phase == 'negative_response':
            sys_mess = self.prompts.get('system_message_negative', '')
            context = ''
        elif answer_phase == 'factory_info':
            sys_mess = self.prompts.get('system_message_info', '') + self.prompts.get('shots_info', '')
            context = self.factory_model
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_gateway.invoke(invoke_payload)
        answer = complete_answer.content
        return prompt, answer

    def _format_results_for_llm(self, results, follow_up_results=None):
        original_pieces = results['results']['total_pieces_produced']
        target_pieces = results['target_pieces']
        original_time = results['simulation_time'] 
        
        if follow_up_results:
            needed_time = follow_up_results['results']['total_execution_time']
            
            formatted = f"""
                            SIMULATION RESULTS:

                            ORIGINAL QUESTION ANALYSIS:
                            - Target: {target_pieces} pieces in {original_time} time units
                            - Actual result: Only {original_pieces} pieces were produced
                            - Feasible: NO

                            ADDITIONAL INFORMATION:
                            - To produce {target_pieces} pieces, {needed_time} time units are needed
                            - This is {needed_time - original_time} more time units than available

                            ANSWER: No, {target_pieces} pieces cannot be produced in {original_time} time units. Only {original_pieces} pieces can be produced in that timeframe. To produce the full {target_pieces} pieces, you would need {needed_time} time units.
                            """
            self.sim_time = needed_time
        else:
            formatted = f"""
                            SIMULATION RESULTS:
                            - Pieces produced: {original_pieces}
                            - Time used: {original_time} time units
                            """
            self.sim_time = original_time
        
         
        return formatted
    
    def _check_negative_result(self, results):
        simulation_time = int(results.get('simulation_time', 0) or 0)
        total_execution_time = int(results['results'].get('total_execution_time', 0) or 0)

        target_pieces = int(results.get('target_pieces', 0) or 0)
        total_pieces_produced = int(results['results'].get('total_pieces_produced', 0) or 0)

        if total_pieces_produced >= target_pieces and total_execution_time <= simulation_time:
            return False

        return total_execution_time > simulation_time or total_pieces_produced < target_pieces
    
    def _generate_new_sim_question(self, results):
        target_pieces = results['target_pieces']
        simulation_time = results['simulation_time']
        task = results['task']

        if task == 'sim_with_time':
            new_question = f"How much time is needed to produce {target_pieces} pieces?"
        elif task == 'sim_with_number_products':
            new_question = f"How many pieces can be produced in {simulation_time} units of time?"
        else:
            raise ValueError(f"Unsupported task: {task}. Must be 'sim_with_time' or 'sim_with_number_products'")
        
        return new_question
    
    def _execute_follow_up_simulation(self, question, station_names):
        sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
        context = self.prompts.get('context_simulation', '').replace('LABELS', station_names)
        
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        
        complete_answer = self.chain_simulation.invoke(invoke_payload)
        answer = complete_answer.content
        
        follow_up_results = factory_interface.interface_with_llm(answer)
        
        return follow_up_results
        
    def _produce_answer_simulation(self, question, modality):
        factory_data = retrieve_factory()
        station_names = ', '.join([station for station in factory_data['stations']])
        sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
        context = self.prompts.get('context_simulation', '').replace('LABELS', station_names)
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_simulation.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_simulation.invoke(invoke_payload)
        answer = complete_answer.content

        if 'evaluation' not in modality:
            results = factory_interface.interface_with_llm(answer)
            is_negative_result = self._check_negative_result(results)
            print(results)
            print(is_negative_result)
            if is_negative_result:
                new_question = self._generate_new_sim_question(results)
                new_results = self._execute_follow_up_simulation(new_question, station_names)

                combined_results = self._format_results_for_llm(results, new_results)
            else:
                combined_results = self._format_results_for_llm(results)

            print(combined_results)

            sys_mess = self.prompts.get('system_message_results_sim', '') + """
                    If the context contains both 'Original analysis' and 'Follow-up analysis', 
                    make sure to provide information from both analyses in your response.
                    """
            context = f"The labels for the stations are: {station_names}\nResults from the simulation: {combined_results}.\nNote: If there are both original and follow-up analyses, provide a complete answer using both."
            invoke_payload = {"question": question,
                            "context": context,
                            "system_message": sys_mess}
            prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
            complete_answer = self.chain_gateway.invoke(invoke_payload)
            answer = complete_answer.content
        return prompt, answer


    def _produce_answer_verification(self, question, modality):
        automata_data = retrieve_automata()
        sys_mess = self.prompts.get('system_message_verification', '') + self.prompts.get('shots_verification', '')
        context = self.prompts.get('context_verification', '').replace('STATES', str(list(automata_data['transitions'].keys())))
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_verification.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_verification.invoke(invoke_payload)
        answer = complete_answer.content

        if 'evaluation' not in modality:
            results = uppaal_interface.interface_with_llm(answer)
            sys_mess = self.prompts.get('system_message_results', '')
            context = f'Results from Uppaal: {results}'
            invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
            prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
            complete_answer = self.chain_gateway.invoke(invoke_payload)
            answer = complete_answer.content
        return prompt, answer
    
    def _produce_answer_failure(self, question, sim_time):
        sys_mess = self.prompts.get('system_message_failure', '') + self.prompts.get('shots_failure', '')
        context = self.factory_model_with_failure
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_failure.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_failure.invoke(invoke_payload)
        answer = complete_answer.content

        answer = clean_json_block(answer)
        parsed_json = json.loads(answer)
        action = parsed_json.get("task")
        if action is None:
            print("Failure JSON missing 'task' field, returning empty result.")
            return prompt, "{}"
        if action == "predict_failure":
            station = parsed_json.get("station_id")
            horizon = parsed_json.get("time_horizon") if parsed_json.get("time_horizon") is not None else sim_time
            result = self.failure_module.predict_station_failures(station, horizon)
        else:
            raise ValueError(f"Unsupported failure action: {action}")

        clean_result = json.dumps(result, indent=2, default=str)
        return prompt, clean_result
    
    def _produce_rewritten_answer(self, answers):
        sys_mess = self.prompts.get('system_message_rewrite_answer', '')
        question = "Rewrite the following answers in a clean way, without any extra information."
        invoke_payload = {"question": question,
                    "context": answers,
                    "system_message": sys_mess}
        prompt = self.chain_rewrite_answer.first.format_prompt(**invoke_payload).to_string()
        answer = self.chain_rewrite_answer.invoke(invoke_payload).content

        return prompt, answer


    def _produce_answer_hybrid(self, question, modality):
        sys_mess = self.prompts.get('system_message_hybrid', '') + self.prompts.get('shots_hybrid', '')
        context = self.pddl_domain
        invoke_payload = {"question": question,
                    "context": context,
                    "system_message": sys_mess}
        prompt_gateway = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
        answer_gateway = self.chain_gateway.invoke(invoke_payload).content
        
        answer_gateway = clean_json_block(answer_gateway)

        #question_json = json.loads(answer_gateway)
        try:
            question_json = json.loads(answer_gateway)
        except json.JSONDecodeError:
            print("Failed to parse hybrid answer as JSON, trying ast.literal_eval...")
            try:
                question_json = ast.literal_eval(answer_gateway)
            except Exception as e:
                print(f"Hybrid response could not be parsed as JSON or Python dict. Got:\n{answer_gateway}")
                raise ValueError(f"Hybrid response could not be parsed.") from e


        problem_string = question_json.get("pddl_problem", answer_gateway)
        print(problem_string)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".pddl") as temp_file:
            temp_file.write(problem_string)
            problem_path = temp_file.name
        plan = pddl_interface.run_planner(problem_path)
        print(plan)
        
        question_json = explicit_deadlock_free(question_json, plan)
        questions = question_json.get("questions", answer_gateway)
        
        typed_questions = {
            "failure": [q["question"] for q in questions if q["type"] == "failure"],
            "simulation": [q["question"] for q in questions if q["type"] == "simulation"],
            "validation": [q["question"] for q in questions if q["type"] == "validation"]
        }
        
        prompts = ""
        answers = ""
        failure_delay = 0
        type_counters = {"failure": 0, "simulation": 0, "validation": 0}
        last_sim_time = None 
        for i, action in enumerate(plan):
            action_lower = action.lower()
            if "simulate" in action_lower:
                qtype = "simulation"
            elif "validate" in action_lower:
                qtype = "validation"
            elif "maintenance" in action_lower:
                qtype = "failure"
            else:
                print(f"Unknown plan action '{action}', skipping.")
                continue

            idx = type_counters[qtype]
            if idx >= len(typed_questions[qtype]):
                print(f"No remaining questions of type {qtype} for plan step {action}, skipping this step.")
                continue

            q_text = typed_questions[qtype][idx]
            type_counters[qtype] += 1

            if qtype == "simulation":
                prompt, answer = self._produce_answer_simulation(q_text, modality)

            elif qtype == "failure":
                last_sim_time = self.sim_time
                prompt, answer = self._produce_answer_failure(q_text, last_sim_time)
                try:
                    delay = json.loads(answer).get("estimated_maintenance_delay", 0)
                    if isinstance(delay, (int, float)):
                        failure_delay += delay
                        answer = f"Estimated maintenance delay: {delay} units of time"
                    else:
                        print(f"Warning: Delay value is not numeric: {delay}. Ignoring.")
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Warning: Failed to parse failure delay from answer. Using 0. Reason: {e}")

            elif qtype == "validation":
                prompt, answer = self._produce_answer_verification(q_text, modality)
                if "deadlock" in q_text.lower():
                    is_deadlock_free = any(phrase in answer.lower() for phrase in [
                        "deadlock free", "no deadlock", "deadlock-free", "free from deadlock"
                    ]) and not any(phrase in answer.lower() for phrase in [
                        "not deadlock free", "deadlock detected", "has deadlock"
                    ])
                    
                    if not is_deadlock_free:
                        print(f"Deadlock detected in validation step {i+1}. Stopping further simulations.")
                        answers += f"\nCRITICAL: Deadlock detected. Further simulations may be unreliable.\n"
                        break

            prompts += f"\n{i+1}. Prompt {qtype}: \n{prompt}\n"
            answers += f"{i+1}. Answer {qtype}: \n{answer}\n\n"
        if last_sim_time and failure_delay:
            total_time = last_sim_time + failure_delay
            answers += f"Adding {failure_delay} units of maintenance delay, the total estimated time is {total_time} units.\n"
            
        #print(answers)
        prompt, answer = self._produce_rewritten_answer(answers) 
        return prompts, answer
    
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
            complete_prompt, answer = self._produce_answer_hybrid(question, 'live')
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
