import gradio as gr
from pipeline import LLMPipeline
from argparse import ArgumentParser
from dotenv import load_dotenv
import warnings
from utility import *
import os
import re
import sys
import time
import traceback
import logging
from docker_manager import setup_docker_lifecycle, stop_docker_containers

try:
    from torch import cuda
    DEVICE = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
except ImportError:
    DEVICE = 'cpu' # CPU for API-only

load_dotenv()
HF_AUTH = os.getenv('HF_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SEED = 10
MAX_RESTART_ATTEMPTS = 3
RESTART_DELAY = 5  # seconds
warnings.filterwarnings('ignore')

if os.path.exists('/app'): # For Docker, otherwise use relative path
    LOG_DIR = '/app/log'
else:
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'chatbot_errors.log')),
        logging.StreamHandler(sys.stdout)
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
    parser.add_argument('--modality', type=str, default='live', help='Modality to use between: evaluation-simulation, evaluation-verification, evaluation-routing, live')
    parser.add_argument('--extracted_model', type=bool, default=False, help='True if already exists the file digital_twin.json. Default False')
    parser.add_argument('--extracted_model_failure', type=bool, default=False, help='True if already exists the file digital_twin_with_failure.json. Default False')
    args = parser.parse_args()
    return args


class GradioHandler:
    def __init__(self):
        self.initialized = False
        self.chain = None
        self.initialization_message = None
        self.initialization_attempts = 0
        
    def initialize(self):
        if not self.initialized:
            try:
                args = parse_arguments()
                model_id_gateway = args.llm_id_gateway
                model_id_simulation = args.llm_id_simulation
                model_id_verification = args.llm_id_verification
                modality = args.modality
                max_new_tokens = args.max_new_tokens
                extracted_model = args.extracted_model
                extracted_model_failure = args.extracted_model_failure
                self.initialization_message = "Initializing system and digital twins..."
                logger.info("Starting chatbot initialization")
                self.chain = LLMPipeline(model_id_gateway, model_id_simulation, model_id_verification, HF_AUTH, max_new_tokens, extracted_model, extracted_model_failure)
                self.initialization_message = None

                self.initialized = True
                self.run_data = {
                    'LLM ID Gateway': model_id_gateway,
                    'LLM ID Simulation': model_id_simulation,
                    'LLM ID Verification': model_id_verification,
                    'Max Generated Tokens LLM': max_new_tokens,
                    'Interaction Modality': modality
                }
                logger.info("Chatbot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize chatbot: {str(e)}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                raise
    
    def reset_state(self):
        logger.info("Resetting chatbot state")
        self.initialized = False
        self.chain = None
        self.initialization_message = None
    
    def process_message(self, message, history):
        try:
            if not self.initialized:
                error_msg = "System not initialized. Please restart the chatbot."
                logger.warning(error_msg)
                yield {"role": "assistant", "content": error_msg}
                return
                
            logger.info(f"Processing user message: {message[:100]}...")  # Log first 100 chars
            yield {"role": "assistant", "content": f"Processing: {message}"}
            
            for result in self.chain.live_prompting(query=message, info_run=self.run_data, chatbot=True):
                if "I discovered the process model. The Petri net has been saved at" in result:
                    match = re.search(r"saved at:\s*(\S+)", result)
                    if match:
                        path = match.group(1).rstrip(".")
                        yield [{"role": "assistant", "content": result}, {"role": "assistant", "content": (path,)}]
                    else:
                        yield {"role": "assistant", "content": result}
                else:
                    yield {"role": "assistant", "content": result}
                    
            logger.info("Message processed successfully")
            
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
            yield {"role": "assistant", "content": "Processing interrupted by user."}
            
        except Exception as e:
            error_msg = f"An error occurred while processing your request: {str(e)}"
            logger.error(f"Error processing message: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.info("Attempting to recover by resetting state")
            self.reset_state()
            yield {
                "role": "assistant", 
                "content": f"{error_msg}\n\nThe system has been reset. Please try your request again, or restart the chatbot if the problem persists."
            }

handler = GradioHandler()

welcome_msg = """Hello! I am your assistant for the LEGO Factory production system. 
                 How can I help you today?"""
demo = gr.ChatInterface(
    handler.process_message,
    chatbot=gr.Chatbot(
        value=[{"role": "assistant", "content": welcome_msg}],
        height=400
    ),
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    save_history=True,
    title="LEGO Factory Production System Assistant",
    description="""Welcome! Make sure you inserted the event log in the "log" folder.<br><br>
**Available Tasks:**<br>
• **Simulation:** Production simulation over time, by piece count, next activity prediction, maintenance scenarios<br>
• **Verification:** Temporal property checking on factory automaton<br>
• **Process Mining:** Process discovery (Petri nets), conformance checking, performance analysis, log filtering<br>
• **Hybrid Reasoning:** Multi-step workflows combining simulation, verification, and failure analysis<br><br>
*Note: Use actual station names (e.g., station11, station21, station41, ...)*<br><br>"""
)

def launch_chatbot_with_fallback():
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
                handler.reset_state()
            logger.info(f"Starting chatbot (attempt {attempt + 1}/{MAX_RESTART_ATTEMPTS})")
            setup_docker_lifecycle()
            print("Initializing chatbot and digital twins...")
            handler.initialize()
            print("Chatbot ready!")
            
            demo.launch()
            logger.info("Chatbot exited normally")
            break
            
        except KeyboardInterrupt:
            logger.info("Chatbot interrupted by user (Ctrl+C)")
            print("\n\nShutting down chatbot gracefully...")
            stop_containers()
            sys.exit(0)
            
        except Exception as e:
            attempt += 1
            logger.error(f"Exception occurred in chatbot (attempt {attempt}/{MAX_RESTART_ATTEMPTS}): {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            if attempt < MAX_RESTART_ATTEMPTS:
                print(f"\n{'='*60}")
                print(f"ERROR: An exception occurred: {str(e)}")
                print(f"{'='*60}\n")
            else:
                print(f"\n{'='*60}")
                print(f"FATAL ERROR: Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) reached.")
                print(f"Last error: {str(e)}")
                print(f"Please check the log file at 'log/chatbot_errors.log' for details.")
                print(f"{'='*60}\n")
                logger.critical("Maximum restart attempts reached. Chatbot terminating.")
                stop_containers()
                sys.exit(1)


if __name__ == "__main__":
    launch_chatbot_with_fallback()