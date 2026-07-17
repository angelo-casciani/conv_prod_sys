import csv
import json
import os
import re

import random
import argparse
import numpy as np
from threading import Lock




_log_file_lock = Lock()


def seed_everything(seed=10):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)



def get_repo_root():
    return os.path.join(os.path.dirname(__file__), '..')


def get_runtime_log_dir():
    default_dir = '/app/runtime_logs' if os.path.exists('/app') else os.path.join(get_repo_root(), 'runtime_logs')
    log_dir = os.getenv('APP_LOG_DIR', default_dir)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def get_interaction_log_dir():
    default_dir = os.path.join(get_runtime_log_dir(), 'interactions')
    interaction_dir = os.getenv('INTERACTION_LOG_DIR', default_dir)
    os.makedirs(interaction_dir, exist_ok=True)
    return interaction_dir


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
    with _log_file_lock:
        with open(filepath, 'a', encoding='utf-8') as file:
            file.write('INFORMATION ON THE RUN\n\n')
            for key in info_run.keys():
                file.write(f"{key}: {info_run[key]}\n")
            file.write('\n-----------------------------------\n\n')
            file.write(conversation)


_MARKDOWN_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)
_LOOSE_JSON_RE = re.compile(r'(\{.*?\})', re.DOTALL)


def extract_markdown_json_block(text):
    """Return the raw text captured inside a ```json ... ``` fenced block, or None."""
    match = _MARKDOWN_JSON_BLOCK_RE.search(text)
    return match.group(1) if match else None


def extract_outer_braces(text):
    """Return the substring spanning the first '{' to the last '}' in text, or None."""
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return None


def extract_loose_json(text):
    """Return the first non-greedy '{...}' match, or None."""
    match = _LOOSE_JSON_RE.search(text)
    return match.group(0) if match else None


def extract_balanced_json_objects(text, required_substring=None):
    """Return all top-level, brace-balanced '{...}' substrings in text (string-aware),
    optionally keeping only those containing required_substring."""
    json_objects = []
    i = 0
    while i < len(text):
        if text[i] == '{':
            brace_count = 0
            start = i
            in_string = False
            escape = False

            for j in range(i, len(text)):
                char = text[j]

                if escape:
                    escape = False
                    continue
                if char == '\\':
                    escape = True
                    continue

                if char == '"':
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = text[start:j + 1]
                            if required_substring is None or required_substring in json_str:
                                json_objects.append(json_str)
                            i = j
                            break
            i += 1
        else:
            i += 1

    return json_objects


def extract_json(llm_answer):
    json_str = extract_outer_braces(llm_answer) or ''
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return json_str


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