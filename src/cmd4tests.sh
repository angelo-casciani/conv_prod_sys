#!/bin/bash

############################## Live ##############################
python3 main.py

################### Evaluation for Simulation ####################
python3 main.py --llm_id_simulation meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.1-8B-Instruct --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.2-1B-Instruct --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.2-3B-Instruct --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Ministral-8B-Instruct-2410 --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation Qwen/Qwen2.5-7B-Instruct --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation google/gemma-2-9b-it --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4o-mini --modality evaluation-simulation --max_new_tokens 512 --extracted_model True  --extracted_model_failure True

################# Evaluation for Verification ###################
python3 main.py --llm_id_verification meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.1-8B-Instruct --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.2-1B-Instruct --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.2-3B-Instruct --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Ministral-8B-Instruct-2410 --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification Qwen/Qwen2.5-7B-Instruct --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification google/gemma-2-9b-it --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4o-mini --modality evaluation-verification --max_new_tokens 512 --extracted_model True  --extracted_model_failure True

#################### Evaluation for Routing #####################
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-routing --max_new_tokens 512 --extracted_model True  --extracted_model_failure True

################## Evaluation for Factory Info ###################
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-factory_info --max_new_tokens 512 --extracted_model True  --extracted_model_failure True

################ Evaluation for Process Mining ##################
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-process_mining --max_new_tokens 512 --extracted_model True  --extracted_model_failure True

################### Evaluation for Hybrid ######################
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-hybrid --max_new_tokens 512 --extracted_model True  --extracted_model_failure True
