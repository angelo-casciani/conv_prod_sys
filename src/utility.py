import csv
import json
import os
import re

import random
import argparse
import numpy as np

try: # (Optional) torch import (not needed for API-only mode)
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def seed_everything(seed=10):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def load_csv_questions(filename):
    filepath = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', filename)
    questions = []
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            question, answer, test_type = row
            questions.append([question, answer, test_type])
        return questions


def log_to_file(conversation, curr_datetime, info_run):
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, "..", "tests", 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"output_{curr_datetime}.txt")
    with open(filepath, 'a') as file:
        file.write('INFORMATION ON THE RUN\n\n')
        for key in info_run.keys():
            file.write(f"{key}: {info_run[key]}\n")
        file.write('\n-----------------------------------\n\n')
        file.write(conversation)


def extract_json(llm_answer):
    json_match = re.search(r'\{.*\}', llm_answer, re.DOTALL)
    json_str = ''
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return json_str


def retrieve_automata():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'automaton', 'factory_automaton.json')
    with open(model_path, 'r') as file:
        data = json.load(file)
    
    return data


def retrieve_factory():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'parameters', 'digital_twin.json')
    with open(model_path, 'r') as file:
        data = json.load(file)
    
    return data

def retrieve_factory_with_failure():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'parameters', 'digital_twin_with_failure.json')
    with open(model_path, 'r') as file:
        data = json.load(file)
        
    return data

def load_txt_questions(filename):
    questions = []
    full_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', filename)
    
    with open(full_path, 'r', encoding='utf-8') as f:
        for line in f:
            cleaned_line = line.replace('<s>', '').replace('</s>', '').strip()
            
            if cleaned_line:
                questions.append(cleaned_line)
                
    return questions