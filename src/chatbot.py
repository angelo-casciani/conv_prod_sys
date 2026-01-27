import gradio as gr
from pipeline import LLMPipeline
from argparse import ArgumentParser
from dotenv import load_dotenv
from torch import cuda
import warnings
from utility import *
import os
import re
from docker_manager import setup_docker_lifecycle

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
    parser.add_argument('--extracted_model', type=bool, default=False, help='True if already exists the file digital_twin.json. Default False')
    parser.add_argument('--extracted_model_failure', type=bool, default=False, help='True if already exists the file digital_twin_with_failure.json. Default False')
    args = parser.parse_args()
    return args


class GradioHandler:
    def __init__(self):
        self.initialized = False
        self.chain = None
        self.initialization_message = None
        
    def initialize(self):
        if not self.initialized:
            args = parse_arguments()
            model_id_gateway = args.llm_id_gateway
            model_id_simulation = args.llm_id_simulation
            model_id_verification = args.llm_id_verification
            modality = args.modality
            max_new_tokens = args.max_new_tokens
            extracted_model = args.extracted_model
            extracted_model_failure = args.extracted_model_failure
            self.initialization_message = "Initializing system and digital twins..."
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
    
    def process_message(self, message, history):
        try:
            if not self.initialized:
                yield {"role": "assistant", "content": "System not initialized. Please restart the chatbot."}
                return
                
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
        except Exception as e:
            yield {"role": "assistant", "content": f"Error occurred: {str(e)}"}

handler = GradioHandler()

welcome_msg = """Welcome! Make sure you inserted the event log in the "log" folder. The tasks that are possible on the LEGO factory are:
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
                            
                            Note: You can refer to stations using their actual names (e.g., station11, station21, station41, corner2, splitter1).

                            Please tell me what you'd like to do!
                            """
demo = gr.ChatInterface(
    handler.process_message,
    type="messages",
    chatbot=gr.Chatbot(
        type="messages",
        value=[{"role": "assistant", "content": welcome_msg}] 
    ),
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    save_history=True,
    title="LEGO Factory Production System Assistant",
    description="Ask me about simulations, verifications and process mining for the extracted Digital Twin!",
    theme="ocean"
)

if __name__ == "__main__":
    setup_docker_lifecycle()
    print("Initializing chatbot and digital twins...")
    handler.initialize()
    print("Chatbot ready!")
    demo.launch()