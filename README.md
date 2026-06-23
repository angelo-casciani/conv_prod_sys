# Neuro-Symbolic Conversational AI for Reliable Production Process Intelligence

Source code, datasets, and instructions for the paper "*Neuro-Symbolic Conversational AI for Reliable Production Process Intelligence*".

## About

Advances in Artificial Intelligence (AI) and the growing availability of production data are driving a profound digital transformation in manufacturing, enhancing traceability, monitoring, and analysis across all stages of a production process. Although production process intelligence (PPI) tools support operators in deriving insight-driven decisions from production systems, existing solutions remain fragmented and operate in silos. This forces operators to use multiple interfaces for multi-perspective analysis. Since most tools require specialized expertise and offer limited interoperability, decision-making still relies on manual data handling and output aggregation, increasing errors and inconsistencies.
In this paper, we tackle this issue by presenting a neuro-symbolic conversational AI framework interposing a natural-language interface between users and PPI tools. Our framework: (i) interprets complex natural-language requests, (ii) translates them into machine-readable problems orchestrated across PPI tools, and (iii) generates actionable insights to analyze and optimize process performance. The novelty lies in combining Conversational AI, particularly Large Language Models (LLMs) to handle natural-language ambiguity, with the reasoning capabilities of PPI tools to ensure transparent and reliable decision-making. Building on a reference architecture, we develop a proof-of-concept system integrating LLMs, temporal logics, automated planning, process mining, and simulation, validating it in a lab-scale manufacturing case study.

### Interaction Guide

An interaction guide is also provided in [interaction_guide.pdf](interaction_guide.pdf).

## Quick Start: Docker Chatbot

Use this path if you just want to launch the chatbot as a Dockerized web app.

### 1. Clone the repository

```bash
git clone --recurse-submodules https://github.com/angelo-casciani/conv_prod_sys
cd conv_prod_sys
```

### 2. Create the environment file

Create `.env` in the project root with the credentials used by the chatbot:

```env
GOOGLE_API_KEY=<your Gemini API key>
OPENAI_API_KEY=<optional>
DEEPSEEK_API_KEY=<optional>
UPPAAL_LICENSE_KEY=<your Uppaal license key>
```

`UPPAAL_LICENSE_KEY` is required to build and run the verification container.

### 3. Prepare the repository once

```bash
./setup_submodules.sh
```

This script initializes the submodules, builds Fast Downward, prepares the LSHA environment, and sets up the Docker dependencies used by the chatbot stack.

### 4. Put the event log in the input folder

Place the event log you want to analyze inside `log/`.

### 5. Launch the chatbot container stack

```bash
sudo docker compose up --build
```

Then open: `http://localhost:7860`

### 6. Useful commands

```bash
# Stop everything
sudo docker compose down

# Rebuild and restart
sudo docker compose up --build
```

## Architecture

![architecture](images/architecture.png)

The Figure shows the components of the framework and how they interact.

The framework is designed to provide faithful answers to natural-language requests concerning a production process, i.e., the representation of the activities performed within a production system. It achieves this through the integration of a *Conversational Layer*, a *Reasoning Layer*, and a *Data Layer*. The Conversational Layer tackles the formulation of the problem to be fed to the Reasoning Layer and the interpretation of the results in response to the user. The Reasoning Layer exploits a simulation module working on a digital twin of the production process, a formal verifier reasoning over its automaton, and a process mining component exracting data directly from an event log. The approach assumes the availability of an event log in input, enabling the Data Layer to extract the digital twin and the automaton of the production process via, respectively, a *Digital Twin Extractor* and an *Automata Learning* module.

As illustrated in the Figure, the Conversational Layer includes a set of LLMs: the *Gateway LLM*, which routes the user’s questions, and the *Encoder LLMs* for *Production Simulation*, *Predictive Maintenance*, *Verification* and *Process Mining*, which translate these requests into machine-readable representations compatible with the corresponding reasoners' syntax.

## Structure of the repository

```
.
├── images            # figures for the README file
|   └── architecture.png
├── data              # extracted automaton and simulation parameters
|   ├── automaton     # automaton files (SKG models)
|   |   ├── *_skg.xml            # discovered/selected SKG automaton used for verification
|   |   ├── *.txt                # observable event semantics used for semantic lookup
|   |   └── README.md # automaton directory documentation
|   └── parameters    # digital twin parameters
|       ├── digital_twin_with_failure.json
|       └── digital_twin.json
├── log               # folder where to insert the event log
├── pmmOutputs        # outputs from the Process Mining module
├── runtime_logs      # runtime logs generated by the Dockerized chatbot
├── src               # source code of proposed approach
|   ├── downward      # Fast-Downward submodule code
|   ├── lsha          # LSHA automaton learning submodule (xes_extension branch)
|   ├── DTLogExtSim   # Digital twin extractor code
|   |   └── Extractor # Extractor component
|   ├── uppaal        # UPPAAL verification engine (download separately)
|   |   ├── bin/      # UPPAAL binaries (verifyta, etc.)
|   |   └── res/      # Contains Dockerfile for building image
|   ├── pddl          # PDDL files for orchestration
|   |   ├── domain.pddl    # Orchestrator PDDL domain
|   |   └── problem.pddl   # Orchestrator PDDL problem
|   ├── extractor_outputs  # outputs from the digital twin extractor
|   ├── automaton_learning.py # SKG extraction with LSHA
|   ├── chatbot.py         # GUI-based conversational interface
|   ├── cmd4tests.sh       # commands for testing
|   ├── docker_manager.py  # Docker container lifecycle management
|   ├── main.py            # main entry point for the framework
|   ├── pipeline.py        # orchestration pipeline
|   ├── simulation_interface.py   # LLM-Simulation interface
|   ├── uppaal_interface.py       # UPPAAL verification interface
|   ├── pddl_interface.py         # Planning interface
|   ├── process_mining.py         # Process Mining module
|   ├── failure_interface.py      # failure handling interface
|   ├── failure_maintenance.py    # failure maintenance logic
|   ├── extractor.py              # digital twin extraction logic
|   ├── oracle.py                 # evaluation oracle
|   ├── parse_evaluation_results.py # evaluation results parser script
|   ├── rnd_bas_eval.py           # evaluation with rng and LLM-only baselines 
|   ├── simulation.py             # simulation implementation
|   ├── test_sets_generation.py   # test set generation script
|   ├── prompts.json              # LLM prompts configuration
|   └── utility.py                # utility functions
├── tests             # sources for the evaluation
|   ├── outputs       # outputs of the live convesations
|   ├── test_sets     # test sets employed during the evaluation
|   |   ├── factory_info.csv
|   |   ├── hybrid.csv
|   |   ├── process_mining.csv
|   |   ├── qualitative_hybrid_requests.txt
|   |   ├── routing.csv
|   |   ├── simulation.csv
|   |   ├── simulation_stats.txt
|   |   ├── unrelated.csv
|   |   └── verification.csv
|   └── evaluation    # quantitative evaluation results for each run
├── docker-compose.yml       # Local Docker compose configuration
├── Dockerfile               # Chatbot container build
├── Dockerfile.uppaal        # UPPAAL engine standalone build
├── requirements.txt         # Core Python dependencies
├── setup_submodules.sh      # Script to initialize submodules
├── .env                     # environment variables (API keys)
├── .gitmodules              # git submodules configuration
├── LICENSE                  # license information
└── README.md                # This file
```

## Setup

## LLM Configuration

This software supports both open-weight (using [Ollama](https://ollama.com/)) and proprietary language models (via API).

**Local Models:**
- Install and run [Ollama](https://github.com/ollama/ollama)
- Pull the models you plan to use

**API-based Models:**
- Obtain API keys for your chosen provider (e.g., OpenAI, Gemini, DeepSeek)
- Add credentials to the `.env` file

**Hardware Requirements:**
- GPU access is recommended for better performance
- Verify your system meets the minimum GPU requirements for your selected models


### Docker-first usage

For most users, the Docker workflow above is enough. You do not need to create a local Python environment just to run the chatbot web interface.

### Local Python environments

Use local Python environments if you want to run the CLI, evaluations, or development workflows outside Docker. Note that the Web GUI is only supported via the Docker flow.

**Requires Python 3.11 or higher and system dependencies.**

First, ensure you have the required system dependencies installed for Graphviz:

```bash
sudo apt-get update
sudo apt-get install graphviz graphviz-dev xdg-utils
```

Then create and activate your environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Finally, set up the submodules and Docker components:

```bash
./setup_submodules.sh
```

### Server deployment

For a remote-server deployment, see [server/README.md](server/README.md).

## Supported Interfaces

### CLI Interface

This is optional. It is not required for the Dockerized chatbot launch.

Start the conversational framework and interact with it through the command line:

```bash
source .venv/bin/activate
python src/main.py
```

The complete conversation will be stored in a `.txt` file in the [outputs](tests/outputs) folder.

The default parameters for `main.py` and `chatbot.py` are:

* Gateway LLM: `'gemma4:latest'` (`main.py`) and `'gemini-3.1-flash-lite'` (`chatbot.py`);
* Simulation LLM: `'gemma4:latest'` (`main.py`) and `'gemini-3.1-flash-lite'` (`chatbot.py`);
* Verification LLM: `'gemma4:latest'` (`main.py`) and `'gemini-3.1-flash-lite'` (`chatbot.py`);
* Number of generated tokens: `32768`;
* Interaction Modality: `'live'`, i.e., the live chat with the conversational framework.;
* Extracted model: `False`, i.e., the digital twin for simulation will be extracted from scratch;
* Extracted model with failure data: `False`, i.e., the digital twin for predictive maintenance will be extracted from scratch.

To customize these settings, modify the corresponding arguments when executing `main.py`:

* Use `--llm_id_gateway` to specify a different Gateway LLM (e.g., among the ones reported in the *LLMs Requirements* section).
* Use `--llm_id_simulation` to specify a different Encoder LLM for Simulation (e.g., among the ones reported in the *LLMs Requirements* section).
* Use `--llm_id_verification` to specify a different Encoder LLM for Verification (e.g., among the ones reported in the *LLMs Requirements* section).
* Adjust `--max_new_tokens` to change the number of generated tokens.
* Set `--modality` to alter the interaction modality (i.e., `'live'`, `'evaluation-simulation'`, '`evaluation-verification`', `'evaluation-factory_info`', `'evaluation-process_mining`', `'evaluation-hybrid`', '`evaluation-routing`' and '`evaluation-qualitative-hybrid`').
* Use `--extracted_model` to specify if the model has already been extracted (True or False).
* Use `--extracted_model_failure` to specify if the model with failure data has already been extracted (True or False).

A comprehensive list of commands can be found in `src/cmd4tests.sh`.

### Web GUI

The recommended way to use the chatbot is the Docker flow described in [Quick Start: Docker Chatbot](#quick-start-docker-chatbot).

Once started, the Web GUI will be accessible in your browser at: `http://127.0.0.1:7860/`

### Experimental Evaluation

Instructions to reproduce the experimental evaluation results are reported in [src/README.md](src/README.md).

## License

Distributed under the GNU GPL License. See [LICENSE](LICENSE) for more information.