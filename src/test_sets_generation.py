import csv
import os
import pandas as pd
import random

import llm_factory_interface as fa
import uppaal_interface as up
import json

simulation_tasks = {
    "sim_with_time": [
        ("Carry out a simulation for {time} units of time to check how many pieces are produced.", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
        ("How many pieces can be produced in {time} units of time?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
        ("What is the mean processing time after executing the factory for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
        ("What is the mean waiting time after the factory's simulation for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
        ("Tell me the mean transfer time after executing the factory for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
        ("What is the mean processing time of {activity} after the factory's execution for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
        ("What is the mean waiting time of {activity} after executing the factory for {time} time units?", 
         {"task": "sim_with_time", "simulation_time": "{time}", "target_pieces": "", "activities_sequence": []}),
    ],
    "sim_with_number_products": [
        ("Simulate the execution of the production process to produce {pieces} pieces.", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("How much time is needed to produce {pieces} pieces in the factory?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("Run a simulation to estimate the time required to produce {pieces} products.", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("What is the mean processing time after executing the factory to generate {pieces} products?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("What is the mean waiting time for producing {pieces} pieces?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("Tell me the mean transfer time after executing the factory to produce {pieces} units?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("What is the mean processing time of {activity} to produce {pieces} pieces?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
        ("What is the mean waiting time of {activity} for creating {pieces} products?", 
         {"task": "sim_with_number_products", "simulation_time": "", "target_pieces": "{pieces}", "activities_sequence": []}),
    ],
    "event_prediction": [
        ("What is the next production activity after {sequence}?", 
         {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "activities_sequence": "{sequence}".split(", ")}),
        ("Predict the next activity given this sequence: {sequence}.", 
         {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "activities_sequence": "{sequence}".split(", ")}),
        ("Based on the sequence {sequence}, what is the most likely next activity?", 
         {"task": "event_prediction", "simulation_time": "", "target_pieces": "", "activities_sequence": "{sequence}".split(", ")}),
    ]
}
time_range_sim = range(200, 5001, 500)
pieces_range = range(50, 501, 50)
activities = ["activity1", "activity2", "activity3", "activity4", "activity5", "activity6"]
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
            if isinstance(answer, dict):
                answer = json.dumps(answer)
            elif isinstance(answer, str) and answer.startswith('{') and answer.endswith('}'):
                try:
                    answer_dict = eval(answer)
                    answer = json.dumps(answer_dict)
                except:
                    pass
            writer.writerow([question, answer, filename])
    print(f"Generated {len(samples)} samples and saved to {output_path}")


def main_simulation():
    samples = []
    for _ in range(15):
        task = random.choices(
            population=list(simulation_tasks.keys()),
            weights=tasks_proportions,
            k=1)[0]
        template, answer_template = random.choice(simulation_tasks[task])
        
        if task == "sim_with_time":
            time_value = random.choice(time_range_sim)
            if "{activity}" in template:
                activity_value = random.choice(activities)
                question = template.format(activity=activity_value, time=time_value)
            else:
                question = template.format(time=time_value)
            answer = answer_template.copy()
            answer["simulation_time"] = time_value
        elif task == "sim_with_number_products":
            pieces_value = random.choice(pieces_range)
            if "{activity}" in template:
                activity_value = random.choice(activities)
                question = template.format(activity=activity_value, pieces=pieces_value)
            else:
                question = template.format(pieces=pieces_value)
            answer = answer_template.copy()
            answer["target_pieces"] = pieces_value
        elif task == "event_prediction":
            sequence_length = random.randint(1, 4)
            sequence = ", ".join(activities[:sequence_length])
            question = template.format(sequence=sequence)
            answer = answer_template.copy()
            answer["activities_sequence"] = sequence.split(", ")        
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
    for _ in range(15):
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


factory_info_questions = [
    ("What is the mean processing time at activity1?", {
    "task": "factory_info",
    "query_nl": "What is the mean processing time at activity1?",
    "response": ""
}),
    ("What is the standard deviation of the processing time at activity2?", {
    "task": "factory_info",
    "query_nl": "What is the standard deviation of the processing time at activity2?",
    "response": ""
}),
    ("What are the possible next activities after activity3?", {
    "task": "factory_info",
    "query_nl": "What are the possible next activities after activity3?",
    "response": ""
}),
    ("What is the probability of routing from activity1 to activity2?", {
    "task": "factory_info",
    "query_nl": "What is the probability of routing from activity1 to activity2?",
    "response": ""
}),
    ("What is the inter-arrival time of products?", {
    "task": "factory_info",
    "query_nl": "What is the inter-arrival time of products?",
    "response": ""
}),
    ("What is the mean transfer time from activity3 to activity4?", {
    "task": "factory_info",
    "query_nl": "What is the mean transfer time from activity3 to activity4?",
    "response": ""
}),
    ("What is the capacity of activity5?", {
    "task": "factory_info",
    "query_nl": "What is the capacity of activity5?",
    "response": ""
}),
    ("How many activities are there in the production line?", {
    "task": "factory_info",
    "query_nl": "How many activities are there in the production line?",
    "response": ""
}),
    ("Which activity has the longest mean processing time?", {
    "task": "factory_info",
    "query_nl": "Which activity has the longest mean processing time?",
    "response": ""
}),
    ("What is the standard deviation of the inter-arrival time?", {
    "task": "factory_info",
    "query_nl": "What is the standard deviation of the inter-arrival time?",
    "response": ""
}),
    ("Which activity has the smallest capacity?", {
    "task": "factory_info",
    "query_nl": "Which activity has the smallest capacity?",
    "response": ""
}),
    ("What is the mean transfer time between activity1 and activity5?", {
    "task": "factory_info",
    "query_nl": "What is the mean transfer time between activity1 and activity5?",
    "response": ""
}),
    ("Is there any activity with parallel routing options?", {
    "task": "factory_info",
    "query_nl": "Is there any activity with parallel routing options?",
    "response": ""
}),
    ("Which activities have probabilistic routing defined?", {
    "task": "factory_info",
    "query_nl": "Which activities have probabilistic routing defined?",
    "response": ""
})
]


def generate_factory_info_questions(factory_info_questions, number_samples=15):
    samples = random.choices(factory_info_questions, k=number_samples)
    questions = []
    for s, a in samples:
        questions.append([s, a])

    write_samples_to_csv('factory_info', questions)

process_mining_questions = process_mining_questions = [
    ("Can you discover the process model from the event log?", {
    "task": "process_discovery"
}),
    ("Can you perform conformance checking between the event log and the reference model?", {
    "task": "conformance_checking"
}),
    ("What is the mean throughput time of all completed cases?", {
    "task": "performance_analysis",
    "metric": "throughput_time"
}),
    ("What are the frequencies of each activity in the event log?", {
    "task": "performance_analysis",
    "metric": "activity_frequency"
}),
    ("What are the top 5 most frequent variants in the log?", {
    "task": "performance_analysis",
    "metric": "top_variants",
    "k": 5
}),
    ("Can you list the start and end activities for the process?", {
    "task": "performance_analysis",
    "metric": "start_end_activities"
}),
    ("Can you filter the log between 2025-03-01T00:00:00 and 2025-03-05T23:59:00?", {
    "task": "filter_by_time_range",
    "start_date": "2025-03-01T00:00:00", 
    "end_date": "2025-03-05T23:59:00"
}),
    ("Can you show the discovered Petri net model?", {
    "task": "process_discovery"
}),
    ("Can you show me the top 3 variants that are present in the event log?", {
    "task": "performance_analysis",
    "metric": "top_variants",
    "k": 3
})
]

def generate_process_mining_questions(process_mining_questions, number_samples=15):
    samples = random.choices(process_mining_questions, k=number_samples)
    questions = []
    for s, a in samples:
        questions.append([s, a])

    write_samples_to_csv('process_mining', questions)

hybrid_questions = hybrid_questions = [
    ("How much time is needed to produce 60 pieces given that activity3 might fail? Also, verify if the system avoids deadlocks during production.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How much time is needed to produce 60 pieces?",
            "type": "simulation"
        },
        {
            "question": "What are the failure patterns of activity3?",
            "type": "failure"
        },
        {
            "question": "Is the system deadlock free during production?",
            "type": "validation"
        }
    ]
}),
    ("Can 100 products be made within 200 units of time? Validate whether state q4 is reachable and check activity5 failure likelihood.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Can 100 products be made within 200 units of time?",
            "type": "simulation"
        },
        {
            "question": "What is the failure likelihood of activity5?",
            "type": "failure"
        },
        {
            "question": "Is state q4 reachable?",
            "type": "validation"
        }
    ]
}),
    ("Will the process reach state q3? How long does it take to produce 25 units considering possible degradation on activity2?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long does it take to produce 25 units?",
            "type": "simulation"
        },
        {
            "question": "What are the degradation effects on activity2?",
            "type": "failure"
        },
        {
            "question": "Will the process reach state q3?",
            "type": "validation"
        }
    ]
}),
    ("Simulate the system for 150 products and verify if q1 is eventually reached. Then confirm there are no deadlocks in the process.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for 150 products.",
            "type": "simulation"
        },
        {
            "question": "Is state q1 eventually reached?",
            "type": "validation"
        },
        {
            "question": "Is the process free of deadlocks?",
            "type": "validation"
        }
    ]
}),
    ("Considering preventive maintenance on activity4, how many pieces can be produced in 100 units of time?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How many pieces can be produced in 100 units of time?",
            "type": "simulation"
        },
        {
            "question": "What are the maintenance effects on activity4?",
            "type": "failure"
        }
    ]
}),
    ("Is state q2 reachable during production? Estimate the time needed to manufacture 40 pieces assuming activity1 failure.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Estimate the time needed to manufacture 40 pieces.",
            "type": "simulation"
        },
        {
            "question": "Check activity1's failure predictions.",
            "type": "failure"
        },
        {
            "question": "Is state q2 reachable during production?",
            "type": "validation"
        }
    ]
}),
    ("How long does it take to produce 200 pieces when activity5 is under maintenance? Also, check whether q3 remains reachable.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long does it take to produce 200 pieces?",
            "type": "simulation"
        },
        {
            "question": "What are the effects of maintenance on activity5?",
            "type": "failure"
        },
        {
            "question": "Is state q3 reachable during production?",
            "type": "validation"
        }
    ]
}),
    ("Can you simulate 300 time units and verify if all activities eventually complete without entering a deadlock state?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for 300 time units.",
            "type": "simulation"
        },
        {
            "question": "Do all activities complete without deadlock?",
            "type": "validation"
        }
    ]
}),
    ("Given potential failures in activity2, what is the maximum number of products that can be produced in 120 units of time?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "What is the maximum number of products that can be produced in 120 units of time?",
            "type": "simulation"
        },
        {
            "question": "What are the potential failures in activity2?",
            "type": "failure"
        }
    ]
}),
    ("Simulate the process for 250 pieces and validate that q4 is reached at least once.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the process for 250 pieces.",
            "type": "simulation"
        },
        {
            "question": "Is state q4 reached at least once?",
            "type": "validation"
        }
    ]
}),
    ("Will the system remain operational if activity1 fails temporarily? How long will it take to produce 50 pieces?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long will it take to produce 50 pieces?",
            "type": "simulation"
        },
        {
            "question": "What is the effect of a temporary failure in activity1?",
            "type": "failure"
        }
    ]
}),
    ("Estimate how many products can be produced in 70 units of time considering failures in activity3.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How many products can be produced in 70 units of time?",
            "type": "simulation"
        },
        {
            "question": "What failures may occur in activity3?",
            "type": "failure"
        }
    ]
}),
    ("Simulate 400 time units and verify whether q5 is ever reached. Check if the process remains deadlock free.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for 400 time units.",
            "type": "simulation"
        },
        {
            "question": "Is state q5 ever reached?",
            "type": "validation"
        },
        {
            "question": "Is the process deadlock free?",
            "type": "validation"
        }
    ]
}),
    ("Can 80 pieces be produced within 60 time units when activity2 is subject to failure?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Can 80 pieces be produced within 60 time units?",
            "type": "simulation"
        },
        {
            "question": "What failures affect activity2?",
            "type": "failure"
        }
    ]
}),
    ("How much time is required to produce 100 pieces assuming maintenance on activity4? Validate if q1 stays reachable.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How much time is required to produce 100 pieces?",
            "type": "simulation"
        },
        {
            "question": "What is the effect of maintenance on activity4?",
            "type": "failure"
        },
        {
            "question": "Is state q1 reachable during production?",
            "type": "validation"
        }
    ]
}),
    ("Simulate the system for 500 time units and verify that there are no deadlocks.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for 500 time units.",
            "type": "simulation"
        },
        {
            "question": "Are there any deadlocks in the process?",
            "type": "validation"
        }
    ]
}),
    ("Is it possible to produce 150 pieces in 90 time units given that activity5 may fail? Validate that q2 remains reachable.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Is it possible to produce 150 pieces in 90 time units?",
            "type": "simulation"
        },
        {
            "question": "Check activity5's failure predictions.",
            "type": "failure"
        },
        {
            "question": "Is state q2 reachable?",
            "type": "validation"
        }
    ]
}),
    ("Run a simulation with 200 products and confirm that the system avoids deadlocks and eventually reaches q4.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Run a simulation with 200 products.",
            "type": "simulation"
        },
        {
            "question": "Does the system avoid deadlocks?",
            "type": "validation"
        },
        {
            "question": "Is state q4 eventually reached?",
            "type": "validation"
        }
    ]
}),
    ("If activity3 experiences failures, how long does it take to complete 60 pieces?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long does it take to complete 60 pieces?",
            "type": "simulation"
        },
        {
            "question": "What happens if activity3 experiences failures?",
            "type": "failure"
        }
    ]
}),
    ("Can the system produce 120 products in 100 units of time while keeping all reachable states deadlock free?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Can the system produce 120 products in 100 units of time?",
            "type": "simulation"
        },
        {
            "question": "Are all reachable states deadlock free?",
            "type": "validation"
        }
    ]
})
]




def generate_hybrid_questions(hybrid_questions, number_samples=10):
    samples = random.choices(hybrid_questions, k=number_samples)
    questions = []
    for s,a in samples:
        questions.append([s, a])

    write_samples_to_csv('hybrid', questions)


def main_routing(simulation_csv, verification_csv, unrelated_csv, factory_info_csv, process_mining_csv, hybrid_csv, output_csv, sim_proportions, total_samples=15):
    sim_df = pd.read_csv(simulation_csv)
    ver_df = pd.read_csv(verification_csv)
    unrel_df = pd.read_csv(unrelated_csv)
    factinf_df = pd.read_csv(factory_info_csv)
    pm_df = pd.read_csv(process_mining_csv)
    hybrid_df = pd.read_csv(hybrid_csv)

    sim_samples_count = total_samples // 6
    ver_samples_count = total_samples // 6
    factinf_samples_count = total_samples // 6
    pm_samples_count = total_samples // 6
    hybrid_samples_count = total_samples // 6

    refuse_samples_count = total_samples - sim_samples_count - ver_samples_count - factinf_samples_count - pm_samples_count - hybrid_samples_count
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
    unrel_samples["answer"] = "conversational gateway"
    factinf_samples = factinf_df.sample(factinf_samples_count, random_state=42)
    factinf_samples["answer"] = "factory_info"
    pm_samples = pm_df.sample(pm_samples_count, random_state=42)
    pm_samples["answer"] = "process_mining"
    hybrid_samples = hybrid_df.sample(hybrid_samples_count, random_state=42)
    hybrid_samples["answer"] = "hybrid"
    combined_samples = pd.concat([sim_samples, ver_samples, unrel_samples, factinf_samples, pm_samples, hybrid_samples]).sample(frac=1, random_state=42).reset_index(drop=True)
    
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
    generate_factory_info_questions(factory_info_questions)
    generate_process_mining_questions(process_mining_questions)
    generate_hybrid_questions(hybrid_questions)

    sim_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'simulation.csv')
    ver_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'verification.csv')
    unrel_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'unrelated.csv')
    factinf_df = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'factory_info.csv')
    pm_df = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'process_mining.csv')
    hybrid_df = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'hybrid.csv')
    routing_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'routing.csv')
    main_routing(sim_csv, ver_csv, unrel_csv, factinf_df, pm_df, hybrid_df, routing_csv, tasks_proportions)

    