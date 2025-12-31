#!/bin/bash

############################## Live ##############################
# python3 main.py

################### Evaluation for Simulation ####################
# Local models
python3 main.py --llm_id_simulation meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.1-8B-Instruct --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.2-1B-Instruct --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.2-3B-Instruct --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Ministral-8B-Instruct-2410 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation Qwen/Qwen2.5-7B-Instruct --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation google/gemma-2-9b-it --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation microsoft/phi-4 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_simulation gpt-4o-mini --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4o --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4.1-mini --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4.1 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5.1 --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5-mini --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5-nano --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-2.5-pro --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-2.5-flash --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-3-flash-preview --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-3-pro-preview --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-chat --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-reasoner --modality evaluation-simulation --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True


################# Evaluation for Verification ###################
# Local models
python3 main.py --llm_id_verification meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.1-8B-Instruct --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.2-1B-Instruct --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.2-3B-Instruct --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Ministral-8B-Instruct-2410 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification Qwen/Qwen2.5-7B-Instruct --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification google/gemma-2-9b-it --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification microsoft/phi-4 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_verification gpt-4o-mini --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4o --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4.1-mini --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4.1 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5.1 --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5-mini --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5-nano --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-2.5-pro --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-2.5-flash --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-3-flash-preview --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-3-pro-preview --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-chat --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-reasoner --modality evaluation-verification --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

#################### Evaluation for Routing #####################
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-routing --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

################## Evaluation for Factory Info ###################
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-factory_info --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

################ Evaluation for Process Mining ##################
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-process_mining --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

################### Evaluation for Hybrid ######################
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-hybrid --max_new_tokens 8192 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-hybrid --max_new_tokens 8192 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-hybrid --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

############# Evaluation for Simulation - ZeroShot ##############
# Local models
python3 main.py --llm_id_simulation meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.1-8B-Instruct --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.2-1B-Instruct --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation meta-llama/Llama-3.2-3B-Instruct --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation mistralai/Ministral-8B-Instruct-2410 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation Qwen/Qwen2.5-7B-Instruct --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation google/gemma-2-9b-it --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation microsoft/phi-4 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_simulation gpt-4o-mini --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4o --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4.1-mini --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-4.1 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5.1 --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5-mini --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gpt-5-nano --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-2.5-pro --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-2.5-flash --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-3-flash-preview --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation gemini-3-pro-preview --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-chat --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_simulation deepseek-reasoner --modality evaluation-simulation-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

############# Evaluation for Verification - ZeroShot ############
# Local models
python3 main.py --llm_id_verification meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.1-8B-Instruct --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.2-1B-Instruct --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification meta-llama/Llama-3.2-3B-Instruct --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification mistralai/Ministral-8B-Instruct-2410 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification Qwen/Qwen2.5-7B-Instruct --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification google/gemma-2-9b-it --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification microsoft/phi-4 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_verification gpt-4o-mini --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4o --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4.1-mini --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-4.1 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5.1 --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5-mini --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gpt-5-nano --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-2.5-pro --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-2.5-flash --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-3-flash-preview --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification gemini-3-pro-preview --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-chat --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_verification deepseek-reasoner --modality evaluation-verification-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

############### Evaluation for Routing - ZeroShot ###############
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-routing-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

############# Evaluation for Factory Info - ZeroShot ############
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-factory_info-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

############ Evaluation for Process Mining - ZeroShot ###########
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-process_mining-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True

############### Evaluation for Hybrid - ZeroShot ################
# Local models
python3 main.py --llm_id_gateway meta-llama/Meta-Llama-3-8B-Instruct --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.1-8B-Instruct --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-1B-Instruct --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway meta-llama/Llama-3.2-3B-Instruct --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.2 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-7B-Instruct-v0.3 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Mistral-Nemo-Instruct-2407 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway mistralai/Ministral-8B-Instruct-2410 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen2.5-7B-Instruct --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway Qwen/Qwen3-30B-A3B-Instruct-2507 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway google/gemma-2-9b-it --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway microsoft/phi-4 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-ai/DeepSeek-R1-Distill-Llama-8B --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
# API models
python3 main.py --llm_id_gateway gpt-4o-mini --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4o --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1-mini --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-4.1 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5.1 --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-mini --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gpt-5-nano --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-pro --modality evaluation-hybrid-zeroshot --max_new_tokens 8192 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-2.5-flash --modality evaluation-hybrid-zeroshot --max_new_tokens 8192 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-flash-preview --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway gemini-3-pro-preview --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-chat --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
python3 main.py --llm_id_gateway deepseek-reasoner --modality evaluation-hybrid-zeroshot --max_new_tokens 1024 --extracted_model True  --extracted_model_failure True
