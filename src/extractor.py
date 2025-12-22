import requests
import os
import json
import pm4py
import ast
import re
from pm4py.objects.bpmn.importer import importer as bpmn_importer
import random

class Extractor:
    def __init__(self, url="http://127.0.0.1:6662/", data = None):
        self.url = url
        if data is not None:
            self.data = {
                    "simthreshold": "0.9",
                    "eta": "0.01",
                    "eps": "0.001"
                    }
        else:
            self.data = data

    def extract_parameters(self, params_path):
        with open(params_path, "r") as f:
            params = json.load(f)
        activities = {}
        for element in params['elements']:
            activities[element['elementId']] = element['durationDistribution']
        return activities
    
    def extract_inter_arrival(self, inter_arrival_path):
        with open(inter_arrival_path, "r") as f:
            lines = f.readlines()

        for line in lines:
            if line.strip().startswith("["):
                vector = ast.literal_eval(line.strip())
                break
        inter_arrival_time = {"type": vector[0], "mean": vector[1]['mean'], "arg1": vector[1]['arg1'], "arg2": vector[1]['arg2']}

        return inter_arrival_time
    
    def extract_branch_prob(self, branch_prob_path):
        with open(branch_prob_path, "r") as f:
            lines = f.readlines()
        
        for line in lines:
            if line.strip().startswith("{"):
                # Match any unquoted key (word chars, hyphens, @) before a colon
                quoted_line = re.sub(r'\{([^{\'"][\w\-@]+):', r'{"\1":', line.strip())
                quoted_line = re.sub(r',\s*([^{\'"][\w\-@]+):', r', "\1":', quoted_line)
                data = eval(quoted_line)
                break
        
        next_activities = {}
        for gateway, flows in data.items():
            for flow in flows:
                src = list(flow["source"])[0]       # e.g. 'A1'
                dst = list(flow["destination"])[0]  # e.g. 'A2'
                prob = flow["total_probability"]

                if src not in next_activities:
                    next_activities[src] = {}
                
                #if destination already exists we sum the probability
                if dst in next_activities[src]:
                    next_activities[src][dst]["probability"] += prob
                else:
                    next_activities[src][dst] = {"probability": prob}

        return next_activities
    
    def get_real_successors(self, t, visited=None):
        if visited is None:
            visited = set()

        successors = set()
        if t in visited:
            return successors
        visited.add(t)

        for arc in t.out_arcs:
            place = arc.target
            for arc2 in place.out_arcs:
                next_t = arc2.target
                if next_t.label is None:
                    #recursive call
                    successors |= self.get_real_successors(next_t, visited)
                else:
                    successors.add(next_t.label)

        return successors

    def extract_successors_from_petri(self, net):
        successors = {}
        for t in net.transitions:
            if t.label is None:
                continue  # skip
            act = t.label
            successors[act] = self.get_real_successors(t)
        return successors
    
    def extract_transfer_times(self, transfer_times_path):
        with open(transfer_times_path, "r") as f:
            lines = f.readlines()
        
        transfer_times = {}
        for line in lines:
            line = ast.literal_eval(line.strip())
            transfer_times[line[0]] = {"type": line[1], "mean": line[2]['mean'], "arg1": line[2]['arg1'], "arg2": line[2]['arg2']}
        
        return transfer_times
    
    def create_model(self, activities, inter_arrival_time, branch_prob, transfer_times):
        model = {}

        model["inter_arrival_time"] = inter_arrival_time

        model["activities"] = {}
        for activity_id, activity_data in activities.items():
            model["activities"][activity_id] = {
                "capacity": 1, 
                "processing_time": activity_data,
                "next_activities": {}
            }

            if activity_id in branch_prob:
                for next_activity, prob_data in branch_prob[activity_id].items():
                    model["activities"][activity_id]["next_activities"][next_activity] = {
                        "probability": prob_data["probability"]
                    }
            
        model["transfer_times"] = {}
        for source_activity, transfer_data in transfer_times.items():
            model["transfer_times"][source_activity] = {}
            
            if source_activity in branch_prob:
                for destination in branch_prob[source_activity].keys():
                    model["transfer_times"][source_activity][destination] = transfer_data
        return model
    
    def add_failure_params(self, model, seed=None):
        if seed is not None:
            random.seed(seed)

        for activity_id in model['activities'].keys():
            failure_rate = round(random.uniform(0.001, 0.010), 3)

            repair_mean = round(random.uniform(15,35), 1)
            repair_std = round(random.uniform(2,7), 1)

            degradation_factor = round(random.uniform(0.0003, 0.0012), 4)

            model['activities'][activity_id]['failure_parameters'] = {
                "failure_rate": failure_rate,
                "repair_time": {
                    "mean": repair_mean,
                    "std": repair_std
                },
                "degradation_factor": degradation_factor
            }

        return model
    
    def extract_model(self, xes_path="", failure=False):
        files = {"xes_file": open(xes_path, "rb")}
        response = requests.post(self.url, files=files, data=self.data)
        parsed_response = response.json()

        output_dir = parsed_response["result"]["output_directory"]
        local_output_dir = os.path.join(os.path.dirname(__file__), "extractor_outputs", os.path.basename(output_dir.strip("/")), "output_data", "output_file")
        #print("Local directory:", local_output_dir)
        files = os.listdir(local_output_dir)
        for file in files:
            if "parameters" in file and "txt" in file:
                params_file = file
            if "interarrival" in file:
                inter_arrival_file = file
            if "branch_prob" in file:
                branch_prob_file = file
            if "act_distr_wait_time" in file:
                transfer_times_file = file
            if "bpmn" in file:
                bpmn_file = file
            

        params_path = os.path.join(local_output_dir, params_file)
        inter_arrival_path = os.path.join(local_output_dir, inter_arrival_file)
        branch_prob_path = os.path.join(local_output_dir, branch_prob_file)
        transfer_times_path = os.path.join(local_output_dir, transfer_times_file)
        bpmn_path = os.path.join(local_output_dir, bpmn_file)
        bpmn_model = bpmn_importer.apply(bpmn_path)
        net, initial_marking, final_marking = pm4py.convert.convert_to_petri_net(bpmn_model)

        #ACTIVITIES IDs EXTRACTION
        activities = self.extract_parameters(params_path)
        
        #INTER ARRIVAL TIME EXTRACTION
        inter_arrival_time = self.extract_inter_arrival(inter_arrival_path)
        
        #BRANCH PROBABILITIES EXTRACTION
        branch_prob = self.extract_branch_prob(branch_prob_path)
        successors = self.extract_successors_from_petri(net)
        for act, succs in successors.items():
            if act not in branch_prob:
                branch_prob[act] = {}
                if len(succs) == 1:
                    only_succ = list(succs)[0]
                    branch_prob[act][only_succ] = {"probability": 1.0}
        
        #TRANSFER TIMES EXTRACTION
        transfer_times = self.extract_transfer_times(transfer_times_path)
            
        model = self.create_model(activities, inter_arrival_time, branch_prob, transfer_times)

        if failure:
            output_dir = "../data/parameters/digital_twin_with_failure.json"
            model = self.add_failure_params(model)
        else:
            output_dir = "../data/parameters/digital_twin.json"

        with open(output_dir, "w") as f:
            json.dump(model, f, indent=2)

        return net, initial_marking, final_marking


if __name__ == "__main__":
    extractor = Extractor()
    xes_path = os.path.join(os.path.dirname(__file__), 'DTLogExtSim', 'log_testing', 'log_test2.xes')
    net, initial_marking, final_marking = extractor.extract_model(xes_path, failure=True)
    pm4py.view_petri_net(net, initial_marking, final_marking, format="png")