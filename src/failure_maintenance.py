import os
import json
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
from failure_interface import FailureInterface


class FailureMaintenanceModule:
    def __init__(self, factory_model_path: str = "lego_factory_with_failure.json"):
        self.factory_model_path = factory_model_path
        self.failure_interface = FailureInterface(factory_model_path)

    def predict_station_failures(self, station_id: str, time_horizon: float = 1000) -> Dict[str, Any]:
        if station_id not in self.failure_interface.model['stations']:
            return {"error": f"Station {station_id} not found"}

        params = self.failure_interface.model['stations'][station_id]['failure_parameters']
        predictions = []

        for i in range(10):
            result = self.failure_interface.simulate(duration=time_horizon, strategy='preventive', station_id=station_id)


            total_failures = result.get('total_failures', 0)
            avg_ttf = time_horizon / total_failures if total_failures > 0 else time_horizon

            predictions.append({
                'sim_id': i,
                'total_failures': total_failures,
                'average_time_to_failure': round(avg_ttf, 2)
            })

        avg_ttf_all = np.mean([p['average_time_to_failure'] for p in predictions])
        reliability = np.exp(-time_horizon / avg_ttf_all)

        return {
            'station_id': station_id,
            'time_horizon': time_horizon,
            'predictions': predictions,
            'statistics': {
                'average_time_to_failure': round(avg_ttf_all, 2),
                'expected_failures_in_horizon': int(time_horizon / avg_ttf_all),
                'reliability_at_horizon': round(reliability, 3)
            },
            'station_parameters': params
        }

    def analyze_maintenance_strategies(self, sim_time: float = 2000) -> Dict[str, Any]:
        results = self.failure_interface.compare_strategies(sim_time)
        report = {
            'strategy_analysis': results,
            'recommendations': self._strategy_recommendations(results),
            'costs': {k: v['total_cost'] for k, v in results.items()},
            'availability': {k: v['availability'] for k, v in results.items()}
        }
        return report

    def optimize_maintenance_schedule(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        freqs = [0.5, 0.75, 1.0, 1.25, 1.5]
        schedules = [self._simulate_schedule(f, constraints) for f in freqs]
        best = max(schedules, key=lambda s: s['score'])
        return best

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        report = {'stations': {}, 'strategies': {}, 'optimal_schedule': {}}
        for sid in self.failure_interface.model['stations']:
            report['stations'][sid] = self.predict_station_failures(sid)

        report['strategies'] = self.analyze_maintenance_strategies()
        report['optimal_schedule'] = self.optimize_maintenance_schedule({
            'budget': 10000,
            'availability_target': 0.95
        })
        return report

    def _simulate_schedule(self, multiplier: float, constraints: Dict[str, Any]) -> Dict[str, Any]:
        schedule, total_cost, availabilities = {}, 0, []
        for sid, sdata in self.failure_interface.model['stations'].items():
            p = sdata['failure_parameters']
            interval = p['maintenance_interval'] / multiplier
            cost = (2000 / interval) * p['maintenance_duration']['mean'] * 50
            avail = interval / (interval + p['repair_time']['mean'])
            total_cost += cost
            availabilities.append(avail)
            schedule[sid] = {'interval': interval, 'cost': cost, 'availability': avail}

        avg_avail = np.mean(availabilities)
        score = avg_avail * 100 - total_cost / 1000
        return {
            'multiplier': multiplier,
            'schedule': schedule,
            'total_cost': round(total_cost, 2),
            'average_availability': round(avg_avail, 3),
            'meets_constraints': total_cost <= constraints.get('budget', float('inf')) and avg_avail >= constraints.get('availability_target', 0.95),
            'score': score
        }

    def _strategy_recommendations(self, results: Dict[str, Any]) -> List[str]:
        if not results:
            return ["No strategy data available."]
        best = min(results.items(), key=lambda x: x[1]['total_cost'])
        return [
            f"Use '{best[0]}' strategy for lowest total cost: ${best[1]['total_cost']:.2f}",
            f"Expected availability: {best[1]['availability']:.2f}%"  
        ]
    

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
    failure_module = FailureMaintenanceModule("lego_factory_with_failure.json")

    prediction = failure_module.predict_station_failures("Station2", 1000)
    print("Predicting failures for Station2...")
    print(clean_output(prediction))

    strategies = failure_module.analyze_maintenance_strategies(2000)
    print("\nAnalyzing maintenance strategies...")
    print(clean_output(strategies))

    constraints = {'budget': 8000, 'availability_target': 0.95}
    optimization = failure_module.optimize_maintenance_schedule(constraints)
    print("\nOptimizing maintenance schedule...")
    print(clean_output(optimization))

    #print("\nGenerating comprehensive failure report...")
    #report = failure_module.generate_comprehensive_report()
    #print("Report generated successfully.")
    # Stampa solo il sommario, o l’intero report pulito se vuoi
    #print(clean_output(report))

