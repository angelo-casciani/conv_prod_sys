from argparse import ArgumentParser
from dotenv import load_dotenv
from torch import cuda
import warnings

from pipeline import *
from utility import *


DEVICE = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
load_dotenv()
HF_AUTH = os.getenv('HF_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SEED = 10
warnings.filterwarnings('ignore')


def parse_arguments():
    parser = ArgumentParser(description="Run LLM Generation.")
    parser.add_argument('--llm_id_gateway', type=str, default='gpt-4o-mini', help='LLM model identifier for Gateway')
    parser.add_argument('--llm_id_simulation', type=str, default='gpt-4o-mini', help='LLM model identifier for Simulation')
    parser.add_argument('--llm_id_verification', type=str, default='gpt-4o-mini', help='LLM model identifier for Verification')
    parser.add_argument('--max_new_tokens', type=int, help='Maximum number of tokens to generate', default=512)
    parser.add_argument('--modality', type=str, default='live', help='Modality to use between: evaluation-simulation, evaluation-verification, evaluation-routing, evaluation-factory_info, evaluation-process_mining, evaluation-hybrid, evaluation-qualitative-hybrid, evaluation-simulation-zeroshot, evaluation-verification-zeroshot, evaluation-routing-zeroshot, evaluation-factory_info-zeroshot, evaluation-process_mining-zeroshot, evaluation-hybrid-zeroshot, live')
    parser.add_argument('--extracted_model', type=bool, default=False, help='True if already exists the file digital_twin.json. Default False')
    parser.add_argument('--extracted_model_failure', type=bool, default=False, help='True if already exists the file digital_twin_with_failure.json. Default False')
    args = parser.parse_args()

    return args


def main():
    print("""Welcome! Make sure you inserted the event log in the "log" folder. The tasks that are possible on the extracted Digital Twin are:
          - Simulation:
            - Discrete simulation of the production in a specified time interval in units of time (SimPy);
            - Discrete simulation of the production of a specified number of pieces (SimPy);
            - Prediction of the next activity in the production line (SimPy);
            - Discrete simulation considering the potential maintenanc time of an activity (SimPy);
          - Verification of temporal properties on the automaton representing the factory (Uppaal).
          - Process Mining:
            - Extract a process model (e.g., Petri Net) from an event log;
            - Conformance_checking to verify if the observed executions in the log match a given process model;
            - Performance_analysis' to compute performance indicators such as throughput time or activity frequencies;
            - Filter the log between a specific time range.\n""")

    args = parse_arguments()

    model_id_gateway = args.llm_id_gateway
    model_id_simulation = args.llm_id_simulation
    model_id_verification = args.llm_id_verification
    modality = args.modality
    max_new_tokens = args.max_new_tokens
    extracted_model = args.extracted_model
    extracted_model_failure = args.extracted_model_failure
    chain = LLMPipeline(model_id_gateway, model_id_simulation, model_id_verification, HF_AUTH, max_new_tokens, extracted_model, extracted_model_failure)

    run_data = {
        'LLM ID Gateway': model_id_gateway,
        'LLM ID Simulation': model_id_simulation,
        'LLM ID Verification': model_id_verification,
        'Max Generated Tokens LLM': max_new_tokens,
        'Interaction Modality': modality
    }

    if modality == 'evaluation-simulation' or modality == 'evaluation-simulation-zeroshot':
        chain.evaluate_performance('simulation.csv', run_data)
    elif modality == 'evaluation-verification' or modality == 'evaluation-verification-zeroshot':
        chain.evaluate_performance('verification.csv', run_data)
    elif modality == 'evaluation-routing' or modality == 'evaluation-routing-zeroshot':
        chain.evaluate_performance('routing.csv', run_data)
    elif modality == 'evaluation-factory_info' or modality == 'evaluation-factory_info-zeroshot':
        chain.evaluate_performance('factory_info.csv', run_data)
    elif modality == 'evaluation-process_mining' or modality == 'evaluation-process_mining-zeroshot':
        chain.evaluate_performance('process_mining.csv', run_data)
    elif modality == 'evaluation-hybrid' or modality == 'evaluation-hybrid-zeroshot':
        chain.evaluate_performance('hybrid.csv', run_data)
    elif 'evaluation-qualitative-hybrid' in modality:
        chain.evaluate_qualitative_hybrid('qualitative_hybrid_requests.txt', run_data)
    else:
        for _ in chain.live_prompting(info_run=run_data, chatbot=False):
            pass


if __name__ == "__main__":
    seed_everything(SEED)
    main()
