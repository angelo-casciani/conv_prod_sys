import requests
import os
import json
import pm4py
import ast
import re
from pm4py.objects.bpmn.importer import importer as bpmn_importer
import random
from automaton_learning import AutomatonLearner

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
        
        # Initialize automaton learner for SKG extraction
        try:
            self.automaton_learner = AutomatonLearner()
        except FileNotFoundError:
            print("Warning: LSHA not found. SKG extraction will be skipped.")
            self.automaton_learner = None

    def extract_parameters(self, params_path):
        with open(params_path, "r") as f:
            params = json.load(f)
        activities = {}

        if 'elements' in params:
            elements = params['elements']
        elif '0' in params and 'elements' in params['0']:
            elements = params['0']['elements']
        else:
            raise KeyError(f"Cannot find 'elements' in parameters file. Available top-level keys: {list(params.keys())}")
        
        for element in elements:
            activities[element['elementId']] = element['durationDistribution']
        return activities
    
    def extract_inter_arrival(self, inter_arrival_path):
        with open(inter_arrival_path, "r") as f:
            content = f.read().strip()
            
            if inter_arrival_path.endswith('.json'):
                vector = json.loads(content)
            else:
                for line in content.split('\n'):
                    if line.strip().startswith("["):
                        vector = ast.literal_eval(line.strip())
                        break
        
        inter_arrival_time = {"type": vector[0], "mean": vector[1]['mean'], "arg1": vector[1]['arg1'], "arg2": vector[1]['arg2']}
        return inter_arrival_time
    
    def extract_branch_prob(self, branch_prob_path):
        with open(branch_prob_path, "r") as f:
            content = f.read().strip()
        
        if branch_prob_path.endswith('.json'):
            data = json.loads(content)
        else:
            for line in content.split('\n'):
                if line.strip().startswith("{"):
                    quoted_line = re.sub(r'\{([^{\'"][\w\-@]+):', r'{"\1":', line.strip())
                    quoted_line = re.sub(r',\s*([^{\'"][\w\-@]+):', r', "\1":', quoted_line)
                    data = eval(quoted_line)
                    break
        
        next_activities = {}
        node_to_label = {}
        for gateway, flows in data.items():
            node_uuid = gateway.rstrip('@') # extract node UUID from gateway key
            
            for flow in flows:
                src = list(flow["source"])[0]       # e.g. 'station11'
                dst = list(flow["destination"])[0]  # e.g. 'station21'
                prob = flow["total_probability"]
                
                if node_uuid and src: # map node UUID to its label
                    node_to_label[node_uuid] = src

                if src not in next_activities:
                    next_activities[src] = {}
                
                if dst in next_activities[src]: # if destination already exists, we sum the probability
                    next_activities[src][dst]["probability"] += prob
                else:
                    next_activities[src][dst] = {"probability": prob}
        self.node_to_label_from_branch = node_to_label

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
    
    def extract_label_to_id_mapping(self, bpmn_model):
        label_to_id = {}
        id_to_label = {}
        
        for node in bpmn_model.get_nodes():
            if hasattr(node, 'get_name') and hasattr(node, 'get_id'):
                label = node.get_name()  # e.g., 'A1', 'A2'
                node_id = node.get_id()  # e.g., 'node_17a40054-...' or 'idnode_...'
                # Normalize node IDs: remove 'id' prefix if present
                if node_id.startswith('idnode_'):
                    node_id = node_id[2:]  # Remove 'id' prefix to get 'node_...'
                
                if label and node_id:
                    label_to_id[label] = node_id
                    id_to_label[node_id] = label
        
        return label_to_id, id_to_label
    
    def extract_transfer_times(self, transfer_times_path):
        with open(transfer_times_path, "r") as f:
            content = f.read().strip()
        
        transfer_times = {}
        
        if transfer_times_path.endswith('.json'):
            data = json.loads(content)
            if not data:     # If empty JSON object, return empty dict
                return transfer_times
            
            for key, value in data.items():
                if isinstance(value, dict):
                    transfer_times[key] = {
                        "type": value.get("type", ""),
                        "mean": value.get("mean", 0),
                        "arg1": value.get("arg1", 0),
                        "arg2": value.get("arg2", 0)
                    }
        else:
            # Old text format
            lines = f.readlines() if hasattr(f, 'readlines') else content.split('\n')
            for line in lines:
                if line.strip():
                    line_data = ast.literal_eval(line.strip())
                    transfer_times[line_data[0]] = {
                        "type": line_data[1],
                        "mean": line_data[2]['mean'],
                        "arg1": line_data[2]['arg1'],
                        "arg2": line_data[2]['arg2']
                    }
        
        return transfer_times
    
    def rebalance_zero_probabilities(self, branch_prob, min_prob=0.1):
        for source_activity, destinations in branch_prob.items():
            zero_probs = []
            nonzero_probs = []
            
            for dest, prob_data in destinations.items():
                prob = prob_data.get("probability", 0.0)
                if prob == 0.0:
                    zero_probs.append(dest)
                else:
                    nonzero_probs.append(dest)
            
            if zero_probs and nonzero_probs:
                num_zeros = len(zero_probs)
                total_to_subtract = num_zeros * min_prob
                current_nonzero_sum = sum(destinations[dest]["probability"] for dest in nonzero_probs)
                
                if current_nonzero_sum > total_to_subtract:
                    # Assign min_prob to zero probabilities
                    for dest in zero_probs:
                        destinations[dest]["probability"] = min_prob
                    
                    remaining_prob = 1.0 - total_to_subtract
                    for dest in nonzero_probs:
                        original_prob = destinations[dest]["probability"]
                        new_prob = (original_prob / current_nonzero_sum) * remaining_prob
                        destinations[dest]["probability"] = round(new_prob, 2)
                    
                    total = sum(destinations[dest]["probability"] for dest in destinations.keys())
                    if abs(total - 1.0) > 0.001:
                        max_dest = max(nonzero_probs, key=lambda d: destinations[d]["probability"])
                        destinations[max_dest]["probability"] = round(
                            destinations[max_dest]["probability"] + (1.0 - total), 2
                        )
        
        return branch_prob
    
    def generate_random_transfer_times(self, branch_prob, seed=42):
        random.seed(seed)
        transfer_times = {}
        
        for source_activity in branch_prob.keys():
            mean_transfer = round(random.uniform(2.0, 5.0), 2)
            std_transfer = round(random.uniform(0.3, 1.0), 2)
            
            transfer_times[source_activity] = {
                "type": "normal",
                "mean": mean_transfer,
                "arg1": std_transfer,
                "arg2": 0
            }
        
        return transfer_times
    
    def create_model(self, activities, inter_arrival_time, branch_prob, transfer_times, id_to_label, label_to_id):
        model = {}

        model["inter_arrival_time"] = inter_arrival_time

        model["activities"] = {}
        # convert UUID-keyed activities into label-keyed activities
        for activity_id, activity_data in activities.items():
            normalized_id = activity_id[2:] if activity_id.startswith('idnode_') else activity_id
            activity_label = getattr(self, 'node_to_label_from_resources', {}).get(activity_id) # from resources file
            if not activity_label:
                activity_label = getattr(self, 'node_to_label_from_branch', {}).get(normalized_id)
            if not activity_label:
                activity_label = id_to_label.get(normalized_id)
            if not activity_label:
                activity_label = activity_id
            
            model["activities"][activity_label] = {
                "capacity": 1, 
                "processing_time": activity_data,
                "next_activities": {}
            }
            
            if activity_label in branch_prob:
                for next_label, prob_data in branch_prob[activity_label].items():
                    model["activities"][activity_label]["next_activities"][next_label] = {
                        "probability": prob_data["probability"]
                    }
            
        model["transfer_times"] = {}
        for source_activity, transfer_data in transfer_times.items():
            model["transfer_times"][source_activity] = {}
            
            if source_activity in branch_prob:
                for destination in branch_prob[source_activity].keys():
                    model["transfer_times"][source_activity][destination] = transfer_data

        # Ensure all routing nodes from branch_prob exist as activities
        # to keep the simulation aligned with the extracted graph.
        branch_nodes = set(branch_prob.keys())
        for src, dsts in branch_prob.items():
            branch_nodes.update(dsts.keys())

        for node in branch_nodes:
            if node not in model["activities"]:
                model["activities"][node] = {
                    "capacity": 1,
                    "processing_time": {"type": "fixed", "mean": 0, "arg1": 0, "arg2": 0},
                    "next_activities": {}
                }

        for src, dsts in branch_prob.items():
            if src in model["activities"]:
                for dst, prob_data in dsts.items():
                    model["activities"][src]["next_activities"][dst] = {
                        "probability": prob_data["probability"]
                    }
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

        if "result" in parsed_response: # Check if extraction was successful
            result = parsed_response["result"]
            if isinstance(result, dict):
                if "success" in result and not result["success"]:
                    error_msg = result.get("error", "Unknown error")
                    raise RuntimeError(f"DTLogExtSim extraction failed: {error_msg}")
                if "output_directory" not in result:
                    raise KeyError(f"Response missing 'output_directory'. Full response: {parsed_response}")
                output_dir = result["output_directory"]
            else:
                raise ValueError(f"Unexpected result structure: {parsed_response}")
        else:
            raise ValueError(f"Response missing 'result' field: {parsed_response}")

        # Extract SKG automaton right after DTLogExtSim completes
        if self.automaton_learner is not None:
            print("\n" + "="*60)
            print("Starting SKG (Stochastic Knowledge Graph) extraction...")
            print("="*60)
            skg_output_name = os.path.basename(xes_path).replace('.xes', '_skg.xml')
            try:
                skg_path = self.automaton_learner.learn_automaton(
                    xes_path=xes_path,
                    output_name=skg_output_name,
                    window_minutes=5
                )
                if skg_path:
                    print(f"\nSKG extraction completed: {skg_path}")
                else:
                    print("\nSKG extraction failed, using default")
            except Exception as e:
                print(f"\nError during SKG extraction: {e}")
                print("Continuing with default SKG...")
            print("="*60 + "\n")
        else:
            print("\nSkipping SKG extraction (LSHA not available)\n")

        local_output_dir = os.path.join(os.path.dirname(__file__), "extractor_outputs", os.path.basename(output_dir.strip("/")), "output_data", "output_file")
        params_file = None
        inter_arrival_file = None
        branch_prob_file = None
        transfer_times_file = None
        bpmn_file = None
        
        files = os.listdir(local_output_dir)
        for file in files:
            if "parameters" in file and "json" in file:
                params_file = file
            if "interarrival" in file:
                inter_arrival_file = file
            if "branch_prob" in file:
                branch_prob_file = file
            if "act_distr_wait_time" in file:
                transfer_times_file = file
            if "bpmn" in file:
                bpmn_file = file
        
        if not params_file:
            raise FileNotFoundError(f"Parameters file not found in {local_output_dir}")
        if not inter_arrival_file:
            raise FileNotFoundError(f"Inter-arrival file not found in {local_output_dir}")
        if not branch_prob_file:
            raise FileNotFoundError(f"Branch probability file not found in {local_output_dir}")
        if not bpmn_file:
            raise FileNotFoundError(f"BPMN file not found in {local_output_dir}")

        params_path = os.path.join(local_output_dir, params_file)
        inter_arrival_path = os.path.join(local_output_dir, inter_arrival_file)
        branch_prob_path = os.path.join(local_output_dir, branch_prob_file)
        bpmn_path = os.path.join(local_output_dir, bpmn_file)
        resources_files = [f for f in os.listdir(local_output_dir) if 'resources_of_activities' in f and f.endswith('.json')]
        node_to_label_from_resources = {}
        if resources_files:
            resources_path = os.path.join(local_output_dir, resources_files[0])
            with open(resources_path, 'r') as f:
                resources_data = json.load(f)
            with open(params_path, 'r') as f:
                params_data = json.load(f)
            
            if 'elements' in params_data:
                elements = params_data['elements']
            elif '0' in params_data and 'elements' in params_data['0']:
                elements = params_data['0']['elements']
            else:
                elements = []
            
            resource_to_label = {} # resource_group -> activity_label
            for activity_label, resource_groups in resources_data.items():
                if resource_groups and resource_groups[0]:
                    resource_group = resource_groups[0][0]
                    resource_to_label[resource_group] = activity_label
            
            for elem in elements: # Map node UUIDs to labels via resource groups
                node_uuid = elem['elementId']
                if elem.get('resourceIds') and elem['resourceIds']:
                    resource_group = elem['resourceIds'][0]['resourceName']
                    if resource_group in resource_to_label:
                        activity_label = resource_to_label[resource_group]
                        node_to_label_from_resources[node_uuid] = activity_label
            
            self.node_to_label_from_resources = node_to_label_from_resources
        
        bpmn_model = bpmn_importer.apply(bpmn_path)
        net, initial_marking, final_marking = pm4py.convert.convert_to_petri_net(bpmn_model)

        label_to_id, id_to_label = self.extract_label_to_id_mapping(bpmn_model)
        activities = self.extract_parameters(params_path)
        inter_arrival_time = self.extract_inter_arrival(inter_arrival_path)
        branch_prob = self.extract_branch_prob(branch_prob_path)
        successors = self.extract_successors_from_petri(net)
        for act, succs in successors.items():
            if act not in branch_prob:
                branch_prob[act] = {}
                if len(succs) == 1:
                    only_succ = list(succs)[0]
                    branch_prob[act][only_succ] = {"probability": 1.0}
        
        branch_prob = self.rebalance_zero_probabilities(branch_prob)
        if transfer_times_file:
            transfer_times_path = os.path.join(local_output_dir, transfer_times_file)
            transfer_times = self.extract_transfer_times(transfer_times_path)
        else:
            print("Warning: No transfer times file found. Defaulting to zero transfer times.")
            transfer_times = {}
            
        model = self.create_model(activities, inter_arrival_time, branch_prob, transfer_times, id_to_label, label_to_id)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))        
        if failure:
            output_path = os.path.join(base_dir, "data", "parameters", "digital_twin_with_failure.json")
            model = self.add_failure_params(model)
        else:
            output_path = os.path.join(base_dir, "data", "parameters", "digital_twin.json")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(model, f, indent=2)

        return net, initial_marking, final_marking


if __name__ == "__main__":
    extractor = Extractor()
    xes_path = os.path.join(os.path.dirname(__file__), 'DTLogExtSim', 'log_testing', 'log_test2.xes')
    net, initial_marking, final_marking = extractor.extract_model(xes_path, failure=True)
    pm4py.view_petri_net(net, initial_marking, final_marking, format="png")