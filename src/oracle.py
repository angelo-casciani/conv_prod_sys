import datetime
import os
import time
from sklearn.metrics import (precision_score, recall_score, f1_score, accuracy_score)
from utility import load_csv_questions
import json
import re


class AnswerVerificationOracle:
    def __init__(self, info_run):
        self.question_with_expected_answer_pairs = {}
        self.true_answers = []
        self.predicted_answers = []
        self.results = []
        self.run_info = info_run
        self.start_time = time.time()
        self.end_time = 0
        self.elapsed_time = 0
        self.accuracy = 0
        self.precision = 0
        self.recall = 0
        self.f1score = 0
        self.mcc = 0.0
        self.auc = 0.0
        self.test_type = None

    
    def set_test_type(self, test_type):
        self.test_type = test_type

    def add_question_expected_answer_pair(self, question, expected_answer):
        self.question_with_expected_answer_pairs[question] = expected_answer

    def verify_answer(self, prompt, question, model_answer):
        result = {
            'prompt': prompt,
            'question': question,
            'model_answer': model_answer,
            'expected_answer': None,
            'verification_result': None
        }
        expected_answer = self.question_with_expected_answer_pairs.get(question)
        if expected_answer is not None:
            result['expected_answer'] = expected_answer
            
            if self.test_type == 'routing':
                print("Using routing verification")
                result['verification_result'] = self._verify_routing(model_answer, expected_answer)
            elif self._is_json_structure(expected_answer):
                print("Using JSON structure verification")
                result['verification_result'] = self._verify_json_answer(expected_answer, model_answer)
            else:
                # Fallback to old logic
                expected_answer_formatted = expected_answer.lower().replace(' ', '')
                model_answer_formatted = model_answer.lower().replace('\n', ' ').replace(' ', '')
                if expected_answer == "no_answer":
                    result['verification_result'] = self._verify_no_answer(model_answer)
                else:
                    result['verification_result'] = expected_answer_formatted in model_answer_formatted
            
            self.true_answers.append(expected_answer)
            self.predicted_answers.append(model_answer)
            
            print(f"Answer: {model_answer}\nExpected_answer: {result['expected_answer']}\nResult: {result['verification_result']}")
            #print(result['verification_result'])
        self.results.append(result)

        return result['verification_result']


    def _verify_no_answer(self, model_answer):
        model_answer_formatted = model_answer.lower()

        has_uppaal = "uppaal_verification" in model_answer_formatted
        has_factory = "factory_simulation" in model_answer_formatted
        has_info = "factory_info" in model_answer_formatted
        has_pm = "process_mining" in model_answer_formatted
        has_hybrid = "hybrid" in model_answer_formatted
        
        return (not has_uppaal and not has_factory and not has_info and not has_pm and not has_hybrid) or (has_uppaal and has_factory and has_info and has_pm and has_hybrid)

    def _verify_routing(self, model_answer, expected_route):
        model_answer_lower = model_answer.lower()
        expected_route_lower = expected_route.lower()

        valid_routes = ["factory_simulation", "uppaal_verification", "factory_info", 
                       "process_mining", "hybrid", "conversational_gateway"]

        if expected_route == "unrelated":
            return self._verify_no_answer(model_answer)
        
        if expected_route_lower not in valid_routes:
            print(f"Warning: Expected route '{expected_route}' not in valid routes")
            return False
        
        routes_found = [route for route in valid_routes if route in model_answer_lower]
        if expected_route_lower in model_answer_lower:
            if len(routes_found) == 1:
                return True
            else:
                return expected_route_lower in model_answer_lower and \
                       all(route == expected_route_lower or route not in model_answer_lower 
                           for route in valid_routes)
        
        return False
    
    def _is_json_structure(self, text):
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))
    
    def _verify_json_answer(self, expected_answer, model_answer):
        try:
            expected_dict = self._reconstruct_json_from_csv(expected_answer)
            
            if expected_dict is None:
                print("Failed to reconstruct expected JSON from CSV")
                expected_dict = json.loads(expected_answer) if isinstance(expected_answer, str) else expected_answer
            
            model_dict = self._extract_json_from_answer(model_answer)
            print(f"Expected JSON: {expected_dict}")
            print(f"Model JSON: {model_dict}")
            if model_dict is None:
                return False
            
            expected_task = expected_dict.get('task', '')
            model_task = model_dict.get('task', '')
            
            if expected_task != model_task:
                return False
            
            if expected_task == 'factory_info':
                return self._verify_factory_info(expected_dict, model_dict)
            elif expected_task == 'process_discovery':
                return model_task == 'process_discovery'
            elif expected_task == 'conformance_checking':
                return model_task == 'conformance_checking'
            elif expected_task == 'performance_analysis':
                return self._verify_performance_analysis(expected_dict, model_dict)
            elif expected_task == 'filter_by_time_range':
                return self._verify_time_filter(expected_dict, model_dict)
            elif expected_task == 'hybrid':
                return self._verify_hybrid(expected_dict, model_dict)
            elif expected_task == 'verification':
                return self._verify_verification_task(expected_dict, model_dict)
            elif expected_task in ['sim_with_time', 'sim_with_number_products', 'event_prediction']:
                return self._verify_simulation_task(expected_dict, model_dict)
            
            return True
            
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing JSON: {e}")
            return False

    def _extract_json_from_answer(self, model_answer):
        try:
            return json.loads(model_answer)
        except json.JSONDecodeError:
            print("Direct JSON parsing failed, trying to extract JSON from answer.")
        
        response_markers = [
            "[/INST]", 
            "Here's my response:",
            "Here is my response:",
            "Based on the provided context",
            "<|start_header_id|>assistant<|end_header_id|>",
            "<<ANSWER>>"
        ]
        
        # Find the last occurrence of response markers to get actual response
        response_start = 0
        for marker in response_markers:
            idx = model_answer.rfind(marker)
            if idx > response_start:
                response_start = idx
        
        # Extract only the actual response part
        actual_response = model_answer[response_start:] if response_start > 0 else model_answer
        
        match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", actual_response, re.DOTALL)
        if match:
            print("Found JSON block in Markdown format.")
            json_part = match.group(1)
            try:
                return json.loads(json_part)
            except json.JSONDecodeError:
                print(f"Warning: Found a Markdown block that looked like JSON but failed to parse: {json_part}")
        
        def extract_json_objects(text):
            json_objects = []
            i = 0
            while i < len(text):
                if text[i] == '{':
                    # Found start of potential JSON
                    brace_count = 0
                    start = i
                    in_string = False
                    escape = False
                    
                    for j in range(i, len(text)):
                        char = text[j]
                        
                        # Handle string escaping
                        if escape:
                            escape = False
                            continue
                        if char == '\\':
                            escape = True
                            continue
                        
                        # Toggle string state
                        if char == '"':
                            in_string = not in_string
                            continue
                        
                        # Only count braces outside strings
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    # Found complete JSON object
                                    json_str = text[start:j+1]
                                    if '"task"' in json_str:  # Only consider objects with 'task' field
                                        json_objects.append(json_str)
                                    i = j
                                    break
                    i += 1
                else:
                    i += 1
            
            return json_objects
        
        json_candidates = extract_json_objects(actual_response)
        
        if json_candidates:
            print(f"Found {len(json_candidates)} potential JSON objects with 'task' field")
            for i, json_part in enumerate(reversed(json_candidates)):
                try:
                    parsed = json.loads(json_part)
                    print(f"Successfully extracted JSON #{len(json_candidates)-i} from response (length: {len(json_part)} chars)")
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON #{len(json_candidates)-i}: {e}")
                    continue
        
        # Fallback: try any JSON-like structure
        match = re.search(r'(\{.*?\})', actual_response, re.DOTALL)
        if match:
            print("Found a raw JSON-like string in the answer.")
            json_part = match.group(0)
            try:
                return json.loads(json_part)
            except json.JSONDecodeError:
                print(f"Warning: Found a raw JSON-like string that failed to parse: {json_part[:100]}...")
        
        return None
    
    def _reconstruct_json_from_csv(self, damaged_json_str):
        print(f"Reconstructing JSON from damaged string: {damaged_json_str}")
        try:
            cleaned = damaged_json_str.strip().strip('"')
            
            if not cleaned.startswith('{'):
                cleaned = '{' + cleaned
            
            if not cleaned.endswith('}'):
                cleaned = cleaned + '}'

            
            return json.loads(cleaned)
                
        except Exception as e:
            print(f"Error reconstructing JSON: {e}")
            return None
        
    def _verify_factory_info(self, expected, model):
        expected_query = expected.get('query_nl', '').lower().strip()
        model_query = model.get('query_nl', '').lower().strip()
        
        return expected_query == model_query
    
    def _verify_performance_analysis(self, expected, model):
        expected_metric = expected.get('metric', '')
        model_metric = model.get('metric', '')
        
        if expected_metric != model_metric:
            return False
        
        if 'k' in expected:
            return expected.get('k') == model.get('k')
        
        return True

    def _verify_time_filter(self, expected, model):
        return (expected.get('start_date') == model.get('start_date') and
                expected.get('end_date') == model.get('end_date'))
        
    def _verify_hybrid(self, expected, model):
        expected_questions = expected.get('questions', [])
        model_questions = model.get('questions', [])
        
        if len(expected_questions) != len(model_questions):
            return False
        
        expected_types = sorted([q.get('type', '') for q in expected_questions])
        model_types = sorted([q.get('type', '') for q in model_questions])
        
        return expected_types == model_types

    def _verify_verification_task(self, expected, model):
        expected_raw = expected.get('uppaal_query', '')
        model_raw = model.get('uppaal_query', '')

        expected_query = re.sub(r'\s+', '', expected_raw).lower()
        model_query = re.sub(r'\s+', '', model_raw).lower()

    
        print(f"RAW Expected: {repr(expected_raw)}")
        print(f"RAW Model:    {repr(model_raw)}")
        print(f"NORME Expected: '{expected_query}'")
        print(f"NORME Model:    '{model_query}'")
        print("----------------------------------\n")
    
        return expected_query == model_query

    def _verify_simulation_task(self, expected, model):
        task_type = expected.get('task', '')
        
        if task_type != model.get('task', ''):
            return False
        
        if task_type == 'sim_with_time':
            return expected.get('simulation_time') == model.get('simulation_time')
        elif task_type == 'sim_with_number_products':
            return expected.get('target_pieces') == model.get('target_pieces')
        elif task_type == 'event_prediction':
            return expected.get('activities_sequence') == model.get('activities_sequence')
        
        return True
    
    def compute_stats(self):
        total_results = len(self.results)
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        
        # Calculate basic accuracy without sklearn for backward compatibility
        correct_results = sum(int(result['verification_result']) for result in self.results)
        basic_accuracy = (correct_results / total_results) * 100 if total_results > 0 else 0
        
        if self.true_answers and self.predicted_answers:
            binary_true = []
            binary_pred = []
            
        if self.results:
            binary_true = [1] * len(self.results) 
            binary_pred = [1 if result['verification_result'] else 0 for result in self.results]
            
            try:
                self.accuracy = accuracy_score(binary_true, binary_pred)
                self.precision = precision_score(binary_true, binary_pred, zero_division=0)
                self.recall = recall_score(binary_true, binary_pred, zero_division=0)
                self.f1score = f1_score(binary_true, binary_pred, zero_division=0)
                # Note: MCC and AUC are not calculated for evaluation tasks
                # because all ground truth labels are positive (single-class problem)
                # These metrics require both positive and negative classes to be meaningful
            except Exception as e:
                print(f"Error calculating sklearn metrics: {e}")
                self.accuracy = basic_accuracy    


    def write_results_to_file(self):
        file_path = os.path.join(os.path.dirname(__file__), "..", "tests", "evaluation",
                                 f"results_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
        self.compute_stats()

        with open(file_path, 'w') as file:
            file.write('INFORMATION ON THE RUN\n\n')
            for key in self.run_info.keys():
                file.write(f"{key}: {self.run_info[key]}\n")
            file.write('\n-----------------------------------\n')
            file.write(f"Accuracy: {self.accuracy:.4f}\n")
            file.write(f"Precision: {self.precision:.4f}\n")
            file.write(f"Recall: {self.recall:.4f}\n")
            file.write(f"F1-score: {self.f1score:.4f}\n")
            file.write(f"Elapsed: {(self.elapsed_time / 3600):.2f} hours\n")
            file.write("-----------------------------------\n\n")

            for result in self.results:
                file.write(f"Prompt: {result['prompt']}\n")
                file.write(f"Model Answer: {result['model_answer']}\n")
                file.write(f"Expected Answer: {result['expected_answer']}\n")
                file.write(f"Verification Result: {result['verification_result']}\n")
                file.write("\n#####################################################################################\n")


if __name__ == "__main__":
    test_filename = 'hybrid.csv'
    run_data = {
        'LLM ID Gateway': 'gemini-2.5-flash',
        'LLM ID Simulation': 'gemini-2.5-flash',
        'LLM ID Verification': 'gemini-2.5-flash',
        'Max Generated Tokens LLM': 2700,
        'Interaction Modality': 'evaluation-hybrid'
    }
    questions = load_csv_questions(test_filename)
    oracle = AnswerVerificationOracle(run_data)
    oracle.set_test_type('hybrid')
    
    prompt = """"""
    model_answer = """"""
    question = questions[2][0]
    expected_answer = questions[2][1]

    oracle.add_question_expected_answer_pair(question, expected_answer)
    oracle.verify_answer(prompt, question, model_answer)


    