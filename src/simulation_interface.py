from simulation import FactorySimulator
from utility import extract_json
import re
import numpy as np


REQUIRED_SIM_FIELDS = ["replicas", "initial_state_mode", "simulation_time"]


def trigger_time_interval_simulation(simulation_time):
    factory_sim = FactorySimulator(simulation_time)
    factory_sim.run()
    results = factory_sim.get_statistics()
    return results


def trigger_batch_production_simulation(target_pieces):
    factory_sim = FactorySimulator()
    factory_sim.compute_batch_production_time(target_pieces)
    results = factory_sim.get_statistics()
    return results


def trigger_activity_prediction(activities_sequence):
    factory_sim = FactorySimulator()
    predicted_activity = factory_sim.predict_next_activity(activities_sequence)
    return f"Predicted next activity: {predicted_activity}"


def _to_float(value):
    if value in [None, "", "null", "None"]:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    if value in [None, "", "null", "None"]:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _normalize_initial_state_mode(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ["empty", "cold", "cold_start", "from_empty"]:
        return "empty"
    if text in ["warm_up", "warmup", "warm", "wip"]:
        return "warm_up"
    return text


def normalize_simulation_request(json_request):
    normalized = dict(json_request)
    normalized["replicas"] = _to_int(normalized.get("replicas"))
    normalized["simulation_time"] = _to_float(normalized.get("simulation_time"))
    normalized["target_pieces"] = _to_int(normalized.get("target_pieces"))
    normalized["random_seed"] = _to_int(normalized.get("random_seed"))
    normalized["initial_state_mode"] = _normalize_initial_state_mode(normalized.get("initial_state_mode"))
    normalized["warm_up_replicas"] = _to_int(normalized.get("warm_up_replicas"))
    normalized["warm_up_time"] = _to_float(normalized.get("warm_up_time"))
    return normalized


def merge_simulation_request(base_request, updates):
    merged = dict(base_request or {})
    for key, value in (updates or {}).items():
        if value not in [None, ""]:
            merged[key] = value
    return normalize_simulation_request(merged)


def extract_simulation_params_from_text(text):
    user_text = (text or "").lower().strip()
    params = {}

    match = re.search(r"replicas?\s*[:=]?\s*(\d+)", user_text)
    if not match:
        match = re.search(r"(\d+)\s*replicas?", user_text)
    if match:
        params["replicas"] = int(match.group(1))

    if any(token in user_text for token in ["empty initial", "empty state", "from empty", "cold start", "initial state empty"]):
        params["initial_state_mode"] = "empty"
    elif any(token in user_text for token in ["warm up", "warm-up", "warmup", "wip"]):
        params["initial_state_mode"] = "warm_up"

    sim_time_match = re.search(r"simulation[_\s-]*time\s*[:=]?\s*(\d+(?:\.\d+)?)", user_text)
    if sim_time_match:
        params["simulation_time"] = float(sim_time_match.group(1))
    else:
        sec_match = re.search(
            r"(?:(?:for|in|time)\s*(\d+(?:\.\d+)?)\s*(?:seconds|second|secs|sec|s)\b)|(?:\b(\d+(?:\.\d+)?)\s*(?:seconds|second|secs|sec|s)\b)",
            user_text,
        )
        if sec_match:
            params["simulation_time"] = float(sec_match.group(1) or sec_match.group(2))
        else:
            plain_number_match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", user_text)
            if plain_number_match:
                params["simulation_time"] = float(plain_number_match.group(1))

    warm_rep_match = re.search(r"warm[_\s-]*up[_\s-]*replicas?\s*[:=]?\s*(\d+)", user_text)
    if warm_rep_match:
        params["warm_up_replicas"] = int(warm_rep_match.group(1))

    warm_time_match = re.search(r"warm[_\s-]*up[_\s-]*time\s*[:=]?\s*(\d+(?:\.\d+)?)", user_text)
    if warm_time_match:
        params["warm_up_time"] = float(warm_time_match.group(1))

    if "target" in user_text or "piece" in user_text or "product" in user_text or "unit" in user_text:
        target_match = re.search(r"target[_\s-]*pieces?\s*[:=]?\s*(\d+)", user_text)
        if not target_match:
            target_match = re.search(r"(\d+)\s*(?:pieces|products|units)\b", user_text)
        if target_match:
            params["target_pieces"] = int(target_match.group(1))

    return normalize_simulation_request(params)


def find_missing_required_parameters(json_request):
    task = json_request.get("task")
    if task == "event_prediction":
        return []

    normalized = normalize_simulation_request(json_request)
    missing = []

    if normalized.get("replicas") is None or normalized.get("replicas") <= 0:
        missing.append("replicas")

    state_mode = normalized.get("initial_state_mode")
    if state_mode not in ["empty", "warm_up"]:
        missing.append("initial_state_mode")

    if normalized.get("simulation_time") is None or normalized.get("simulation_time") <= 0:
        missing.append("simulation_time")

    if state_mode == "warm_up":
        if normalized.get("warm_up_replicas") is None or normalized.get("warm_up_replicas") <= 0:
            missing.append("warm_up_replicas")
        if normalized.get("warm_up_time") is None or normalized.get("warm_up_time") <= 0:
            missing.append("warm_up_time")

    return missing


def _mean(values):
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _average_station_metrics(results, metric_key):
    if not results:
        return {}
    stations = results[0][metric_key].keys()
    averaged = {}
    for station in stations:
        averaged[station] = _mean([rep[metric_key].get(station, 0.0) for rep in results])
    return averaged


def _run_single_replica(request):
    simulator = FactorySimulator()
    initial_snapshot = simulator.capture_snapshot()
    warm_up_pieces_produced = 0

    if request["initial_state_mode"] == "warm_up":
        warm_up_replicas = int(request.get("warm_up_replicas") or 1)
        if warm_up_replicas <= 0:
            warm_up_replicas = 1
        for _ in range(warm_up_replicas):
            simulator.run_for(request["warm_up_time"])
        initial_snapshot = simulator.capture_snapshot()
        warm_up_pieces_produced = int(initial_snapshot["total_pieces_produced"])

    simulator.run_for(request["simulation_time"])
    deadline_stats = simulator.get_statistics_since(initial_snapshot, request["simulation_time"])
    deadline_stats["pieces_produced_during_warm_up"] = warm_up_pieces_produced
    deadline_stats["pieces_produced_in_measured_window"] = deadline_stats["total_pieces_produced"]

    required_time = None
    if request.get("target_pieces"):
        time_sim = FactorySimulator()
        time_snapshot = time_sim.capture_snapshot()
        if request["initial_state_mode"] == "warm_up":
            warm_up_replicas = int(request.get("warm_up_replicas") or 1)
            if warm_up_replicas <= 0:
                warm_up_replicas = 1
            for _ in range(warm_up_replicas):
                time_sim.run_for(request["warm_up_time"])
            time_snapshot = time_sim.capture_snapshot()
        required_time_total = time_sim.compute_batch_production_time(request["target_pieces"])
        required_time = float(required_time_total - time_snapshot["env_time"])

    return deadline_stats, required_time


def run_replicated_simulation(json_request):
    request = normalize_simulation_request(json_request)
    replicas = int(request["replicas"])
    base_seed = int(request.get("random_seed") if request.get("random_seed") is not None else 10)

    replica_stats = []
    required_times = []
    for replica_idx in range(replicas):
        np.random.seed(base_seed + replica_idx)
        stats, required_time = _run_single_replica(request)
        replica_stats.append(stats)
        if required_time is not None:
            required_times.append(required_time)

    total_pieces_samples = [rep["total_pieces_produced"] for rep in replica_stats]
    total_pieces_std = float(np.std(total_pieces_samples)) if total_pieces_samples else 0.0
    total_pieces_se = float(total_pieces_std / np.sqrt(len(total_pieces_samples))) if total_pieces_samples else 0.0

    averaged = {
        "total_pieces_produced": _mean(total_pieces_samples),
        "pieces_produced_in_measured_window": _mean([rep["pieces_produced_in_measured_window"] for rep in replica_stats]),
        "pieces_produced_during_warm_up": _mean([rep.get("pieces_produced_during_warm_up", 0) for rep in replica_stats]),
        "mean_waiting_times": _average_station_metrics(replica_stats, "mean_waiting_times"),
        "mean_processing_times": _average_station_metrics(replica_stats, "mean_processing_times"),
        "total_mean_waiting_time": _mean([rep["total_mean_waiting_time"] for rep in replica_stats]),
        "total_mean_processing_time": _mean([rep["total_mean_processing_time"] for rep in replica_stats]),
        "total_mean_transfer_time": _mean([rep["total_mean_transfer_time"] for rep in replica_stats]),
        "total_execution_time": request["simulation_time"],
        "measured_execution_time": request["simulation_time"],
        "replicas": replicas,
        "effective_replicas": replicas,
        "random_seed": base_seed,
        "initial_state_mode": request["initial_state_mode"],
        "total_pieces_std": total_pieces_std,
        "total_pieces_ci95_halfwidth": 1.96 * total_pieces_se,
    }

    if request["initial_state_mode"] == "warm_up":
        averaged["warm_up_replicas"] = request["warm_up_replicas"]
        averaged["warm_up_time"] = request["warm_up_time"]
        averaged["effective_warm_up_time"] = float(request["warm_up_replicas"] * request["warm_up_time"])
    else:
        averaged["effective_warm_up_time"] = 0.0

    target_pieces = request.get("target_pieces")
    if target_pieces is not None:
        averaged["target_pieces"] = target_pieces
        averaged["mean_time_needed_for_target_pieces"] = _mean(required_times) if required_times else 0.0
        averaged["mean_time_needed_for_target_pieces_post_warmup"] = averaged["mean_time_needed_for_target_pieces"]
        required_time_std = float(np.std(required_times)) if required_times else 0.0
        required_time_se = float(required_time_std / np.sqrt(len(required_times))) if required_times else 0.0
        averaged["time_needed_std"] = required_time_std
        averaged["time_needed_ci95_halfwidth"] = 1.96 * required_time_se
        averaged["can_meet_deadline"] = averaged["mean_time_needed_for_target_pieces"] <= request["simulation_time"]

    return averaged


def interface_with_llm(llm_answer):
    json_request = extract_json(llm_answer)
    if not isinstance(json_request, dict):
        return {"task": "invalid_simulation_request", "results": "Could not parse simulation JSON request."}

    json_request = normalize_simulation_request(json_request)
    task = json_request.get("task")
    activities_sequence = json_request.get("activities_sequence")
    factory_output = ''

    if task in ["sim_with_time", "sim_with_number_products"]:
        factory_output = run_replicated_simulation(json_request)
    elif task == "event_prediction":
        factory_output = trigger_activity_prediction(activities_sequence)
    else:
        factory_output = f"Unsupported simulation task: {task}"
    
    json_request["results"] = factory_output
    return json_request


"""def main():
    llm_input = 'Given the user request, this is the JSON to invoke the factory: {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "activities_sequence": ["activity1", "activity2"]}'
    factory_output = interface_with_llm(llm_input)

    
    llm_input = 'Given the user request, this is the JSON to invoke the factory: {"task": "time_interval", "simulation_time": 2000, "target_pieces": "", "activities_sequence": []}'
    factory_output = interface_with_llm(llm_input)
    
    llm_input = 'Given the user request, this is the JSON to invoke the factory: {"task": "batch_production", "simulation_time": "", "target_pieces": 100, "activities_sequence": []}'
    factory_output = interface_with_llm(llm_input)
    
    print(factory_output)

if __name__ == "__main__":
    main()"""