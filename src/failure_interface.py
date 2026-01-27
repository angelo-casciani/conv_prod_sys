import json, os, random
import numpy as np
import time

class FailureInterface:
    def __init__(self):
        self.time = 0
        self.activity_results = {}

    def simulate(self, model, duration=2000, activity_id=None, seed=None):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        else:
            current_seed = int(time.time() * 1000000) % 2**32
            np.random.seed(current_seed)
            random.seed(current_seed)
        
        self.state = {sid: {'degradation': 0.0, 'failures': 0, 'downtime': 0.0}
                      for sid in model['activities']}
        self.time = 0
        self.activity_results = {sid: {'failures': 0, 'downtime': 0.0, 'failure_times': []} 
                                for sid in model['activities']}
        time_step = 1

        activities_to_simulate = [activity_id] if activity_id else list(model['activities'].keys())

        while self.time < duration:
            for sid in activities_to_simulate:
                params = model['activities'][sid]
                s = self.state[sid]
                s['degradation'] += params['failure_parameters']['degradation_factor'] * time_step

                rate = params['failure_parameters']['failure_rate']
                adj_rate = rate * (1 + s['degradation'])
                if random.random() < adj_rate * time_step:
                    repair_time = max(1, np.random.normal(params['failure_parameters']['repair_time']['mean'],
                                                        params['failure_parameters']['repair_time']['std']))
                    s['failures'] += 1
                    s['downtime'] += repair_time
                    self.activity_results[sid]['failures'] += 1
                    self.activity_results[sid]['downtime'] += repair_time
                    self.activity_results[sid]['failure_times'].append(self.time)
                    self.time += repair_time
                    continue

            self.time += time_step

        return self._summary(duration, activity_id=activity_id)

    def _summary(self, total_time, activity_id=None):
        if activity_id:
            res = self.activity_results[activity_id]
            total_failures = res['failures']
            total_downtime = res['downtime']
        else:
            total_failures = sum(r['failures'] for r in self.activity_results.values())
            total_downtime = sum(r['downtime'] for r in self.activity_results.values())

        availability = round((total_time - total_downtime) / total_time * 100, 2)
        return {
            'total_failures': total_failures,
            'total_downtime': round(total_downtime, 2),
            'availability': availability,
        }

if __name__ == "__main__":
    sim = FailureInterface(os.path.join(os.path.dirname(__file__), '..', 'parameters', 'digital_twin_with_failure.json'))
    result = sim.simulate(150)
    print(json.dumps(result, indent=2))
