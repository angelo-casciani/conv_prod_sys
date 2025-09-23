import requests
import os 
import process_mining
import json

#pmm = process_mining.ProcessMiningModule(os.path.join(os.path.dirname(__file__), '..', '10-Minute Sample.csv'))
xes_path = os.path.join(os.path.dirname(__file__), 'DTLogExtSim', 'log_testing', 'log_test1.xes')
url = "http://127.0.0.1:6662/"
files = {"xes_file": open(xes_path, "rb")}
data = {
    "simthreshold": "0.9",
    "eta": "0.01",
    "eps": "0.001"
}

response = requests.post(url, files=files, data=data)
parsed_response = response.json()

output_dir = parsed_response["result"]["output_directory"]
local_output_dir = os.path.join(os.path.dirname(__file__), "extractor_outputs", os.path.basename(output_dir.strip("/")), "output_data", "output_file")
print("Local directory:", local_output_dir)
files = os.listdir(local_output_dir)
for file in files:
    if "parameters" in file and "json" in file:
        params_file = file

factory_model_path = os.path.join(local_output_dir, params_file)

with open(factory_model_path, "r") as f:
    factory_model = json.load(f)
print(factory_model)