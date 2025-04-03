import csv
import os
import pandas as pd
import random

import llm_factory_interface as fa
import uppaal_interface as up


simulation_tasks = {
    "sim_with_time": [
        ("Carry out a simulation for {time} units of time to check how many pieces are produced.", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
        ("How many pieces can be produced in {time} units of time?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
        ("What is the mean processing time after executing the factory for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
        ("What is the mean waiting time after the factory's simulation for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
        ("Tell me the mean transfer time after executing the factory for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
        ("What is the mean processing time of {station} after the factory's execution for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
        ("What is the mean waiting time of {station} after executing the factory for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "stations_sequence": []}),
    ],
    "sim_with_number_products": [
        ("Simulate the execution of the production process to produce {pieces} pieces.", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("How much time is needed to produce {pieces} pieces in the factory?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("Run a simulation to estimate the time required to produce {pieces} products.", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("What is the mean processing time after executing the factory to generate {pieces} products?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("What is the mean waiting time for producing {pieces} pieces?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("Tell me the mean transfer time after executing the factory to produce {pieces} units?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("What is the mean processing time of {station} to produce {pieces} pieces?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
        ("What is the mean waiting time of {station} for creating {pieces} products?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "stations_sequence": []}),
    ],
    "event_prediction": [
        ("What is the next production station after {sequence}?", 
         {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "stations_sequence": "{sequence}".split(", ")}),
        ("Predict the next station given this sequence: {sequence}.", 
         {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "stations_sequence": "{sequence}".split(", ")}),
        ("Based on the sequence {sequence}, what is the most likely next station?", 
         {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "stations_sequence": "{sequence}".split(", ")}),
    ]
}
time_range_sim = range(200, 5001, 500)
pieces_range = range(50, 501, 50)
stations = ["Station1", "Station2", "Station3", "Station4", "Station5"]
tasks_proportions = [0.4, 0.4, 0.2]


def generate_stats_file(filename, samples):
    stats = {task: 0 for task in simulation_tasks.keys()}
    for question, answer in samples:
        for task in stats.keys():
            if task in answer:
                stats[task] += 1
                break
    stats_output_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', f'{filename}_stats.txt')
    with open(stats_output_path, mode="w", encoding="utf-8") as file:
        for task, count in stats.items():
            file.write(f"{task}: {count}\n")

    print(f"Generated statistics and saved to {stats_output_path}")


def write_samples_to_csv(filename, samples):
    output_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', f'{filename}.csv')
    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["question", "answer", "evaluation_type"])
        for question, answer in samples:
            writer.writerow([question, answer.replace("'", '"').replace("{", '').replace("}", ''), filename])
    print(f"Generated {len(samples)} samples and saved to {output_path}")


def main_simulation():
    samples = []
    for _ in range(300):
        task = random.choices(
            population=list(simulation_tasks.keys()),
            weights=tasks_proportions,
            k=1)[0]
        template, answer_template = random.choice(simulation_tasks[task])
        
        if task == "sim_with_time":
            time_value = random.choice(time_range_sim)
            if "{station}" in template:
                station_value = random.choice(stations)
                question = template.format(station=station_value, time=time_value)
            else:
                question = template.format(time=time_value)
            answer = answer_template.copy()
            answer["simulation_time"] = time_value
        elif task == "sim_with_number_products":
            pieces_value = random.choice(pieces_range)
            if "{station}" in template:
                station_value = random.choice(stations)
                question = template.format(station=station_value, pieces=pieces_value)
            else:
                question = template.format(pieces=pieces_value)
            answer = answer_template.copy()
            answer["target_pieces"] = pieces_value
        elif task == "event_prediction":
            sequence_length = random.randint(1, 4)
            sequence = ", ".join(stations[:sequence_length])
            question = template.format(sequence=sequence)
            answer = answer_template.copy()
            answer["stations_sequence"] = sequence.split(", ")        
        samples.append((question, str(answer)))

    write_samples_to_csv('simulation', samples)
    generate_stats_file('simulation', samples)


states_verification = ["q_0", "q_1", "q_2", "q_3", "q_4", "q_5", "q_6", "q_7", "q_8", "q_9", "q_10", "q_11", "q_12", "q_13", "q_14"]
queries_verification = [
    ("Does the system will always eventually reach state {state}.", 
     "A<> s.{state}"),
    ("Does a path where state {state} is reached exist?",
     "E<> s.{state}"),
    ("Verify if the automaton can always stay in state {state} for up to {time} time units.", 
     "A[] s.{state} && s.x <= {time}"),
    ("Does a path where the system stays in state {state} forever exist?", 
     "E[] s.{state}"),
    ("Check if state {state} is reachable within {time} time units.", 
     "E<> s.{state} && s.x <= {time}"),
    ("If the system reaches {state1}, will it eventually be in {state2}?", 
     "s.{state1} --> s.{state2}"),
    ("Verify if the automaton reaches at least once the states {state1} and {state2}.",
     "E<> (s.{state1} && s.{state2})")
]
time_range_verification = range(10, 51, 5)


def main_verification():
    samples = []
    for _ in range(299):
        query_template, uppaal_query_template = random.choice(queries_verification)
        state = random.choice(states_verification)
        state1 = random.choice(states_verification)
        state2 = random.choice(states_verification)
        while state1 == state2:
            state2 = random.choice(states_verification)
        time = random.choice(time_range_verification)

        question = query_template.format(state=state, state1=state1, state2=state2, time=time)
        uppaal_query = uppaal_query_template.format(
            state=f"{state}",
            state1=f"{state1}",
            state2=f"{state2}",
            time=time
        )
        
        samples.append((
            question, 
            str({"task": "verification", "query_nl": question, "uppaal_query": uppaal_query})
        ))

    samples.append((
            "Is there a deadlock at some point?", 
            str({"task": "verification", "query_nl": "Is there a deadlock at some point?", "uppaal_query": "E<> deadlock"})
        ))

    write_samples_to_csv('verification', samples)

unrelated_questions = [
        "What is the weather today?",
        "Tell me a joke.",
        "How many legs does a spider have?",
        "What is the capital of France?",
        "Translate 'hello' to Spanish.",
        "What time is it?",
        "Can you write a poem?",
        "What's the population of the Earth?",
        "How do I bake a cake?",
        "Who won the soccer game yesterday?",
        "Can you solve this math problem for me?",
        "What is 2+2?",
        "Can you describe the Eiffel Tower?",
        "What is the meaning of life?",
        "Tell me a fun fact about space.",
        "How do airplanes fly?",
        "What is your favorite movie?",
        "What is the speed of light?",
        "What is quantum physics?",
        "Can you sing a song?",
        "What is the tallest mountain on Earth?",
        "How does a car engine work?",
        "What is artificial intelligence?",
        "What is the weather like in Paris?",
        "What is a neural network?",
        "How do plants make food?",
        "Who invented the telephone?",
        "How far is the moon?",
        "What is the chemical formula for water?",
        "Can you summarize the plot of 'Romeo and Juliet'?",
        "How does a microwave work?",
        "What are black holes?",
    ]
def generate_unrelated_questions(unrelated_questions, number_samples=100):
    samples = random.choices(unrelated_questions, k=number_samples)
    questions = []
    for s in samples:
        questions.append([s, "no_answer"])

    write_samples_to_csv('unrelated', questions)


def main_routing(simulation_csv, verification_csv, unrelated_csv, output_csv, sim_proportions, total_samples=300):
    sim_df = pd.read_csv(simulation_csv)
    ver_df = pd.read_csv(verification_csv)
    unrel_df = pd.read_csv(unrelated_csv)
    sim_samples_count = total_samples // 3
    ver_samples_count = total_samples // 3
    refuse_samples_count = total_samples - sim_samples_count - ver_samples_count
    sim_with_time_count = int(sim_samples_count * sim_proportions[0])
    sim_with_number_products_count = int(sim_samples_count * sim_proportions[1])
    event_prediction_count = sim_samples_count - sim_with_time_count - sim_with_number_products_count
    
    sim_with_time = sim_df[sim_df["answer"].str.contains('"task": "sim_with_time"')]
    sim_with_number_products = sim_df[sim_df["answer"].str.contains('"task": "sim_with_number_products"')]
    event_prediction = sim_df[sim_df["answer"].str.contains('"task": "event_prediction"')]
    sim_samples = pd.concat([
        sim_with_time.sample(sim_with_time_count, random_state=42),
        sim_with_number_products.sample(sim_with_number_products_count, random_state=42),
        event_prediction.sample(event_prediction_count, random_state=42)
    ])
    sim_samples["answer"] = "factory_simulation"
    ver_samples = ver_df.sample(ver_samples_count, random_state=42)
    ver_samples["answer"] = "uppaal_verification"
    unrel_samples = unrel_df.sample(refuse_samples_count, random_state=42)
    combined_samples = pd.concat([sim_samples, ver_samples, unrel_samples]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    combined_samples.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL)
    print(f"Generated mixed CSV with {len(combined_samples)} samples and saved to {output_csv}")


def main_answer(routing_csv_path):
    questions = []
    new_questions = []
    with open(routing_csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            question, answer, test_type = row
            questions.append([question, answer, test_type])
    
    for question, answer, test_type in questions:
        answer = '{' + answer + '}'
        if test_type == "simulation":
            new_questions.append([question, fa.interface_with_llm(answer), test_type])
        else:
            new_questions.append([question, up.interface_with_llm(answer), test_type])
    
    output_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'answer.csv')
    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["question", "answer", "evaluation_type"])
        for question, answer, test_type in new_questions:
            writer.writerow([question, str(answer).replace("'", '"').replace("{", '').replace("}", ''), test_type])
    print(f"Generated {len(new_questions)} samples and saved to {output_path}")


if __name__ == "__main__":
    main_simulation()
    main_verification()
    generate_unrelated_questions(unrelated_questions)
    sim_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'simulation.csv')
    ver_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'verification.csv')
    unrel_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'unrelated.csv')
    routing_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'routing.csv')
    main_routing(sim_csv, ver_csv, unrel_csv, routing_csv, tasks_proportions)

    