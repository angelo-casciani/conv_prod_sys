import os
import simpy
import json
import numpy as np


class FactorySimulator:
    def __init__(self, simulation_time=None, config_file=None):
        config_file = os.path.join(os.path.dirname(__file__), '..', 'models', 'lego_factory.json')
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.simulation_time = simulation_time
        self.env = simpy.Environment()
        self.stations = {}
        self.stats = {
            "total_pieces_produced": 0,
            "waiting_times": {s: [] for s in self.config["stations"]},
            "processing_times": {s: [] for s in self.config["stations"]},
            "total_processing_time": [],
            "total_waiting_time": [],
            "total_transfer_time": []
        }

        for station_name, station_data in self.config["stations"].items():
            self.stations[station_name] = {
                "resource": simpy.Resource(self.env, capacity=station_data["capacity"]),
                "processing_time_mean": station_data["processing_time"]["mean"],
                "processing_time_std": station_data["processing_time"]["std"],
                "next_stations": station_data["next_stations"]
            }

    def arrival_generator(self):
        # It simulates the arrival of new pieces to process based on inter-arrival time distribution.
        while True:
            inter_arrival_time = max(0, np.random.normal(self.config["inter_arrival_time"]["mean"],
                                                         self.config["inter_arrival_time"]["std"]))
            yield self.env.timeout(inter_arrival_time)
            self.env.process(self.process_piece("Station1"))

    def choose_next_station(self, next_stations):
        # Select the next station based on provided probabilities.
        if not next_stations:
            return None  # No next station

        stations, probabilities = zip(*[(station, data["probability"]) for station, data in next_stations.items()])
        return np.random.choice(stations, p=probabilities)

    def process_piece(self, station_name):
        # It processes a piece through the factory stations.
        while station_name:
            station = self.stations[station_name]

            # Request a slot in the current station's capacity
            with station["resource"].request() as request:
                arrival_time = self.env.now
                yield request  # Wait for resource
                wait_time = self.env.now - arrival_time
                self.stats["waiting_times"][station_name].append(wait_time)
                self.stats["total_waiting_time"].append(wait_time)

                # Processing time at the current station
                processing_time = max(0, np.random.normal(station["processing_time_mean"],
                                                          station["processing_time_std"]))
                yield self.env.timeout(processing_time)
                self.stats["processing_times"][station_name].append(processing_time)
                self.stats["total_processing_time"].append(processing_time)

            # Decide the next station based on probabilities
            next_station = self.choose_next_station(station["next_stations"])
            if next_station:
                # Check if there’s a defined transfer time between the stations
                transfer_data = self.config["transfer_times"].get(station_name, {}).get(next_station)
                if transfer_data:
                    transfer_time = max(0, np.random.normal(transfer_data["mean"], transfer_data["std"]))
                    yield self.env.timeout(transfer_time)
                    self.stats["total_transfer_time"].append(transfer_time)
            else:
                self.stats["total_pieces_produced"] += 1  # Increment the counter when a part completes processing
                break

            station_name = next_station

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
        mean_waiting_times = {s: np.mean(times) for s, times in self.stats["waiting_times"].items()}
        mean_processing_times = {s: np.mean(times) for s, times in self.stats["processing_times"].items()}
        total_mean_waiting_time = np.mean(self.stats["total_waiting_time"])
        total_mean_processing_time = np.mean(self.stats["total_processing_time"])
        total_mean_transfer_time = np.mean(self.stats["total_transfer_time"])

        return {
            "total_pieces_produced": self.stats["total_pieces_produced"],
            "mean_waiting_times": mean_waiting_times,
            "mean_processing_times": mean_processing_times,
            "total_mean_waiting_time": total_mean_waiting_time,
            "total_mean_processing_time": total_mean_processing_time,
            "total_mean_transfer_time": total_mean_transfer_time,
            "total_execution_time": self.simulation_time
        }

    def predict_next_station(self, station_sequence):
        # Predicts the next station given a sequence of stations.
        if not station_sequence:
            return None  # No prediction possible if the sequence is empty
        last_station = station_sequence[-1]
        next_stations = self.stations[last_station]["next_stations"]
        if not next_stations:
            return None
        stations, probabilities = zip(*[(station, data["probability"]) for station, data in next_stations.items()])

        # Predict the next station based on probabilities
        predicted_next_station = np.random.choice(stations, p=probabilities)
        return predicted_next_station

    def compute_batch_production_time(self, target_pieces):
        # Computes the time needed to produce a specified number of pieces incrementally.
        self.env.process(self.arrival_generator())
        while self.stats["total_pieces_produced"] < target_pieces:
            self.env.run(until=self.env.now + 1)
        self.simulation_time = self.env.now
