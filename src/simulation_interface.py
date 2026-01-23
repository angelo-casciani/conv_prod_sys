from simulation import FactorySimulator
from utility import extract_json


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


def interface_with_llm(llm_answer):
    json_request = extract_json(llm_answer)
    task = json_request.get("task")
    simulation_time = json_request.get("simulation_time")
    target_pieces = json_request.get("target_pieces")
    activities_sequence = json_request.get("activities_sequence")
    factory_output = ''

    if task == "sim_with_time":
        factory_output = trigger_time_interval_simulation(simulation_time)
    elif task == "sim_with_number_products":
        factory_output = trigger_batch_production_simulation(target_pieces)
    elif task == "event_prediction":
        factory_output = trigger_activity_prediction(activities_sequence)
    
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