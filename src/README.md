# Experiments

Instructions to reproduce the experimental evaluation.

## Simulation experiments

To reproduce the experiments for the *simulation* evaluation, for example:

``` bash
python src/main.py --llm_id_simulation Qwen/Qwen2.5-7B-Instruct --modality evaluation-simulation --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## Verification experiments

To reproduce the experiments for the *verification* evaluation, for example:

``` bash
python src/main.py --llm_id_verification gpt-4o-mini --modality evaluation-verification --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## Factory info experiments

To reproduce the experiments for the *factory\_info* evaluation, for example:

``` bash
python src/main.py --llm_id_gateway gemini-2.0-flash --modality evaluation-factory_info --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## Process mining experiments

To reproduce the experiments for the *process\_mining* evaluation, for example:

``` bash
python src/main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-process_mining --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## Hybrid experiments

To reproduce the experiments for the *hybrid* evaluation, for example:

``` bash
python src/main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-hybrid --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## Routing experiments

To reproduce the experiments for the *routing* evaluation, for example:

``` bash
python src/main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-routing --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## Qualitative Hybrid experiments

To reproduce the experiments for the *hybrid* qualitative evaluation, for example:

``` bash
python src/main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-qualitative-hybrid --max_new_tokens 512
```

The results will be stored in a `.txt` file reporting all the information for the run and the corresponding results in the [evaluation](tests/evaluation) folder.

## RNG and LLM-Only Baselines experiments
We provide baseline comparisons for the simulation and verification tasks using `answers-dataset.csv`to motivate our approach, which leverages PPI tools in the backend to produce faithful answers.

``` bash
python src/rnd_bas_eval.py
```

The random baseline samples answers uniformly between the minimum and maximum values in the ground-truth dataset for simulation, and samples a boolean value uniformly for verification. The LLM baseline uses only the event log (in the [log](log) folder) as input. By default, it uses the `gemini-2.5-flash` model (requiring a Google API key), but you can change the model inside the script.

## Generation of New Test Sets

To generate new test sets for the three supported evaluation, run the script `test_sets_generation.py` before running an evaluation.

``` bash
python src/test_sets_generation.py
```