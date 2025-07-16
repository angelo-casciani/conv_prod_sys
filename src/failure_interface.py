import json, os, random
import numpy as np

class FailureInterface:
    def __init__(self, model_path):
        self.model = self.load_model(model_path)
        self.state = {sid: {'degradation': 0.0, 'failures': 0, 'downtime': 0.0}
                      for sid in self.model['stations']}
        self.maintenance_cost = 0.0
        self.time = 0
        self.station_results = {}

    def load_model(self, path):
        path = os.path.join(os.path.dirname(__file__), '..', 'models', path)
        with open(path, 'r') as f:
            return json.load(f)

    def simulate(self, duration=2000, strategy='preventive', station_id=None, seed=None):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        else:
            # Use current time-based seed for true randomness
            import time
            current_seed = int(time.time() * 1000000) % 2**32
            np.random.seed(current_seed)
            random.seed(current_seed)
        self.time = 0
        self.station_results = {sid: {'failures': 0, 'downtime': 0.0, 'maintenance_cost': 0.0, 'failure_times': []} 
                                for sid in self.model['stations']}
        time_step = 1

        stations_to_simulate = [station_id] if station_id else list(self.model['stations'].keys())

        while self.time < duration:
            for sid in stations_to_simulate:
                params = self.model['stations'][sid]
                s = self.state[sid]
                s['degradation'] += params['failure_parameters']['degradation_factor'] * time_step

                rate = params['failure_parameters']['failure_rate']
                adj_rate = rate * (1 + s['degradation'])
                if random.random() < adj_rate * time_step:
                    repair_time = max(1, np.random.normal(params['failure_parameters']['repair_time']['mean'],
                                                        params['failure_parameters']['repair_time']['std']))
                    s['failures'] += 1
                    s['downtime'] += repair_time
                    self.station_results[sid]['failures'] += 1
                    self.station_results[sid]['downtime'] += repair_time
                    self.station_results[sid]['failure_times'].append(self.time)
                    self.time += repair_time
                    continue

                if strategy == 'preventive' and self.time % params['failure_parameters']['maintenance_interval'] == 0:
                    cost = self._maintain(s, params, strategy)
                    self.station_results[sid]['maintenance_cost'] += cost
                elif strategy == 'predictive' and s['degradation'] > 0.5:
                    cost = self._maintain(s, params, strategy)
                    self.station_results[sid]['maintenance_cost'] += cost

            self.time += time_step

        return self._summary(duration, station_id=station_id)
    
    def compare_strategies(self, sim_time=2000):
        strategies = ['preventive', 'predictive', 'reactive']
        results = {}
        for strat in strategies:
            self.state = {sid: {'degradation': 0.0, 'failures': 0, 'downtime': 0.0} for sid in self.model['stations']}
            res = self.simulate(duration=sim_time, strategy=strat)
            results[strat] = res
        return results

    def _maintain(self, s, params, strategy):
        duration = max(1, np.random.normal(params['failure_parameters']['maintenance_duration']['mean'],
                                           params['failure_parameters']['maintenance_duration']['std']))
        cost = 500 if strategy != 'reactive' else 1000
        cost *= (1 + s['degradation'])
        s['degradation'] = max(0, s['degradation'] - 0.5)
        self.maintenance_cost += cost
        return cost  # Return cost so caller can store per station


    def _summary(self, total_time, station_id=None):
        if station_id:
            res = self.station_results[station_id]
            total_failures = res['failures']
            total_downtime = res['downtime']
            maintenance_cost = res['maintenance_cost']
        else:
            total_failures = sum(r['failures'] for r in self.station_results.values())
            total_downtime = sum(r['downtime'] for r in self.station_results.values())
            maintenance_cost = sum(r['maintenance_cost'] for r in self.station_results.values())

        availability = round((total_time - total_downtime) / total_time * 100, 2)
        return {
            'total_failures': total_failures,
            'total_downtime': round(total_downtime, 2),
            'availability': availability,
            'maintenance_cost': round(maintenance_cost, 2),
            'total_cost': round(total_downtime * 100 + maintenance_cost, 2)
        }

if __name__ == "__main__":
    sim = FailureInterface("lego_factory_with_failure.json")
    for strategy in ['preventive', 'predictive', 'reactive']:
        result = sim.simulate(150, strategy)
        print(f"{strategy.capitalize()} strategy: {json.dumps(result, indent=2)}")
