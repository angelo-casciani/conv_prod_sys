import datetime
import json
import os
import re
import io
from contextlib import redirect_stdout

from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate

try: # (Optional) imports for local LLMs (not needed for API-only)
    from langchain_huggingface import HuggingFacePipeline
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig, AutoConfig
    from torch import bfloat16
    LOCAL_MODEL_SUPPORT = True
except ImportError:
    LOCAL_MODEL_SUPPORT = False

import simulation_interface as factory_interface
from oracle import AnswerVerificationOracle
import uppaal_interface
from utility import log_to_file, retrieve_automata, retrieve_factory, load_csv_questions, retrieve_factory_with_failure, load_txt_questions
import pddl_interface
import tempfile
import failure_maintenance
import ast
import process_mining


def clean_json_block(text: str) -> str:
    match_md = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if match_md:
        return match_md.group(1).strip()
    
    start_brace = text.find('{')
    end_brace = text.rfind('}')
    
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_candidate = text[start_brace:end_brace+1]
        try:
            json.loads(json_candidate)
            return json_candidate
        except json.JSONDecodeError:
            pass

    match_simple = re.search(r'(\{.*?\})', text, re.DOTALL)
    if match_simple:
        return match_simple.group(0)

    return None


def explicit_deadlock_free(qjson, plan):
    questions = qjson.get("questions", [])

    mentions_deadlock = any("deadlock" in q.get("question", "").lower() for q in questions)
    
    if any("validate_deadlock" in a for a in plan) and not mentions_deadlock:
        questions.append({
            "question": "Is the system deadlock free during production?",
            "type": "validation"
        })

    qjson["questions"] = questions
    return qjson


class LLMPipeline:
    MODELS = {
        'api': {
            'openai': ['gpt-4o-mini', 'gpt-4.1-mini', 'gpt-4.1-nano', 'gpt-4.1', 'gpt-4o', 'gpt-5', 'gpt-5.1', 'gpt-5-mini', 'gpt-5-nano'],
            'google_genai': ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-3-flash-preview', 'gemini-3-pro-preview'],
            'deepseek': ['deepseek-chat', 'deepseek-reasoner'],
        },
        'local': {
            'metaai': ['meta-llama/Meta-Llama-3-8B-Instruct', 'meta-llama/Llama-3.1-8B-Instruct',
                       'meta-llama/Llama-3.2-1B-Instruct', 'meta-llama/Llama-3.2-3B-Instruct', 'meta-llama/Llama-4-Scout-17B-16E-Instruct'],
            'mistral': ['mistralai/Mistral-7B-Instruct-v0.2','mistralai/Mistral-7B-Instruct-v0.3',
                        'mistralai/Mistral-Nemo-Instruct-2407', 'mistralai/Ministral-8B-Instruct-2410'],
            'qwen': ['Qwen/Qwen2.5-7B-Instruct', 'Qwen/Qwen3-30B-A3B-Instruct-2507'],
            'google_genai': ['google/gemma-2-9b-it'],
            'microsoft': ['microsoft/phi-4', 'microsoft/Phi-4-mini-instruct'],
            'deepseek': ['deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', 'deepseek-ai/DeepSeek-R1-Distill-Llama-8B'],
        }
    }
    TERMINATOR_TOKENS = {
        'metaai': "<|eot_id|>",
        'mistral': "[/INST]",
        'qwen': "<|im_end|>",
        'microsoft': "<|im_sep|>",
        'deepseek': "｜end▁of▁sentence｜"
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
        'deepseek': '<｜Assistant｜><think>'
    }

    def __init__(self, model_id_gateway, model_id_simulation, model_id_verification, hf_token, max_new_tokens, extracted_model, extracted_model_failure):
        self.model_id_gateway = model_id_gateway
        self.model_id_simulation = model_id_simulation
        self.model_id_verification = model_id_verification
        self.model_family_gateway, self.model_type_gateway = self._get_model_family_type(self.model_id_gateway)
        self.model_family_simulation, self.model_type_simulation = self._get_model_family_type(model_id_simulation)
        self.model_family_verification, self.model_type_verification = self._get_model_family_type(model_id_verification)
        self.hf_token = hf_token
        self.max_new_tokens = max_new_tokens
        self.path_prompts = os.path.join(os.path.dirname(__file__), 'prompts.json')
        self.pddl_domain = os.path.join(os.path.dirname(__file__), 'pddl', 'domain.pddl')
        with open(self.pddl_domain, 'r') as f:
            self.pddl_domain = f.read()
        with open(self.path_prompts, 'r') as prompt_file:
            self.prompts = json.load(prompt_file)
        self.chain_simulation = self._initialize_chain(model_id_simulation, self.model_family_simulation, self.model_type_simulation)
        self.chain_verification = self._initialize_chain(model_id_verification,self.model_family_verification, self.model_type_verification)
        self.chain_gateway = self._initialize_chain(model_id_gateway,self.model_family_gateway, self.model_type_gateway)
        self.chain_failure = self._initialize_chain(model_id_gateway, self.model_family_gateway, self.model_type_gateway)
        self.chain_process_mining = self._initialize_chain(model_id_gateway, self.model_family_gateway, self.model_type_gateway)
        self.failure_module = failure_maintenance.FailureMaintenanceModule()
        self.process_mining_module = process_mining.ProcessMiningModule()
        print("Initializing digital twins...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        digital_twin_path = os.path.join(base_dir, "data", "parameters", "digital_twin.json")
        digital_twin_failure_path = os.path.join(base_dir, "data", "parameters", "digital_twin_with_failure.json")
        
        if not os.path.exists(digital_twin_path):
            print("Extracting standard digital twin...")
            self.process_mining_module.extract(failure=False)
            self.extracted = True
        else:
            print("Standard digital twin found on disk.")
            self.extracted = True
            
        if not os.path.exists(digital_twin_failure_path):
            print("Extracting digital twin with failure parameters...")
            self.process_mining_module.extract(failure=True)
            self.extracted_failure = True
        else:
            print("Digital twin with failure parameters found on disk.")
            self.extracted_failure = True
        print("Digital twins for simulation and predictive maintenance ready!")


    def _initialize_local_model(self, model_id, model_family):
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
    
        model_family_key = model_family.lower()
        if model_family_key in LLMPipeline.TERMINATOR_TOKENS:
            custom_terminator = tokenizer.convert_tokens_to_ids(LLMPipeline.TERMINATOR_TOKENS[model_family_key])
            
            # Handle models where eos_token_id is None
            if tokenizer.eos_token_id is not None:
                terminators = [tokenizer.eos_token_id, custom_terminator]
                pipeline_params["pad_token_id"] = tokenizer.eos_token_id
            else:
                # For models without eos_token_id, use custom terminator
                terminators = [custom_terminator]
                pipeline_params["pad_token_id"] = custom_terminator
                
            pipeline_params["eos_token_id"] = terminators

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

    def _parse_llm_answer(self, complete_answer, model_family):
        model_family_key = model_family.lower()
        delimiter = LLMPipeline.RESPONSE_DELIMITERS.get(model_family_key, 'Answer:')

        index = complete_answer.find(delimiter)
        if index != -1:
            prompt = complete_answer[:index + len(delimiter)]
            answer = complete_answer[index + len(delimiter):]
        else:
            prompt = complete_answer
            answer = ""

        return prompt, answer
    

    def _initialize_chain(self, model_id, model_family, model_type):
        prompt_template_structure = self._generate_prompt_template(model_family)
        if model_type == 'local':
            if not LOCAL_MODEL_SUPPORT:
                raise RuntimeError(
                    "Local model support not available. Install langchain_huggingface, "
                    "transformers, and torch to use local models."
                )
            generate_text = self._initialize_local_model(model_id, model_family) 
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


    def _produce_answer_gateway(self, question, answer_phase, modality=''):
        prompt, answer = ('', '')
        if answer_phase == 'routing':
            sys_mess = self.prompts.get('system_message_routing', '')
            context = self.prompts.get('context_routing', '')            
        elif answer_phase == 'negative_response':
            sys_mess = self.prompts.get('system_message_negative', '')
            context = ''
        elif answer_phase == 'factory_info':
            sys_mess = self.prompts.get('system_message_info', '')
            if 'zeroshot' not in modality:
                sys_mess += self.prompts.get('shots_info', '')
            factory_model = os.path.join(os.path.dirname(__file__), '..', 'data', 'parameters', 'digital_twin.json')
            with open(factory_model, 'r') as factory_file:
                factory_model = json.load(factory_file)
            context = factory_model
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_gateway.invoke(invoke_payload)
        if self.model_type_gateway == 'local':
            prompt, answer = self._parse_llm_answer(complete_answer, self.model_family_gateway)
        else:
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
    
    def _execute_follow_up_simulation(self, question, activity_names):
        sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
        context = self.prompts.get('context_simulation', '').replace('LABELS', activity_names)
        
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        
        complete_answer = self.chain_simulation.invoke(invoke_payload)
        answer = complete_answer.content
        
        follow_up_results = factory_interface.interface_with_llm(answer)
        
        return follow_up_results
        
    def _produce_answer_simulation(self, question, modality):
        factory_data = retrieve_factory()
        activity_names = ', '.join([activity for activity in factory_data['activities']])
        sys_mess = self.prompts.get('system_message_simulation', '') + self.prompts.get('shots_simulation', '')
        context = self.prompts.get('context_simulation', '').replace('LABELS', activity_names)
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_simulation.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_simulation.invoke(invoke_payload)
        if self.model_type_simulation == 'local':
            answer = complete_answer
        else:
            answer = complete_answer.content

        if 'evaluation' not in modality:
            results = factory_interface.interface_with_llm(answer)
            #print(answer)
            if "event_prediction" not in answer:
                if results['target_pieces'] != '' and results['simulation_time']:
                    is_negative_result = self._check_negative_result(results)
                    print(results)
                    print(is_negative_result)
                    if is_negative_result:
                        new_question = self._generate_new_sim_question(results)
                        new_results = self._execute_follow_up_simulation(new_question, activity_names)

                        combined_results = self._format_results_for_llm(results, new_results)
                    else:
                        combined_results = self._format_results_for_llm(results)
                else:
                    self.sim_time = results['results']['total_execution_time'] 
                    combined_results = results
            else:
                combined_results = results
            print(combined_results)

            sys_mess = self.prompts.get('system_message_results_sim', '') + """
                    If the context contains both 'Original analysis' and 'Follow-up analysis', 
                    make sure to provide information from both analyses in your response.
                    """
            context = f"The labels for the activities are: {activity_names}\nResults from the simulation: {combined_results}.\nNote: If there are both original and follow-up analyses, provide a complete answer using both."
            invoke_payload = {"question": question,
                            "context": context,
                            "system_message": sys_mess}
            prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
            complete_answer = self.chain_gateway.invoke(invoke_payload)
            if self.model_type_gateway == 'local':
                prompt, answer = self._parse_llm_answer(complete_answer, self.model_family_gateway)
            else:
                answer = complete_answer.content
        return prompt, answer


    def _produce_answer_verification(self, question, modality):
        automata_data = retrieve_automata()
        sys_mess = self.prompts.get('system_message_verification', '')
        if 'zeroshot' not in modality:
            sys_mess += self.prompts.get('shots_verification', '')
        context = self.prompts.get('context_verification', '').replace('STATES', str(list(automata_data['transitions'].keys())))
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_verification.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_verification.invoke(invoke_payload)
        if self.model_type_verification == 'local':
            answer = complete_answer
        else:
            answer = complete_answer.content

        if 'evaluation' not in modality:
            results = uppaal_interface.interface_with_llm(answer)
            sys_mess = self.prompts.get('system_message_results_ver', '')
            context = f'Results from Uppaal: {results}'
            invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
            prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
            complete_answer = self.chain_gateway.invoke(invoke_payload)
            if self.model_type_gateway == 'local':
                prompt, answer = self._parse_llm_answer(complete_answer, self.model_family_gateway)
            else:
                answer = complete_answer.content
        return prompt, answer
    
    def _produce_answer_failure(self, question, sim_time, modality=''):
        factory_model_with_failure = retrieve_factory_with_failure()
        sys_mess = self.prompts.get('system_message_failure', '')
        if 'zeroshot' not in modality:
            sys_mess += self.prompts.get('shots_failure', '')
        context = factory_model_with_failure
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_failure.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_failure.invoke(invoke_payload)
        if self.model_type_gateway == 'local':
            answer = complete_answer
        else:
            answer = complete_answer.content

        cleaned_answer = clean_json_block(answer)
        
        if cleaned_answer is None:
            print(f"ERROR: Impossible to extract a clean JSON from the failure model answer. Answer: {answer}")
            return prompt, "{}"

        try:
            parsed_json = json.loads(cleaned_answer)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed JSON decoding even after cleaning. JSON: {cleaned_answer}. Error: {e}")
            return prompt, "{}" # Ritorna un JSON vuoto
            
        action = parsed_json.get("task")
        if action is None:
            print("Failure JSON missing 'task' field, returning empty result.")
            return prompt, "{}"
        if action == "predict_failure":
            activity = parsed_json.get("activity_id")
            horizon = parsed_json.get("time_horizon") if parsed_json.get("time_horizon") is not None else sim_time
            result = self.failure_module.predict_activity_failures(factory_model_with_failure, activity, horizon)
        else:
            raise ValueError(f"Unsupported failure action: {action}")

        clean_result = json.dumps(result, indent=2, default=str)
        return prompt, clean_result
    
    def _produce_answer_process_mining(self, question, modality):
        sys_mess = self.prompts.get('system_message_process_mining', '')
        if 'zeroshot' not in modality:
            sys_mess += self.prompts.get('shots_process_mining', '')
        context = ''
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt = self.chain_process_mining.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_process_mining.invoke(invoke_payload)
        if self.model_type_gateway == 'local':
            prompt, answer = self._parse_llm_answer(complete_answer, self.model_family_gateway)
            #print("Risposta LLM:" + answer)
        else:
            answer = complete_answer.content
            
        answer = clean_json_block(answer)
        if answer is None:
            print(f"ERROR: clean_json_block returned None for process_mining answer")
            print(f"Original answer: {complete_answer.content if hasattr(complete_answer, 'content') else complete_answer}")
            if 'evaluation' in modality:
                return prompt, '{"task": "invalid_no_json_found"}'
            else:
                raise ValueError("No valid JSON found in the answer")
        #print(answer)
        try:
            parsed_json = json.loads(answer)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed JSON decoding in process mining. JSON: {answer}. Error: {e}")
            return prompt, '{"task": "invalid_json_parse_error"}' 
        
        action = parsed_json.get("task")
        nl_output = answer
        if 'evaluation' not in modality:
            
            if action is None:
                print("Process mining JSON missing 'task' field, returning empty result.")
                return prompt, "{}"
            elif action == 'process_discovery':
                net, initial_marking, final_marking, net_path = self.process_mining_module.discovery()
                self.process_mining_module.view_petri_net(net, initial_marking, final_marking)
                nl_output = f"I discovered the process model. The Petri net has been saved at: {net_path}."
            elif action == 'conformance_checking':
                log = self.process_mining_module.load_log()
                net, initial_marking, final_marking, net_path = self.process_mining_module.discovery()
                trace_is_fit, trace_fitness = self.process_mining_module.conformal_checking(net, initial_marking, final_marking, log)
                fit_text = "fits" if trace_is_fit else "does not fit"
                nl_output = f"The event log {fit_text} the discovered model, with a fitness score of {trace_fitness:.2f}."
            elif action == 'performance_analysis':
                metric = parsed_json.get("metric")
                log = self.process_mining_module.load_log()    
                result = self.process_mining_module.performance_analysis(log, metric, parsed_json)

                if isinstance(result, dict) and 'interpretation' in result:
                    nl_output = result['interpretation']
                else:
                    nl_output = f"I computed the {metric} metric. Result: {result}"
            elif action == "filter_by_time_range":
                log = self.process_mining_module.load_log()
                start_date, end_date = parsed_json.get("start_date"), parsed_json.get("end_date") 
                filtered_path = self.process_mining_module.filter_by_time_range(log, start_date, end_date)
                nl_output = f"The filtered event log has been saved at: {filtered_path}."
            else:
                raise ValueError(f"Unsupported process mining action: {action}")
        
        return prompt, nl_output
    
    def _produce_rewritten_answer(self, answers):
        sys_mess = self.prompts.get('system_message_rewrite_answer', '')
        question = "Rewrite the following answers in a clean way, without any extra information."
        invoke_payload = {"question": question,
                    "context": answers,
                    "system_message": sys_mess}
        prompt = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_gateway.invoke(invoke_payload)
        if self.model_type_gateway == 'local':
            prompt, answer = self._parse_llm_answer(complete_answer, self.model_family_gateway)
        else:
            answer = complete_answer.content

        return prompt, answer


    def _produce_answer_hybrid(self, question, modality):
        factory_model = retrieve_factory()
        activities = [a for a in factory_model['activities'].keys()]
        activities_str = ", ".join(activities)
        activities_context = f"\n\nAvailable activities in the system: {activities_str}\nNote: When generating PDDL problems, use these exact activity names as activity objects (e.g., station41, corner2, splitter3), not generic names like A1, A2, etc.\n"
        sys_mess = self.prompts.get('system_message_hybrid', '')
        if 'zeroshot' not in modality:
            sys_mess += self.prompts.get('shots_hybrid', '')
        context = self.pddl_domain + activities_context
        invoke_payload = {"question": question,
                        "context": context,
                        "system_message": sys_mess}
        prompt_gateway = self.chain_gateway.first.format_prompt(**invoke_payload).to_string()
        complete_answer = self.chain_gateway.invoke(invoke_payload)
        if self.model_type_gateway == 'local':
            answer_gateway = complete_answer
        else:
            answer_gateway = complete_answer.content
        
        if "evaluation" in modality:
            return prompt_gateway, answer_gateway
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
        if 'evaluation' not in modality:
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
                elif "extract_digital_twin" in action_lower:
                    continue
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
                    prompt, answer = self._produce_answer_failure(q_text, last_sim_time, modality)
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
    
    def _generate_response(self, question, curr_datetime, info_run, chatbot=False):
        complete_prompt, answer = self._produce_answer_gateway(question, 'routing')
        print(f'\n\nPrompt: {complete_prompt}\n')
        print(f'{answer}\n')
        print('--------------------------------------------------')

        self.request_type = answer

        if 'uppaal_verification' in answer.lower():
            complete_prompt, answer = self._produce_answer_verification(question, 'live')
        elif 'factory_simulation' in answer.lower():
            complete_prompt, answer = self._produce_answer_simulation(question, 'live')
        elif 'factory_info' in answer.lower():
            complete_prompt, answer = self._produce_answer_gateway(question, 'factory_info', info_run.get('Interaction Modality', ''))
            answer = clean_json_block(answer)
            parsed_json = json.loads(answer)
            answer = parsed_json["response"]
        elif 'process_mining' in answer.lower():
            complete_prompt, answer = self._produce_answer_process_mining(question, 'live')
        elif 'hybrid' in answer.lower():
            complete_prompt, answer = self._produce_answer_hybrid(question, 'live')
        else:
            complete_prompt, answer = self._produce_answer_gateway(question, 'negative_response')

        print(f'Prompt: {complete_prompt}\n')
        print(f'{answer}\n')
        print('--------------------------------------------------')

        if chatbot:
            yield answer
        log_to_file(f'Query: {complete_prompt}\n\n{answer}\n\n##########################\n\n',
                    curr_datetime, info_run)


    def live_prompting(self, info_run, chatbot, query=""):
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if chatbot:
            if query.lower().strip() == "quit":
                yield "Goodbye!"
                return

            yield f"Processing your query: {query}"
            
            for response in self._generate_response(query, current_datetime, info_run, chatbot=True):
                yield response
        else:
            while True:
                query = input('Insert the query you want to ask (type "quit" to exit): ')

                if query.lower() == 'quit':
                    print("Exiting the chat.")
                    break
                
                for response in self._generate_response(query, current_datetime, info_run, chatbot=False):
                    print(response)
                    print()


    def evaluate_performance(self, test_filename, info_run):
        questions = load_csv_questions(test_filename)
        oracle = AnswerVerificationOracle(info_run)

        if test_filename == 'routing.csv':
            oracle.set_test_type('routing')
        elif test_filename == 'simulation.csv':
            oracle.set_test_type('simulation')
        elif test_filename == 'verification.csv':
            oracle.set_test_type('verification')
        elif test_filename == 'factory_info.csv':
            oracle.set_test_type('factory_info')
        elif test_filename == 'process_mining.csv':
            oracle.set_test_type('process_mining')
        elif test_filename == 'hybrid.csv':
            oracle.set_test_type('hybrid')

        count = 0
        prompt, answer = '', ''
        for el in questions:
            question = el[0]
            expected_answer = el[1]
            oracle.add_question_expected_answer_pair(question, expected_answer)

            if test_filename == 'simulation.csv':
                self.request_type = "factory_simulation"
                prompt, answer = self._produce_answer_simulation(question, 'evaluation-simulation')
            elif test_filename == 'verification.csv':
                prompt, answer = self._produce_answer_verification(question, 'evaluation-verification')
            elif test_filename == 'routing.csv':
                prompt, answer = self._produce_answer_gateway(question, 'routing')
            elif test_filename == 'factory_info.csv':
                prompt, answer = self._produce_answer_gateway(question, 'factory_info')
            elif test_filename == 'process_mining.csv':
                prompt, answer = self._produce_answer_process_mining(question, 'evaluation-process_mining')
            elif test_filename == 'hybrid.csv':
                prompt, answer = self._produce_answer_hybrid(question, 'evaluation-hybrid')
            oracle.verify_answer(prompt, question, answer)
            count += 1
            print(f'Processing answer for question {count} of {len(questions)}...')

        print('Evaluation process completed. Check the output file.')
        oracle.write_results_to_file()


    def evaluate_qualitative_hybrid(self, test_filename, info_run):
        print(f"Starting hybrid qualitative evaluation from: {test_filename}")
        
        log_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "evaluation")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"qualitative_results_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        log_path = os.path.join(log_dir, log_filename)
        
        questions = load_txt_questions(test_filename)
        
        total_questions = len(questions)
        print(f"{total_questions} question found. Logging into: {log_path}")
        
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write('QUALITATIVE EVALUATION INFO\n\n')
            for key, value in info_run.items():
                log_file.write(f"{key}: {value}\n")
            log_file.write(f"Test file: {test_filename}\n")
            log_file.write('\n' + '=' * 80 + '\n\n')
            
            for i, question in enumerate(questions):
                print(f"Elaborating question {i+1} of {total_questions}...")
                log_file.write(f"QUESTION {i+1}/{total_questions}: {question}\n\n")
                
                buffer = io.StringIO()
                
                final_answer = ""
                intermediate_logs = ""
                
                with redirect_stdout(buffer):
                    try:
                        self.request_type = "hybrid"
                        prompt, final_answer = self._produce_answer_hybrid(question, 'live')

                        
                    except Exception as e:
                        print(f"ERROR DURING THE ELABORATION OF THE QUESTION: {e}")
                        final_answer = f"Execution failer with error: {e}"
                
                intermediate_logs = buffer.getvalue()
                
                log_file.write("--- INTERMEDIATE LOGS (STDOUT) ---\n")
                log_file.write(intermediate_logs)
                log_file.write("\n--- MODEL FINAL ANSWER ---\n")
                log_file.write(final_answer)
                log_file.write("\n\n" + '#' * 80 + "\n\n")

        print(f"QUALITATIVE EVALUATION COMPLETED. Results are in: {log_path}")
