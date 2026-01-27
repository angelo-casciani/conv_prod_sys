from argparse import ArgumentParser
from dotenv import load_dotenv
from torch import cuda
import warnings
import sys
import time
import traceback
import logging

from pipeline import *
from utility import *
from docker_manager import setup_docker_lifecycle, stop_docker_containers


DEVICE = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
load_dotenv()
HF_AUTH = os.getenv('HF_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SEED = 10
MAX_RESTART_ATTEMPTS = 3
RESTART_DELAY = 5  # seconds
warnings.filterwarnings('ignore')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/main_errors.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


def stop_containers():
    try:
        logger.info("Stopping Docker containers...")
        stop_docker_containers()
        return True
    except Exception as e:
        logger.error(f"Error stopping containers: {str(e)}")
        return False


def parse_arguments():
    parser = ArgumentParser(description="Run LLM Generation.")
    parser.add_argument('--llm_id_gateway', type=str, default='gemini-2.5-flash', help='LLM model identifier for Gateway')
    parser.add_argument('--llm_id_simulation', type=str, default='gemini-2.5-flash', help='LLM model identifier for Simulation')
    parser.add_argument('--llm_id_verification', type=str, default='gemini-2.5-flash', help='LLM model identifier for Verification')
    parser.add_argument('--max_new_tokens', type=int, help='Maximum number of tokens to generate', default=32768)
    parser.add_argument('--modality', type=str, default='live', help='Modality to use between: evaluation-simulation, evaluation-verification, evaluation-routing, evaluation-factory_info, evaluation-process_mining, evaluation-hybrid, evaluation-qualitative-hybrid, evaluation-simulation-zeroshot, evaluation-verification-zeroshot, evaluation-routing-zeroshot, evaluation-factory_info-zeroshot, evaluation-process_mining-zeroshot, evaluation-hybrid-zeroshot, live')
    parser.add_argument('--extracted_model', type=bool, default=False, help='True if already exists the file digital_twin.json. Default False')
    parser.add_argument('--extracted_model_failure', type=bool, default=False, help='True if already exists the file digital_twin_with_failure.json. Default False')
    args = parser.parse_args()

    return args


def main():
    setup_docker_lifecycle()
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

    print("""Welcome! Make sure you inserted the event log in the "log" folder. The tasks that are possible on the LEGO factory are:
          - Simulation:
            - Discrete simulation of the production in a specified time interval in units of time;
            - Discrete simulation of the production of a specified number of pieces;
            - Prediction of the next activity in the production line;
            - Discrete simulation considering the potential maintenance time of a station;
          - Verification of temporal properties on the automaton representing the factory.
          - Process Mining:
            - Discover a process model (i.e., Petri Net) from an event log through the Inductive Miner;
            - Conformance checking (via token-based replay) to verify if the observed executions in the log match a given process model;            
            - Performance analysis to compute performance indicators such as throughput time or station frequencies;
            - Filter the log between a specific time range;
          - Hybrid Reasoning:
            - Combine simulation, verification, and failure analysis in multi-step workflows;
            - Predict failure patterns, maintenance needs, and reliability for specific stations;
            - Estimate maintenance delays and their impact on production;
            - Answer complex queries involving multiple reasoning tasks.
          
          Note: You can refer to stations using their actual names (e.g., station11, station21, station41, ...).\n""")


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


def run_with_fallback():
    attempt = 0
    while attempt < MAX_RESTART_ATTEMPTS:
        try:
            if attempt > 0:
                logger.info(f"Restart attempt {attempt}/{MAX_RESTART_ATTEMPTS}")
                print(f"\n Attempting restart ({attempt}/{MAX_RESTART_ATTEMPTS})...")
                print("  Stopping existing containers...")
                stop_containers()
                print(f" Waiting {RESTART_DELAY} seconds before restart...")
                time.sleep(RESTART_DELAY)
            logger.info(f"Starting main application (attempt {attempt + 1}/{MAX_RESTART_ATTEMPTS})")
            seed_everything(SEED)
            main()
            logger.info("Application exited normally")
            break
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user (Ctrl+C)")
            print("\n\nShutting down gracefully...")
            stop_containers()
            sys.exit(0)
            
        except Exception as e:
            attempt += 1
            logger.error(f"Exception occurred in main (attempt {attempt}/{MAX_RESTART_ATTEMPTS}): {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            if attempt < MAX_RESTART_ATTEMPTS:
                print(f"\n{'='*60}")
                print(f"ERROR: An exception occurred: {str(e)}")
                print(f"{'='*60}\n")
            else:
                print(f"\n{'='*60}")
                print(f"FATAL ERROR: Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached.")
                print(f"Last error: {str(e)}")
                print(f"Please check the log file at 'log/main_errors.log' for details.")
                print(f"{'='*60}\n")
                logger.critical("Maximum restart attempts reached. Application terminating.")
                stop_containers()
                sys.exit(1)


if __name__ == "__main__":
    run_with_fallback()
