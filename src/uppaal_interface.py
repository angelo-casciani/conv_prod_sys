import os
import subprocess
import logging
from pathlib import Path
from utility import extract_json
from docker_manager import get_docker_command

logger = logging.getLogger(__name__)

DOCKER_CONTAINER_NAME = "uppaal-engine"

def get_skg_model_path():
    """
    Find the SKG model file in data/automaton directory.
    Returns the local path and the container path.
    """
    automaton_dir = Path(__file__).parent.parent / 'data' / 'automaton'
    
    # Look for XML files in the automaton directory (excluding README)
    xml_files = [f for f in automaton_dir.glob('*.xml') if f.name.lower() != 'readme.xml']
    
    if not xml_files:
        # Fallback to default path if no file found
        return (
            os.path.join(os.path.dirname(__file__), '..', 'data', 'automaton', 'lego_SKG_item-10_no_doubles.xml'),
            '/home/uppaal/models/lego_SKG_item-10_no_doubles.xml'
        )
    
    # Use the most recently modified XML file
    latest_xml = max(xml_files, key=lambda p: p.stat().st_mtime)
    
    model_path = str(latest_xml)
    model_path_in_container = f'/home/uppaal/models/{latest_xml.name}'
    
    return model_path, model_path_in_container

# Get the model paths dynamically
MODEL_PATH, MODEL_PATH_IN_CONTAINER = get_skg_model_path()

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
        # Get current model paths (in case they changed)
        model_path, model_path_in_container = get_skg_model_path()
        
        # Check if model file exists
        if not os.path.exists(model_path):
            return f"Error: Model file not found: {model_path}"
        
        logger.info(f"Using SKG model: {os.path.basename(model_path)}")
        logger.info(f"Container path: {model_path_in_container}")
        
        docker_cmd = get_docker_command()
        if not docker_cmd:
            return "Error: UPPAAL verification not available (Docker not found in container environment)"
        
        exec_cmd = docker_cmd + [
            'exec', '-i',
            DOCKER_CONTAINER_NAME,
            'bash', '-c',
            f'echo "{query}" > /tmp/query.q && verifyta {model_path_in_container} /tmp/query.q'
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