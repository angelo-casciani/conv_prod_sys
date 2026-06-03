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
import json
import uuid
import threading
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

LOG_DIR = get_runtime_log_dir()
INTERACTION_LOG_DIR = get_interaction_log_dir()


def _build_file_handler(path, formatter=None):
    try:
        handler = logging.FileHandler(path)
    except OSError as exc:
        fallback = logging.StreamHandler(sys.stdout)
        if formatter is not None:
            fallback.setFormatter(formatter)
        fallback._logging_fallback_error = exc
        return fallback

    if formatter is not None:
        handler.setFormatter(formatter)
    return handler


main_log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
main_file_handler = _build_file_handler(os.path.join(LOG_DIR, 'chatbot_errors.log'), main_log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(main_log_formatter)

main_handlers = [main_file_handler]
if not hasattr(main_file_handler, '_logging_fallback_error'):
    main_handlers.append(console_handler)

logging.basicConfig(
    level=logging.INFO,
    handlers=main_handlers
)
logger = logging.getLogger(__name__)

if hasattr(main_file_handler, '_logging_fallback_error'):
    logger.warning(
        "Could not open chatbot error log file in %s; logging to stdout only. Error: %s",
        LOG_DIR,
        main_file_handler._logging_fallback_error,
    )

interaction_logger = logging.getLogger("chatbot_interactions")
interaction_logger.setLevel(logging.INFO)
interaction_handler = _build_file_handler(
    os.path.join(INTERACTION_LOG_DIR, 'chatbot_interactions.log'),
    logging.Formatter('%(asctime)s - %(message)s')
)
interaction_logger.addHandler(interaction_handler)
interaction_logger.propagate = False

if hasattr(interaction_handler, '_logging_fallback_error'):
    logger.warning(
        "Could not open interaction log file in %s; interaction logs will go to stdout. Error: %s",
        INTERACTION_LOG_DIR,
        interaction_handler._logging_fallback_error,
    )


def log_chat_interaction(role, content, session_id="unknown", request_id="unknown"):
    if isinstance(content, gr.FileData):
        payload = f"file:{content.path}"
    else:
        payload = str(content).replace("\n", "\\n")

    entry = {
        "session_id": str(session_id),
        "request_id": str(request_id),
        "role": role.upper(),
        "content": payload,
    }
    interaction_logger.info(json.dumps(entry, ensure_ascii=False))

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
    parser.add_argument('--llm_id_gateway', type=str, default='gemini-3.1-flash-lite', help='LLM model identifier for Gateway')
    parser.add_argument('--llm_id_simulation', type=str, default='gemini-3.1-flash-lite', help='LLM model identifier for Simulation')
    parser.add_argument('--llm_id_verification', type=str, default='gemini-3.1-flash-lite', help='LLM model identifier for Verification')
    parser.add_argument('--max_new_tokens', type=int, help='Maximum number of tokens to generate', default=32768)
    parser.add_argument('--modality', type=str, default='live', help='Modality to use between: evaluation-simulation, evaluation-verification, evaluation-routing, live')
    parser.add_argument('--extracted_model', type=bool, default=False, help='True if already exists the file digital_twin.json. Default False')
    parser.add_argument('--extracted_model_failure', type=bool, default=False, help='True if already exists the file digital_twin_with_failure.json. Default False')
    parser.add_argument('--ensure_skg', type=bool, default=True, help='Ensure an SKG automaton exists (runs LSHA if needed)')
    args = parser.parse_args()
    return args


class GradioHandler:
    def __init__(self):
        self.initialized = False
        self.chain = None
        self.initialization_message = None
        self.initialization_attempts = 0
        self.session_states = {}
        self.session_locks = {}
        self._session_guard = threading.Lock()
        
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
                ensure_skg = args.ensure_skg
                self.initialization_message = "Initializing system and digital twins..."
                logger.info("Starting chatbot initialization")
                self.chain = LLMPipeline(model_id_gateway, model_id_simulation, model_id_verification, HF_AUTH, max_new_tokens, extracted_model, extracted_model_failure)
                if ensure_skg and hasattr(self.chain, "_ensure_skg_exists"):
                    logger.info("Ensuring SKG automaton exists...")
                    self.chain._ensure_skg_exists()
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
        with self._session_guard:
            self.session_states.clear()
            self.session_locks.clear()

    def _resolve_session_id(self, request):
        if request is not None:
            session_hash = getattr(request, "session_hash", None)
            if session_hash:
                return str(session_hash)
        return f"legacy-{threading.get_ident()}"

    def _get_or_create_session_context(self, session_id):
        with self._session_guard:
            if session_id not in self.session_states:
                self.session_states[session_id] = {
                    "pending_simulation_request": None,
                    "hybrid_simulation_defaults": None,
                    "sim_time": None,
                }
            if session_id not in self.session_locks:
                self.session_locks[session_id] = threading.Lock()

            return self.session_states[session_id], self.session_locks[session_id]

    def _reset_single_session(self, session_id):
        with self._session_guard:
            self.session_states[session_id] = {
                "pending_simulation_request": None,
                "hybrid_simulation_defaults": None,
                "sim_time": None,
            }
    
    def process_message(self, message, history, request: gr.Request = None):
        session_id = self._resolve_session_id(request)
        request_id = uuid.uuid4().hex
        session_state, session_lock = self._get_or_create_session_context(session_id)
        info_run = dict(self.run_data) if hasattr(self, "run_data") else {}
        info_run["Session ID"] = session_id
        info_run["Request ID"] = request_id

        try:
            if not self.initialized:
                error_msg = "System not initialized. Please restart the chatbot."
                logger.warning(error_msg)
                log_chat_interaction("assistant", error_msg, session_id=session_id, request_id=request_id)
                yield {"role": "assistant", "content": error_msg}
                return

            with session_lock:
                logger.info(
                    "Processing user message [session=%s request=%s]: %s...",
                    session_id,
                    request_id,
                    message[:100],
                )
                log_chat_interaction("user", message, session_id=session_id, request_id=request_id)
                yield {"role": "assistant", "content": f"Processing: {message}"}

                for result in self.chain.live_prompting(
                    query=message,
                    info_run=info_run,
                    chatbot=True,
                    session_state=session_state,
                    request_id=request_id,
                ):
                    if "I discovered the Petri net representing the process. The Petri net has been saved at" in result:
                        match = re.search(r"saved at:\s*(\S+)", result)
                        if match:
                            path = match.group(1).rstrip(".")
                            log_chat_interaction("assistant", result, session_id=session_id, request_id=request_id)
                            yield {"role": "assistant", "content": result}
                            log_chat_interaction("assistant", f"file:{path}", session_id=session_id, request_id=request_id)
                            yield {"role": "assistant", "content": gr.FileData(path=path, mime_type="image/png")}
                        else:
                            log_chat_interaction("assistant", result, session_id=session_id, request_id=request_id)
                            yield {"role": "assistant", "content": result}
                    else:
                        log_chat_interaction("assistant", result, session_id=session_id, request_id=request_id)
                        yield {"role": "assistant", "content": result}

            logger.info("Message processed successfully")
            
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
            log_chat_interaction("assistant", "Processing interrupted by user.", session_id=session_id, request_id=request_id)
            yield {"role": "assistant", "content": "Processing interrupted by user."}
            
        except Exception as e:
            error_msg = f"An error occurred while processing your request: {str(e)}"
            logger.error(f"Error processing message: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.info("Attempting to recover by resetting only the active session state")
            self._reset_single_session(session_id)
            log_chat_interaction("assistant", error_msg, session_id=session_id, request_id=request_id)
            yield {
                "role": "assistant", 
                "content": f"{error_msg}\n\nYour session context has been reset. Please try your request again."
            }

handler = GradioHandler()

CHAT_HISTORY_CSS = """
[class*='history'] [class*='item'], [data-testid*='history'] [class*='item'] {
    position: relative;
}

.history-trash-btn {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    opacity: 0.65;
    padding: 2px 4px;
    border-radius: 6px;
}

.history-trash-btn:hover {
    opacity: 1;
    background: rgba(200, 200, 200, 0.2);
}

.chatbot-welcome-message {
    margin: 12px 0;
    padding: 12px 14px;
    max-width: min(680px, 92%);
    border-radius: 14px;
    background: rgba(240, 244, 248, 0.95);
    border: 1px solid rgba(160, 174, 192, 0.35);
    color: #1f2937;
    white-space: pre-wrap;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}
"""

CHAT_HISTORY_JS = """
() => {
    const welcomeMessage = "Hello! I am your assistant for the LEGO Factory production system.\nHow can I help you today?";
    const itemSelectors = [
        "[data-testid='history-item']",
        "[data-testid*='history-item']",
        ".history-item",
        "[class*='history-item']",
        "[class*='chat-history'] [class*='item']"
    ];

    const chatbotSelectors = [
        "[data-testid='chatbot']",
        "[data-testid*='chatbot']",
        ".gr-chatbot",
        "[class*='chatbot']"
    ];

    const messageSelectors = [
        "[data-testid='chatbot-message']",
        "[data-testid*='message']",
        "[role='log'] > *",
        "[class*='message']"
    ];

    const findHistoryItems = () => {
        for (const selector of itemSelectors) {
            const items = Array.from(document.querySelectorAll(selector));
            if (items.length) return items;
        }
        return [];
    };

    const findChatbot = () => {
        for (const selector of chatbotSelectors) {
            const candidates = Array.from(document.querySelectorAll(selector));
            const chatbot = candidates.find((el) => el instanceof HTMLElement);
            if (chatbot) return chatbot;
        }
        return null;
    };

    const getMessageNodes = (chatbot) => {
        if (!(chatbot instanceof HTMLElement)) return [];
        for (const selector of messageSelectors) {
            const nodes = Array.from(chatbot.querySelectorAll(selector)).filter(
                (el) => el instanceof HTMLElement && !el.classList.contains('chatbot-welcome-message')
            );
            if (nodes.length) return nodes;
        }
        return [];
    };

    const ensureWelcomeMessage = () => {
        const chatbot = findChatbot();
        if (!(chatbot instanceof HTMLElement)) return;

        const existingWelcome = chatbot.querySelector('.chatbot-welcome-message');
        const messages = getMessageNodes(chatbot);

        if (messages.length > 0) {
            if (existingWelcome) existingWelcome.remove();
            return;
        }

        if (existingWelcome) return;

        const logContainer = chatbot.querySelector("[role='log']") || chatbot;
        const welcomeNode = document.createElement('div');
        welcomeNode.className = 'chatbot-welcome-message';
        welcomeNode.setAttribute('data-welcome-message', 'true');
        welcomeNode.textContent = welcomeMessage;
        logContainer.prepend(welcomeNode);
    };

    const clickDeleteAction = (item) => {
        const directDelete = item.querySelector(
            "button[aria-label*='Delete'], button[title*='Delete'], [data-testid*='delete']"
        );
        if (directDelete) {
            directDelete.click();
            return true;
        }

        const moreBtn = item.querySelector(
            "button[aria-label*='More'], button[title*='More'], button[aria-haspopup='menu']"
        );

        if (moreBtn) {
            moreBtn.click();
            setTimeout(() => {
                const menuDelete = document.querySelector(
                    "button[role='menuitem'][aria-label*='Delete'], button[role='menuitem'][title*='Delete'], [role='menuitem'][data-testid*='delete']"
                ) || Array.from(document.querySelectorAll("[role='menuitem'], button")).find(
                    (el) => /delete|remove|trash/i.test((el.textContent || "").trim())
                );
                if (menuDelete) menuDelete.click();
            }, 50);
            return true;
        }

        return false;
    };

    const enhanceHistory = () => {
        const items = findHistoryItems();
        items.forEach((item) => {
            if (!(item instanceof HTMLElement)) return;
            if (item.querySelector('.history-trash-btn')) return;

            const btn = document.createElement('button');
            btn.className = 'history-trash-btn';
            btn.type = 'button';
            btn.title = 'Delete chat';
            btn.setAttribute('aria-label', 'Delete chat');
            btn.textContent = '🗑️';

            btn.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                clickDeleteAction(item);
            });

            item.appendChild(btn);
        });

        ensureWelcomeMessage();
    };

    const observer = new MutationObserver(() => enhanceHistory());
    observer.observe(document.body, { childList: true, subtree: true });
    enhanceHistory();
}
"""

welcome_msg = "Hello! I am your assistant for the LEGO Factory production system.\nHow can I help you today?"

chatbot_description = """Welcome! Make sure you inserted the event log in the "log" folder.<br><br>
**Available Tasks:**<br>
• **Simulation:** Production simulation over time, by piece count, next activity prediction, maintenance scenarios.<br>
Supported simulation KPIs: total pieces produced, mean processing time, mean waiting time, mean transfer time, station-level mean processing times, station-level mean waiting times, total execution time<br>
• **Verification:** Temporal property checking on factory automaton<br>
• **Process Mining:** Process discovery of the Petri net representing the process, conformance checking, performance analysis, log filtering<br>
• **Hybrid Reasoning:** Multi-step workflows combining simulation, verification, and failure analysis<br><br>
*Note: Use actual station names (e.g., station11, station21, station41, ...)*<br><br>
*Always use **seconds** as unit of time.*<br><br>"""

with gr.Blocks(css=CHAT_HISTORY_CSS, js=CHAT_HISTORY_JS, title="LEGO Factory Production System Assistant") as demo:
    gr.ChatInterface(
        handler.process_message,
        chatbot=gr.Chatbot(
            value=[{"role": "assistant", "content": welcome_msg}],
            height=400
        ),
        flagging_mode="manual",
        flagging_options=["Like", "Spam", "Inappropriate", "Other"],
        save_history=True,
        title="LEGO Factory Production System Assistant",
        description=chatbot_description,
    )

demo.queue(default_concurrency_limit=16, max_size=128)

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
                print(f"Please check the log file at 'runtime_logs/chatbot_errors.log' for details.")
                print(f"{'='*60}\n")
                logger.critical("Maximum restart attempts reached. Chatbot terminating.")
                stop_containers()
                sys.exit(1)


if __name__ == "__main__":
    launch_chatbot_with_fallback()