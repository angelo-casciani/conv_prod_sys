import time
import gradio as gr
from pipeline import LLMPipeline
from argparse import ArgumentParser
from dotenv import load_dotenv
from torch import cuda
import warnings
from utility import *
import os

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


class GradioHandler:
    def __init__(self):
        self.initialized = False
        self.chain = None
        
    def initialize(self):
        if not self.initialized:
            args = parse_arguments()
            model_id_gateway = args.llm_id_gateway
            model_id_simulation = args.llm_id_simulation
            model_id_verification = args.llm_id_verification
            modality = args.modality
            max_new_tokens = args.max_new_tokens
            self.chain = LLMPipeline(model_id_gateway, model_id_simulation, model_id_verification, HF_AUTH, max_new_tokens)

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
            self.initialize()
            # if len(history) == 0:
            #     welcome_msg = """Welcome! The tasks that are possible on the LEGO Factory are:
            #                 - Simulation:
            #                 - Discrete simulation of the production in a specified time interval in units of time (SimPy);
            #                 - Discrete simulation of the production of a specified number of pieces (SimPy);
            #                 - Prediction of the next station in the production line (SimPy);
            #                 - Verification of temporal properties on the automaton representing the factory (Uppaal).

            #                 Please tell me what you'd like to do!
            #                 """
            #     yield welcome_msg
            #     return
            
            yield f"Processing: {message}"
            
            for result in self.chain.live_prompting(query=message, info_run=self.run_data, chatbot=True):
                yield result
                
        except Exception as e:
            yield f"Error occurred: {str(e)}"

handler = GradioHandler()

welcome_msg = """Welcome! The tasks that are possible on the LEGO Factory are:
                            - Simulation:
                            - Discrete simulation of the production in a specified time interval in units of time (SimPy);
                            - Discrete simulation of the production of a specified number of pieces (SimPy);
                            - Prediction of the next station in the production line (SimPy);
                            - Verification of temporal properties on the automaton representing the factory (Uppaal).

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
    title="LEGO Factory Assistant",
    description="Ask me about simulations and verifications for the LEGO Factory!"
)

if __name__ == "__main__":
    demo.launch()