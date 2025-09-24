import requests
import os
import json
import pm4py
from pm4py.objects.bpmn.importer import importer as bpmn_importer

class Extractor:
    def __init__(self, url="http://127.0.0.1:6662/", data = None):
        self.url = "http://127.0.0.1:6662/"
        if data is not None:
            self.data = {
                    "simthreshold": "0.9",
                    "eta": "0.01",
                    "eps": "0.001"
                    }
        else:
            self.data = data
    
    def extract_model(self, xes_path=""):
        files = {"xes_file": open(xes_path, "rb")}
        response = requests.post(self.url, files=files, data=self.data)
        parsed_response = response.json()

        output_dir = parsed_response["result"]["output_directory"]
        local_output_dir = os.path.join(os.path.dirname(__file__), "extractor_outputs", os.path.basename(output_dir.strip("/")), "output_data", "output_file")
        print("Local directory:", local_output_dir)
        files = os.listdir(local_output_dir)
        for file in files:
            if "parameters" in file and "json" in file:
                params_file = file
            if "bpmn" in file:
                bpmn_file = file

        factory_model_path = os.path.join(local_output_dir, params_file)
        bpmn_path = os.path.join(local_output_dir, bpmn_file)
        bpmn_model = bpmn_importer.apply(bpmn_path)

        with open(factory_model_path, "r") as f:
            factory_model = json.load(f)

        return factory_model, bpmn_model
    


if __name__ == "__main__":
    extractor = Extractor()
    xes_path = os.path.join(os.path.dirname(__file__), 'DTLogExtSim', 'log_testing', 'log_test1.xes')
    factory_model, bpmn_model = extractor.extract_model(xes_path)
    net, initial_marking, final_marking = pm4py.convert.convert_to_petri_net(bpmn_model)
    print(factory_model)
    pm4py.view_petri_net(net, initial_marking, final_marking, format="png")