import os
import subprocess
import tempfile
from utility import extract_json


UPPAAL_PATH = os.path.join(os.path.dirname(__file__), 'uppaal', 'lib', 'app', 'bin', 'verifyta')
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'lego_SKG_item-10_no_doubles.xml')


def interface_with_llm(llm_answer):
    json_request = extract_json(llm_answer)
    task = json_request.get("task")
    formal_query = json_request.get("uppaal_query")
    uppaal_output = ''

    if task == "verification":
        uppaal_output = execute_query(formal_query)
    
    json_request["results"] = uppaal_output
    return json_request


def execute_query(query):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_query_file:
        temp_query_file.write(query)          # Temporary file to store the query for Uppaal
        temp_query_file.flush()
        process = subprocess.Popen([UPPAAL_PATH, MODEL_PATH, temp_query_file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        result = format_uppaal_output(stdout)
        return f"Result: {result}\nErrors: {stderr}"


def format_uppaal_output(uppaal_answer):
    delimiter = 'Verifying formula'
    index = uppaal_answer.find(delimiter)
    return uppaal_answer[index:]  



"""QUERIES = ["A<> s.q_1", "E<> s.q_1", "s.q_0 --> s.q_6"]
for query in QUERIES:
    print(execute_query(query))"""