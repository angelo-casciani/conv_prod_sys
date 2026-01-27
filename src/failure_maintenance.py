from datetime import datetime
from typing import Dict, Any
import numpy as np
from failure_interface import FailureInterface
from utility import retrieve_factory_with_failure


class FailureMaintenanceModule:
    def __init__(self):
        self.failure_interface = FailureInterface()

    def predict_activity_failures(self, model, activity_id: str, time_horizon: float = 1000) -> Dict[str, Any]:
        if activity_id not in model['activities']:
            return {"error": f"activity {activity_id} not found"}

        params = model['activities'][activity_id]['failure_parameters']
        predictions = []

        for i in range(10):
            result = self.failure_interface.simulate(model, duration=time_horizon, activity_id=activity_id, seed=42 + i)


            total_failures = result.get('total_failures', 0)
            if total_failures > 0:
                failure_times = self.failure_interface.activity_results[activity_id]['failure_times']
                if failure_times:
                    # Time to first failure
                    first_failure_time = failure_times[0]
                    avg_ttf = first_failure_time
                else:
                    avg_ttf = time_horizon / total_failures
            else:
                avg_ttf = time_horizon

            predictions.append({
                'sim_id': i,
                'total_failures': total_failures,
                'average_time_to_failure': round(avg_ttf, 2)
            })

        ttf_values = [p['average_time_to_failure'] for p in predictions]
        avg_ttf_all = np.mean(ttf_values)
    
        failure_rate = params['failure_rate']
        reliability = np.exp(-failure_rate * time_horizon)

        repair_time_mean = params['repair_time']['mean']
        expected_failures = max(1, int(time_horizon * failure_rate))
        estimated_delay = expected_failures * repair_time_mean

        return {
            'activity_id': activity_id,
            'time_horizon': time_horizon,
            'predictions': predictions,
            'statistics': {
                'average_time_to_failure': round(avg_ttf_all, 2),
                'expected_failures_in_horizon': int(time_horizon / avg_ttf_all),
                'reliability_at_horizon': round(reliability, 3)
            },
            'activity_parameters': params,
            'estimated_maintenance_delay': round(estimated_delay, 2),
        }

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        report = {'activities': {}}
        for sid in self.failure_interface.model['activities']:
            report['activities'][sid] = self.predict_activity_failures(sid)
        return report
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")


def clean_output(obj):
        if isinstance(obj, dict):
            return {k: clean_output(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_output(i) for i in obj]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        else:
            return obj
        
if __name__ == "__main__":
    failure_module = FailureMaintenanceModule()
    model = retrieve_factory_with_failure()

    prediction = failure_module.predict_activity_failures(model, "station11", 1000)
    print("Predicting failures for station11...")
    print(clean_output(prediction))

