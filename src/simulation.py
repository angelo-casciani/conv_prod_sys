import os
import simpy
import json
import numpy as np
from scipy import stats


class FactorySimulator:
    def __init__(self, simulation_time=None, config_file=None):
        config_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'parameters', 'digital_twin.json')
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.simulation_time = simulation_time
        self.env = simpy.Environment()
        self.activities = {}
        self.stats = {
            "total_pieces_produced": 0,
            "waiting_times": {s: [] for s in self.config["activities"]},
            "processing_times": {s: [] for s in self.config["activities"]},
            "total_processing_time": [],
            "total_waiting_time": [],
            "total_transfer_time": []
        }

        for activity_name, activity_data in self.config["activities"].items():
            self.activities[activity_name] = {
                "resource": simpy.Resource(self.env, capacity=activity_data["capacity"]),
                "processing_time": {
                    "type": activity_data["processing_time"]["type"],
                    "mean": activity_data["processing_time"]["mean"],
                    "arg1": activity_data["processing_time"]["arg1"],
                    "arg2": activity_data["processing_time"]["arg2"]
                },
                "next_activities": activity_data["next_activities"]
            }

        self.start_activity = None
        all_activities = set(self.config["activities"].keys())
        activities_with_predecessors = set()

        for activity_name, activity_data in self.config["activities"].items():
            for next_act in activity_data["next_activities"].keys():
                activities_with_predecessors.add(next_act)

        start_activities = all_activities - activities_with_predecessors

        if start_activities:
            self.start_activity = list(start_activities)[0]
            print(f"Start activity identified: {self.start_activity}")
        else:
            print("Warning: No start activity found!")

    def arrival_generator(self):
        # It simulates the arrival of new pieces to process based on inter-arrival time distribution.
        while True:
            inter_arrival_time = max(0, self.sample_distribution(self.config["inter_arrival_time"]))
            if inter_arrival_time == 0:
                inter_arrival_time = 0.1
            yield self.env.timeout(inter_arrival_time)
            self.env.process(self.process_piece(self.start_activity))

    def choose_next_activity(self, next_activities):
        # Select the next activity based on provided probabilities.
        if not next_activities:
            return None  # No next activity

        activities, probabilities = zip(*[(activity, data["probability"]) for activity, data in next_activities.items()])
        return np.random.choice(activities, p=probabilities)

    def sample_distribution(self, processing_time):
        dist_type = processing_time.get("type", "fixed").lower()
        mean = float(processing_time.get("mean", 0))
        arg1 = processing_time.get("arg1")
        arg2 = processing_time.get("arg2")
        
        arg1 = float(arg1) if arg1 not in [None, '', 0, '0'] else 0
        arg2 = float(arg2) if arg2 not in [None, '', 0, '0'] else 0
        
        if dist_type == "fixed":
            return float(mean)
        
        try:
            result = None
            
            if dist_type in ["normal", "gaussian", "norm"]:
                std = arg1 if arg1 > 0 else 0.1
                result = stats.norm(loc=mean, scale=std).rvs()
            
            elif dist_type == "uniform":
                min_val = arg1
                max_val = arg2
                if max_val > min_val:
                    result = stats.uniform(loc=min_val, scale=max_val - min_val).rvs()
                else:
                    result = mean
            
            elif dist_type in ["exponential", "expon"]:
                scale = mean if mean > 0 else 0.01
                result = stats.expon(loc=0, scale=scale).rvs()
            
            elif dist_type == "gamma":
                variance = arg1
                if variance > 0 and mean > 0:
                    shape = (mean ** 2) / variance
                    scale = variance / mean
                    result = stats.gamma(a=shape, loc=0, scale=scale).rvs()
                else:
                    result = stats.gamma(a=1, loc=0, scale=max(mean, 0.01)).rvs()
            
            elif dist_type in ["lognormal", "lognorm"]:
                variance = arg1
                if mean > 0 and variance > 0:
                    sigma2 = np.log(variance / (mean ** 2) + 1)
                    mu = np.log(mean) - 0.5 * sigma2
                    sigma = np.sqrt(sigma2)
                    result = stats.lognorm(s=sigma, loc=0, scale=np.exp(mu)).rvs()
                else:
                    result = max(mean, 0.01)
            
            elif dist_type in ["triangular", "triang"]:
                if mean > 0:
                    loc = 0
                    scale = 2 * mean
                    c = 0.5
                    result = stats.triang(c=c, loc=loc, scale=scale).rvs()
                else:
                    result = 0.01 
            
            else:
                print(f"Warning: Unknown distribution type '{dist_type}', using mean value")
                result = mean
            
            if isinstance(result, np.ndarray):
                result = float(result.item())
            else:
                result = float(result)
            
            if np.isnan(result) or np.isinf(result):
                print(f"Warning: Invalid sample ({result}) from {dist_type}, using mean={mean}")
                return float(mean) if mean > 0 else 0.01
            
            return result
                
        except Exception as e:
            print(f"Error sampling from {dist_type}: {e}, using mean value")
            import traceback
            traceback.print_exc()
            return float(mean) if mean > 0 else 0.01
        
    def process_piece(self, activity_name):
        # It processes a piece through the factory activities.
        while activity_name:
            activity = self.activities[activity_name]
            # Request a slot in the current activity's capacity
            with activity["resource"].request() as request:
                arrival_time = self.env.now
                yield request  # Wait for resource
                wait_time = self.env.now - arrival_time
                self.stats["waiting_times"][activity_name].append(wait_time)
                self.stats["total_waiting_time"].append(wait_time)

                # Processing time at the current activity
                processing_time = max(0, self.sample_distribution(activity["processing_time"]))
                yield self.env.timeout(processing_time)
                self.stats["processing_times"][activity_name].append(processing_time)
                self.stats["total_processing_time"].append(processing_time)

            # Decide the next activity based on probabilities
            next_activity = self.choose_next_activity(activity["next_activities"])
            if next_activity:
                # Check if there’s a defined transfer time between the activities
                transfer_data = self.config["transfer_times"].get(activity_name, {}).get(next_activity)
                if transfer_data:
                    transfer_time = max(0, self.sample_distribution(transfer_data))
                    yield self.env.timeout(transfer_time)
                    self.stats["total_transfer_time"].append(transfer_time)
            else:
                self.stats["total_pieces_produced"] += 1  # Increment the counter when a part completes processing
                break

            activity_name = next_activity

    def run(self):
        """Run the simulation for the specified simulation time."""
        self.env.process(self.arrival_generator())
        if self.simulation_time is not None:
            # Run for a fixed time if provided
            self.env.run(until=self.simulation_time)
        else:
            # If no fixed time, stop condition handled in other functions
            raise ValueError("No simulation time provided. Use compute_batch_production_time for batch runs.")

    def get_statistics(self):
        """Calculate and return statistics, including the input simulation time."""
        mean_waiting_times = {s: np.mean(times) if times else 0 for s, times in self.stats["waiting_times"].items()}
        mean_processing_times = {s: np.mean(times) if times else 0 for s, times in self.stats["processing_times"].items()}
        total_mean_waiting_time = np.mean(self.stats["total_waiting_time"]) if self.stats["total_waiting_time"] else 0
        total_mean_processing_time = np.mean(self.stats["total_processing_time"]) if self.stats["total_processing_time"] else 0
        total_mean_transfer_time = np.mean(self.stats["total_transfer_time"]) if self.stats["total_transfer_time"] else 0

        return {
            "total_pieces_produced": self.stats["total_pieces_produced"],
            "mean_waiting_times": mean_waiting_times,
            "mean_processing_times": mean_processing_times,
            "total_mean_waiting_time": total_mean_waiting_time,
            "total_mean_processing_time": total_mean_processing_time,
            "total_mean_transfer_time": total_mean_transfer_time,
            "total_execution_time": self.simulation_time
        }

    def predict_next_activity(self, activity_sequence):
        # Predicts the next activity given a sequence of activities.
        if not activity_sequence:
            return None  # No prediction possible if the sequence is empty
        last_activity = activity_sequence[-1]
        next_activities = self.activities[last_activity]["next_activities"]
        if not next_activities:
            return None
        activities, probabilities = zip(*[(activity, data["probability"]) for activity, data in next_activities.items()])

        # Predict the next activity based on probabilities
        predicted_next_activity = np.random.choice(activities, p=probabilities)
        return predicted_next_activity

    def compute_batch_production_time(self, target_pieces):
        # Computes the time needed to produce a specified number of pieces incrementally.
        self.env.process(self.arrival_generator())
        while self.stats["total_pieces_produced"] < target_pieces:
            self.env.run(until=self.env.now + 1)
        self.simulation_time = self.env.now