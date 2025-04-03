import datetime
import os
import time
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score


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
            expected_answer_formatted = expected_answer.lower().replace(' ', '')
            model_answer_formatted = model_answer.lower().replace('\n', ' ').replace(' ', '')
            if expected_answer == "no_answer":
                model_answer_formatted = model_answer.lower()
                result['verification_result'] = False
                if ('uppaal_verification' not in model_answer_formatted and 'factory_simulation' not in model_answer_formatted) or ('uppaal_verification' in model_answer_formatted and 'factory_simulation' in model_answer_formatted):
                    result['verification_result'] = True
            else:
                result['verification_result'] = expected_answer_formatted in model_answer_formatted
            
            self.true_answers.append(expected_answer)
            self.predicted_answers.append(model_answer)
            
            print(f"Answer: {model_answer}\nExpected_answer: {result['expected_answer']}\nResult: {result['verification_result']}")
        self.results.append(result)

        return result['verification_result']


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
            
            for result in self.results:
                binary_true.append(1 if result['verification_result'] else 0)
                binary_pred.append(1 if result['verification_result'] else 0)
            
            try:
                self.accuracy = accuracy_score(binary_true, binary_pred)
                self.precision = precision_score(binary_true, binary_pred, zero_division=0)
                self.recall = recall_score(binary_true, binary_pred, zero_division=0)
                self.f1score = f1_score(binary_true, binary_pred, zero_division=0)
            except Exception as e:
                print(f"Error calculating sklearn metrics: {e}")
                self.accuracy = basic_accuracy / 100


    def write_results_to_file(self):
        file_path = os.path.join(os.path.dirname(__file__), "..", "tests", "validation",
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
