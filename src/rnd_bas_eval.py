import os
import json
import numpy as np
import pandas as pd
from typing import Dict
from argparse import ArgumentParser
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import pm4py

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_ollama import ChatOllama
    LOCAL_MODEL_SUPPORT = True
except ImportError:
    LOCAL_MODEL_SUPPORT = False

load_dotenv()

# 'model_id' for 'ollama' entries must match a model tag already pulled/created
# locally (`ollama pull <tag>` or `ollama create <tag> -f Modelfile`), consistent
# with the tags used across the rest of the pipeline (see cmd4tests.sh).
MODEL_CONFIGS = {
    'llama-3.2-1b': {
        'model_id': 'meta-llama/Llama-3.2-1B-Instruct',
        'model_provider': 'ollama',
    },
    'qwen2.5-7b': {
        'model_id': 'Qwen/Qwen2.5-7B-Instruct',
        'model_provider': 'ollama',
    },
    'phi-4': {
        'model_id': 'microsoft/phi-4',
        'model_provider': 'ollama',
    },
    'ministral-8b': {
        'model_id': 'mistralai/Ministral-8B-Instruct-2410',
        'model_provider': 'ollama',
    },
    'llama-3.1-8b': {
        'model_id': 'meta-llama/Llama-3.1-8B-Instruct',
        'model_provider': 'ollama',
    },
    'gemini-2.5-flash': {
        'model_id': 'gemini-2.5-flash',
        'model_provider': 'google_genai',
    },
    'gemini-2.5-pro': {
        'model_id': 'gemini-2.5-pro',
        'model_provider': 'google_genai',
    },
}

DEFAULT_LLM_MODELS = [
    'llama-3.2-1b',
    'qwen2.5-7b',
    'phi-4',
    'ministral-8b',
    'llama-3.1-8b',
    'gemini-2.5-flash',
    'gemini-2.5-pro',
]


def parse_arguments():
    parser = ArgumentParser(description="Run random and LLM-only baselines.")
    parser.add_argument(
        '--llm_models',
        type=str,
        default=','.join(DEFAULT_LLM_MODELS),
        help='Comma-separated model aliases. Supported: ' + ', '.join(MODEL_CONFIGS.keys())
    )
    parser.add_argument(
        '--num_random_runs',
        type=int,
        default=10,
        help='Number of runs for random baseline.'
    )
    return parser.parse_args()


def parse_boolean(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ('true', '1', 'yes', 'satisfied'):
            return True
        elif value_lower in ('false', '0', 'no', 'not satisfied'):
            return False
        if 'true' in value_lower and 'false' not in value_lower:
            return True
        if 'false' in value_lower and 'true' not in value_lower:
            return False
    return bool(value)


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def calculate_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(y_true == y_pred) * 100


class RandomBaseline:
    def __init__(self, dataset_path: str):
        self.df = pd.read_csv(dataset_path)
        numeric_answers = self.df[self.df['type'] == 'simulation']['answer'].astype(float)
        self.min_value = numeric_answers.min()
        self.max_value = numeric_answers.max()
    
    def predict_boolean(self) -> bool:
        return np.random.choice([True, False])
    def predict_numeric(self) -> float:
        return np.random.uniform(self.min_value, self.max_value)
    def evaluate(self, dataset_path: str) -> Dict[str, float]:
        df = pd.read_csv(dataset_path)
        
        simulation_rows = df[df['type'] == 'simulation']
        verification_rows = df[df['type'] == 'verification']
        simulation_predictions = [self.predict_numeric() for _ in range(len(simulation_rows))]
        verification_predictions = [self.predict_boolean() for _ in range(len(verification_rows))]
        verification_true_answers = verification_rows['answer'].apply(parse_boolean)
        mape = calculate_mape(simulation_rows['answer'].values, simulation_predictions)
        accuracy = calculate_accuracy(verification_true_answers.values, verification_predictions)
        
        return {
            'mape': mape,
            'accuracy': accuracy,
            'simulation_samples': len(simulation_rows),
            'verification_samples': len(verification_rows)
        }


class LLMOnlyBaseline:
    
    def __init__(self, model_id='gemini-2.5-flash', model_provider='google_genai', api_key: str = None):
        self.model_id = model_id
        self.model_provider = model_provider

        if self.model_provider == 'google_genai':
            if api_key is None:
                api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                os.environ['GOOGLE_API_KEY'] = api_key

        self.model = self._initialize_model(model_id, model_provider)
        self.system_prompt = self._load_system_prompt()
        self.domain_description = self._load_domain_description()

    def _initialize_model(self, model_id: str, model_provider: str):
        """Create the chat model with provider-specific fallbacks for server environments."""
        if model_provider == 'google_genai':
            if ChatGoogleGenerativeAI is None:
                raise RuntimeError(
                    "Missing dependency for Google models: install `langchain-google-genai`."
                )
            return ChatGoogleGenerativeAI(
                model=model_id,
                temperature=0.1,
                max_tokens=2048,
            )

        if model_provider == 'ollama':
            if not LOCAL_MODEL_SUPPORT:
                raise RuntimeError(
                    "Missing dependency for Ollama models: install `langchain-ollama`."
                )
            return ChatOllama(
                model=model_id,
                temperature=0.1,
                max_tokens=2048,
            )

        # Keep support for any additional provider we may add later.
        return init_chat_model(
            model_id,
            model_provider=model_provider,
            temperature=0.1,
            max_tokens=2048,
        )
    
    def _load_system_prompt(self) -> str:
        prompts_path = os.path.join(os.path.dirname(__file__), 'prompts.json')
        try:
            with open(prompts_path, 'r') as f:
                prompts = json.load(f)
                return prompts.get('system_prompt', '')
        except:
            return "You are an expert assistant for a LEGO factory production system."
    
    def _load_domain_description(self) -> str:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'parameters', 'digital_twin.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return f"LEGO Factory Configuration:\n{json.dumps(config, indent=2)}"
        except:
            return "LEGO Factory: Multi-station production system with stochastic processing times."
    
    def _load_event_log_sample(self) -> str:
        log_path = os.path.join(os.path.dirname(__file__), '..', 'log', 'event_log_250905.xes')
        try:
            log = pm4py.read_xes(log_path)
            
            num_traces = min(5, len(log))
            sample_traces = []
            
            for i, trace in enumerate(log[:num_traces]):
                case_id = trace.attributes.get('concept:name', f'Case_{i}')
                events = []
                for event in trace:
                    activity = event.get('concept:name', 'Unknown')
                    timestamp = event.get('time:timestamp', '')
                    events.append(f"{activity} @ {timestamp}")
                
                trace_str = f"Trace {i+1} (Case: {case_id}):\n  " + "\n  ".join(events)
                sample_traces.append(trace_str)
            
            return f"Event Log Sample ({num_traces} traces):\n\n" + "\n\n".join(sample_traces)
        except Exception as e:
            return f"Event log sample unavailable: {str(e)}"
    
    def predict(self, question: str, task_type: str) -> any:
        context = f"{self.system_prompt}\n\n{self.domain_description}\n\n{self._load_event_log_sample()}"
        if task_type == 'verification':
            modified_question = f"{question} Please answer with only 'True' or 'False'."
            prompt = f"{context}\n\nQuestion: {modified_question}\n\nAnswer:"
        else:
            prompt = f"{context}\n\nQuestion: {question}\n\nProvide only a numeric answer:"
        
        try:
            response = self.model.invoke(prompt)
            if hasattr(response, 'content'):
                answer_text = response.content.strip()
            else:
                answer_text = str(response).strip()
            
            if task_type == 'verification':
                parsed_answer = parse_boolean(answer_text)
                return parsed_answer
            else:
                try:
                    parsed_value = float(''.join(c for c in answer_text if c.isdigit() or c == '.' or c == '-'))
                    return parsed_value
                except:
                    return 0.0
        except Exception as e:
            print(f"Error predicting with LLM: {e}")
            if task_type == 'verification':
                return True
            else:
                return 0.0
    
    def evaluate(self, dataset_path: str) -> Dict[str, float]:
        df = pd.read_csv(dataset_path)
        
        simulation_predictions = []
        verification_predictions = []
        
        print("Evaluating LLM-Only Baseline...")
        for idx, row in df.iterrows():
            question = row['question']
            task_type = row['type']
            expected_answer = row['answer']
            
            prediction = self.predict(question, task_type)
            
            if task_type == 'simulation':
                simulation_predictions.append(prediction)
                result_match = "✓" if abs(prediction - float(expected_answer)) < 0.1 else "✗"
                print(f"  [{idx+1}/{len(df)}] {result_match} Simulation: {question[:50]}...")
                print(f"      Expected: {expected_answer}, Predicted: {prediction}")
            else:
                verification_predictions.append(prediction)
                expected_bool = parse_boolean(expected_answer)
                result_match = "✓" if prediction == expected_bool else "✗"
                print(f"  [{idx+1}/{len(df)}] {result_match} Verification: {question[:50]}...")
                print(f"      Expected: {expected_bool}, Predicted: {prediction}")
        
        simulation_rows = df[df['type'] == 'simulation']
        verification_rows = df[df['type'] == 'verification']
        
        verification_true_answers = verification_rows['answer'].apply(parse_boolean)
        
        mape = calculate_mape(simulation_rows['answer'].values, simulation_predictions)
        accuracy = calculate_accuracy(verification_true_answers.values, verification_predictions)
        
        print(f"\nLLM-Only Baseline Results:")
        print(f"  MAPE: {mape:.2f}%")
        print(f"  Accuracy: {accuracy:.2f}%\n")
        
        return {
            'mape': mape,
            'accuracy': accuracy,
            'simulation_samples': len(simulation_rows),
            'verification_samples': len(verification_rows)
        }


def run_evaluation(dataset_path: str, llm_models=None, num_random_runs: int = 10):
    if llm_models is None:
        llm_models = DEFAULT_LLM_MODELS
    
    print("="*80)
    print("BASELINE EVALUATION")
    print("="*80)
    print(f"\nDataset: {dataset_path}")
    
    print("\n" + "-"*80)
    print("1. RANDOM BASELINE")
    print("-"*80)
    
    random_baseline = RandomBaseline(dataset_path)
    random_results = []
    
    for run in range(num_random_runs):
        results = random_baseline.evaluate(dataset_path)
        random_results.append(results)
        print(f"Run {run+1}/{num_random_runs}: MAPE={results['mape']:.2f}%, Accuracy={results['accuracy']:.2f}%")
    
    random_avg_mape = np.mean([r['mape'] for r in random_results])
    random_avg_accuracy = np.mean([r['accuracy'] for r in random_results])
    random_std_mape = np.std([r['mape'] for r in random_results])
    random_std_accuracy = np.std([r['accuracy'] for r in random_results])
    
    print(f"\nRandom Baseline Average (over {num_random_runs} runs):")
    print(f"  MAPE: {random_avg_mape:.2f}% ± {random_std_mape:.2f}%")
    print(f"  Accuracy: {random_avg_accuracy:.2f}% ± {random_std_accuracy:.2f}%")
    
    print("\n" + "-"*80)
    print("2. LLM-ONLY BASELINE (multiple models)")
    print("-"*80)

    llm_results_by_model = {}
    failed_models = {}

    for model_alias in llm_models:
        model_key = model_alias.strip().lower()
        model_cfg = MODEL_CONFIGS.get(model_key)
        if model_cfg is None:
            failed_models[model_alias] = 'Unsupported model alias'
            print(f"\nSkipping {model_alias}: unsupported model alias")
            continue

        print(f"\nEvaluating model: {model_alias} ({model_cfg['model_id']}, provider={model_cfg['model_provider']})")
        try:
            llm_baseline = LLMOnlyBaseline(
                model_id=model_cfg['model_id'],
                model_provider=model_cfg['model_provider'],
            )
            llm_results = llm_baseline.evaluate(dataset_path)
            llm_results_by_model[model_alias] = llm_results
        except Exception as e:
            failed_models[model_alias] = str(e)
            print(f"Failed {model_alias}: {e}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n{'Baseline':<25} {'MAPE (%)':<20} {'Accuracy (%)':<20}")
    print("-"*80)
    print(f"{'Random':<25} {random_avg_mape:>8.2f} ± {random_std_mape:<7.2f} {random_avg_accuracy:>8.2f} ± {random_std_accuracy:<7.2f}")
    for model_alias in llm_models:
        if model_alias in llm_results_by_model:
            result = llm_results_by_model[model_alias]
            print(f"{('LLM-Only (' + model_alias + ')'):<25} {result['mape']:>8.2f} {'':>9} {result['accuracy']:>8.2f}")
        elif model_alias in failed_models:
            print(f"{('LLM-Only (' + model_alias + ')'):<25} {'FAILED':>8} {'':>9} {'FAILED':>8}")
    print("="*80)
    
    results_summary = {
        'random_baseline': {
            'mape_mean': random_avg_mape,
            'mape_std': random_std_mape,
            'accuracy_mean': random_avg_accuracy,
            'accuracy_std': random_std_accuracy
        },
        'llm_only_baseline': llm_results_by_model,
        'failed_models': failed_models,
    }
    
    output_path = os.path.join(os.path.dirname(dataset_path), 'evaluation_results.json')
    with open(output_path, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return results_summary


if __name__ == "__main__":
    args = parse_arguments()
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'answers-dataset.csv')
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        print("Please generate the dataset first using generate_answers_dataset()")
        exit(1)
    
    selected_models = [m.strip() for m in args.llm_models.split(',') if m.strip()]
    run_evaluation(dataset_path, llm_models=selected_models, num_random_runs=args.num_random_runs)
