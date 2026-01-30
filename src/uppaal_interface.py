import os
import subprocess
from utility import extract_json
from docker_manager import get_docker_command

DOCKER_CONTAINER_NAME = "uppaal-engine"
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'automaton', 'lego_SKG_item-10_no_doubles.xml')
MODEL_PATH_IN_CONTAINER = "/home/uppaal/models/lego_SKG_item-10_no_doubles.xml"

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
    try:
        docker_cmd = get_docker_command()
        if not docker_cmd:
            return "Error: UPPAAL verification not available (Docker not found in container environment)"
        
        exec_cmd = docker_cmd + [
            'exec', '-i',
            DOCKER_CONTAINER_NAME,
            'bash', '-c',
            f'echo "{query}" > /tmp/query.q && verifyta {MODEL_PATH_IN_CONTAINER} /tmp/query.q'
        ]
        process = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        result = format_uppaal_output(stdout)

        return f"Result: {result}\nErrors: {stderr}"
    
    except Exception as e:
        return f"Error executing query: {str(e)}"

def format_uppaal_output(uppaal_answer):
    delimiter = 'Verifying formula'
    index = uppaal_answer.find(delimiter)
    return uppaal_answer[index:]  

"""QUERIES = ["A<> s.q_1", "E<> s.q_1", "s.q_0 --> s.q_6"]
for query in QUERIES:
    print(execute_query(query))"""

if __name__ == "__main__":
    query="A<> s.q_1"
    print(f"Testing query: {query}")
    result = execute_query(query)
    print(result)