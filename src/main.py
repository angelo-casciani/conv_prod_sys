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
    parser.add_argument('--modality', type=str, default='live', help='Modality to use between: evaluation-simulation, evaluation-verification, evaluation-routing, live')
    args = parser.parse_args()

    return args


def main():
    print("""Welcome! The tasks that are possible on the LEGO Factory are:
          - Simulation:
            - Discrete simulation of the production in a specified time interval in units of time (SimPy);
            - Discrete simulation of the production of a specified number of pieces (SimPy);
            - Prediction of the next station in the production line (SimPy);
          - Verification of temporal properties on the automaton representing the factory (Uppaal).\n""")

    args = parse_arguments()

    model_id_gateway = args.llm_id_gateway
    model_id_simulation = args.llm_id_simulation
    model_id_verification = args.llm_id_verification
    modality = args.modality
    max_new_tokens = args.max_new_tokens
    chain = LLMPipeline(model_id_gateway, model_id_simulation, model_id_verification, HF_AUTH, max_new_tokens)

    run_data = {
        'LLM ID Gateway': model_id_gateway,
        'LLM ID Simulation': model_id_simulation,
        'LLM ID Verification': model_id_verification,
        'Max Generated Tokens LLM': max_new_tokens,
        'Interaction Modality': modality
    }

    if 'evaluation-simulation' in modality:
        chain.evaluate_performance('simulation.csv', run_data)
    elif 'evaluation-verification' in modality:
        chain.evaluate_performance('verification.csv', run_data)
    elif 'evaluation-routing' in modality:
        chain.evaluate_performance('routing.csv', run_data)
    elif 'evaluation-answer' in modality:
        chain.evaluate_performance('answer.csv', run_data)
    else:
        chain.live_prompting(run_data)


if __name__ == "__main__":
    seed_everything(SEED)
    main()
