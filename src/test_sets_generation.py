import csv
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import random
import sys

import simulation_interface as fa
from simulation import FactorySimulator
import uppaal_interface as up


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
    for _ in range(300):
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
        answer["query_nl"] = question
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
    for _ in range(300):
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
    ("What is the mean processing time at {activity}?", {
    "task": "factory_info",
    "query_nl": "What is the mean processing time at {activity}?",
    "response": ""
}),
    ("What is the standard deviation of the processing time at {activity}?", {
    "task": "factory_info",
    "query_nl": "What is the standard deviation of the processing time at {activity}?",
    "response": ""
}),
    ("What are the possible next activities after {activity}?", {
    "task": "factory_info",
    "query_nl": "What are the possible next activities after {activity}?",
    "response": ""
}),
    ("What is the probability of routing from {activity1} to {activity2}?", {
    "task": "factory_info",
    "query_nl": "What is the probability of routing from {activity1} to {activity2}?",
    "response": ""
}),
    ("What is the inter-arrival time of products?", {
    "task": "factory_info",
    "query_nl": "What is the inter-arrival time of products?",
    "response": ""
}),
    ("What is the mean transfer time from {activity1} to {activity2}?", {
    "task": "factory_info",
    "query_nl": "What is the mean transfer time from {activity1} to {activity2}?",
    "response": ""
}),
    ("What is the capacity of {activity}?", {
    "task": "factory_info",
    "query_nl": "What is the capacity of {activity}?",
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
    ("What is the mean transfer time between {activity1} and {activity2}?", {
    "task": "factory_info",
    "query_nl": "What is the mean transfer time between {activity1} and {activity2}?",
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


def generate_factory_info_questions(factory_info_questions, number_samples=300):
    samples = []
    for _ in range(number_samples):
        s, a = random.choice(factory_info_questions)
        activity = random.choice(activities)
        activity1 = random.choice(activities)
        activity2 = random.choice(activities)
        while activity1 == activity2:
            activity2 = random.choice(activities)
        
        s = s.format(activity=activity, activity1=activity1, activity2=activity2)
        a = a.copy()
        query_nl = a["query_nl"]
        a["query_nl"] = query_nl.format(activity=f"{activity}", activity1=f"{activity1}", activity2=f"{activity2}")
        samples.append([s, a])

    write_samples_to_csv('factory_info', samples)

process_mining_questions = [
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
    ("What are the top {k} most frequent variants in the log?", {
    "task": "performance_analysis",
    "metric": "top_variants",
    "k": "{k}"
}),
    ("Can you list the start and end activities for the process?", {
    "task": "performance_analysis",
    "metric": "start_end_activities"
}),
    ("Can you filter the log between {year}-{month}-{day}T{hour}:{minute}:{second} and {year1}-{month1}-{day1}T{hour1}:{minute1}:{second1}?", {
    "task": "filter_by_time_range",
    "start_date": "{year}-{month}-{day}T{hour}:{minute}:{second}", 
    "end_date": "{year1}-{month1}-{day1}T{hour1}:{minute1}:{second1}"
}),
    ("Can you show the discovered Petri net model?", {
    "task": "process_discovery"
}),
    ("Can you show me the top {k} variants that are present in the event log?", {
    "task": "performance_analysis",
    "metric": "top_variants",
    "k": "{k}"
})
]

k_range = range(1, 10, 1)
year_range = range(2015, 2025, 1)
month_range = range(1, 12, 1)
day_range = range(1, 31, 1)
hour_range = range(0, 24, 1)
minute_range = range(0, 59, 1)
second_range = range(0, 59, 1)
def generate_process_mining_questions(process_mining_questions, number_samples=300):
    samples = []
    for _ in range(number_samples):
        s, a = random.choice(process_mining_questions)
        k = random.choice(k_range)
        year = random.choice(year_range)
        month = random.choice(month_range)
        day = random.choice(day_range)
        hour = random.choice(hour_range)
        minute = random.choice(minute_range)
        second = random.choice(second_range)
        
        try:
            start_dt = datetime(year, month, day, hour, minute, second)
        except ValueError:
            continue

        delta = timedelta(
            days=random.randint(0, 3),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(1, 59)
        )
        end_dt = start_dt + delta

        fmt = lambda d: d.strftime("%Y-%m-%dT%H:%M:%S")

        s = s.format(
            k=k,
            year=start_dt.year, month=f"{start_dt.month:02d}", day=f"{start_dt.day:02d}",
            hour=f"{start_dt.hour:02d}", minute=f"{start_dt.minute:02d}", second=f"{start_dt.second:02d}",
            year1=end_dt.year, month1=f"{end_dt.month:02d}", day1=f"{end_dt.day:02d}",
            hour1=f"{end_dt.hour:02d}", minute1=f"{end_dt.minute:02d}", second1=f"{end_dt.second:02d}"
        )
        
        a = a.copy()
        if "k" in a:
            a["k"] = a["k"].format(k=k)
            a["k"] = int(a["k"])
        if "start_date" in a and "end_date" in a:
            a["start_date"] = fmt(start_dt)
            a["end_date"] = fmt(end_dt)

        samples.append([s, a])

    write_samples_to_csv('process_mining', samples)

hybrid_questions = hybrid_questions = [
    ("How much time is needed to produce {pieces} pieces given that {activity} might fail? Also, verify if the system avoids deadlocks during production.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How much time is needed to produce {pieces} pieces?",
            "type": "simulation"
        },
        {
            "question": "What are the failure patterns of {activity}?",
            "type": "failure"
        },
        {
            "question": "Is the system deadlock free during production?",
            "type": "validation"
        }
    ]
}),
    ("Can {pieces} products be made within {time} units of time? Validate whether state {state} is reachable and check {activity} failure likelihood.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Can {pieces} products be made within {time} units of time?",
            "type": "simulation"
        },
        {
            "question": "What is the failure likelihood of {activity}?",
            "type": "failure"
        },
        {
            "question": "Is state {state} reachable?",
            "type": "validation"
        }
    ]
}),
    ("Will the process reach state {state}? How long does it take to produce {pieces} units considering possible degradation on {activity}?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long does it take to produce {pieces} units?",
            "type": "simulation"
        },
        {
            "question": "What are the degradation effects on {activity}?",
            "type": "failure"
        },
        {
            "question": "Will the process reach state {state}?",
            "type": "validation"
        }
    ]
}),
    ("Simulate the system for {pieces} products and verify if {state} is eventually reached. Then confirm there are no deadlocks in the process.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for {pieces} products.",
            "type": "simulation"
        },
        {
            "question": "Is state {state} eventually reached?",
            "type": "validation"
        },
        {
            "question": "Is the process free of deadlocks?",
            "type": "validation"
        }
    ]
}),
    ("Considering preventive maintenance on {activity}, how many pieces can be produced in {time} units of time?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How many pieces can be produced in {time} units of time?",
            "type": "simulation"
        },
        {
            "question": "What are the maintenance effects on {activity}?",
            "type": "failure"
        }
    ]
}),
    ("Is state {state} reachable during production? Estimate the time needed to manufacture {pieces} pieces assuming {activity} failure.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Estimate the time needed to manufacture {pieces} pieces.",
            "type": "simulation"
        },
        {
            "question": "Check {activity}'s failure predictions.",
            "type": "failure"
        },
        {
            "question": "Is state {state} reachable during production?",
            "type": "validation"
        }
    ]
}),
    ("How long does it take to produce {pieces} pieces when {activity} is under maintenance? Also, check whether {state} remains reachable.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long does it take to produce {pieces} pieces?",
            "type": "simulation"
        },
        {
            "question": "What are the effects of maintenance on {activity}?",
            "type": "failure"
        },
        {
            "question": "Is state {state} reachable during production?",
            "type": "validation"
        }
    ]
}),
    ("Can you simulate {time} time units and verify if all activities eventually complete without entering a deadlock state?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for {time} time units.",
            "type": "simulation"
        },
        {
            "question": "Do all activities complete without deadlock?",
            "type": "validation"
        }
    ]
}),
    ("Given potential failures in {activity}, what is the maximum number of products that can be produced in {time} units of time?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "What is the maximum number of products that can be produced in {time} units of time?",
            "type": "simulation"
        },
        {
            "question": "What are the potential failures in {activity}?",
            "type": "failure"
        }
    ]
}),
    ("Simulate the process for {pieces} pieces and validate that {state} is reached at least once.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the process for {pieces} pieces.",
            "type": "simulation"
        },
        {
            "question": "Is state {state} reached at least once?",
            "type": "validation"
        }
    ]
}),
    ("What happens if {activity} fails temporarily? How long will it take to produce {pieces} pieces?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long will it take to produce {pieces} pieces?",
            "type": "simulation"
        },
        {
            "question": "What is the effect of a temporary failure in {activity}?",
            "type": "failure"
        }
    ]
}),
    ("Estimate how many products can be produced in {time} units of time considering failures in {activity}.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How many products can be produced in {time} units of time?",
            "type": "simulation"
        },
        {
            "question": "What failures may occur in {activity}?",
            "type": "failure"
        }
    ]
}),
    ("Simulate {time} time units and verify whether {state} is ever reached. Check if the process remains deadlock free.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for {time} time units.",
            "type": "simulation"
        },
        {
            "question": "Is state {state} ever reached?",
            "type": "validation"
        },
        {
            "question": "Is the process deadlock free?",
            "type": "validation"
        }
    ]
}),
    ("Can {pieces} pieces be produced within {time} time units when {activity} is subject to failure?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Can {pieces} pieces be produced within {time} time units?",
            "type": "simulation"
        },
        {
            "question": "What failures affect {activity}?",
            "type": "failure"
        }
    ]
}),
    ("How much time is required to produce {pieces} pieces assuming maintenance on {activity}? Validate if {state} stays reachable.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How much time is required to produce {pieces} pieces?",
            "type": "simulation"
        },
        {
            "question": "What is the effect of maintenance on {activity}?",
            "type": "failure"
        },
        {
            "question": "Is state {state} reachable during production?",
            "type": "validation"
        }
    ]
}),
    ("Simulate the system for {time} time units and verify that there are no deadlocks.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Simulate the system for {time} time units.",
            "type": "simulation"
        },
        {
            "question": "Are there any deadlocks in the process?",
            "type": "validation"
        }
    ]
}),
    ("Is it possible to produce {pieces} pieces in {time} time units given that {activity} may fail? Validate that {state} remains reachable.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Is it possible to produce {pieces} pieces in {time} time units?",
            "type": "simulation"
        },
        {
            "question": "Check {activity}'s failure predictions.",
            "type": "failure"
        },
        {
            "question": "Is state {state} reachable?",
            "type": "validation"
        }
    ]
}),
    ("Run a simulation with {pieces} products and confirm that the system avoids deadlocks and eventually reaches {state}.", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Run a simulation with {pieces} products.",
            "type": "simulation"
        },
        {
            "question": "Does the system avoid deadlocks?",
            "type": "validation"
        },
        {
            "question": "Is state {state} eventually reached?",
            "type": "validation"
        }
    ]
}),
    ("If {activity} experiences failures, how long does it take to complete {pieces} pieces?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "How long does it take to complete {pieces} pieces?",
            "type": "simulation"
        },
        {
            "question": "What happens if {activity} experiences failures?",
            "type": "failure"
        }
    ]
}),
    ("Can the system produce {pieces} products in {time} units of time while keeping all reachable states deadlock free?", {
    "task": "hybrid",
    "pddl_problem": "",
    "questions": [
        {
            "question": "Can the system produce {pieces} products in {time} units of time?",
            "type": "simulation"
        },
        {
            "question": "Are all reachable states deadlock free?",
            "type": "validation"
        }
    ]
})
]




def generate_hybrid_questions(hybrid_questions, number_samples=300):
    samples = []
    for _ in range(number_samples):
        s, a = random.choice(hybrid_questions)
        pieces = random.choice(pieces_range)
        time = random.choice(time_range_sim)
        activity = random.choice(activities)
        state = random.choice(states_verification)

        s = s.format(pieces=pieces, time=time, activity=activity, state=state)
        a = a.copy()
        for q in a["questions"]:
            q["question"] = q["question"].format(
                pieces=pieces,
                time=time,
                activity=activity,
                state=state
            )
        
        samples.append([s, a])

    write_samples_to_csv('hybrid', samples)


def main_routing(simulation_csv, verification_csv, unrelated_csv, factory_info_csv, process_mining_csv, hybrid_csv, output_csv, sim_proportions, total_samples=300):
    sim_df = pd.read_csv(simulation_csv)
    ver_df = pd.read_csv(verification_csv)
    unrel_df = pd.read_csv(unrelated_csv)
    factinf_df = pd.read_csv(factory_info_csv)
    pm_df = pd.read_csv(process_mining_csv)
    hybrid_df = pd.read_csv(hybrid_csv)

    num_categories = 6
    base_samples_per_cat = total_samples // num_categories
    remaining_samples = total_samples % num_categories
    counts = [base_samples_per_cat] * num_categories
    for i in range(remaining_samples):
        counts[i] += 1

    sim_samples_count = counts[0]
    ver_samples_count = counts[1]
    unrel_samples_count = counts[2]
    factinf_samples_count = counts[3]
    pm_samples_count = counts[4]
    hybrid_samples_count = counts[5]
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
    unrel_samples = unrel_df.sample(unrel_samples_count, random_state=42)
    unrel_samples["answer"] = "conversational_gateway"
    factinf_samples = factinf_df.sample(factinf_samples_count, random_state=42)
    factinf_samples["answer"] = "factory_info"
    pm_samples = pm_df.sample(pm_samples_count, random_state=42)
    pm_samples["answer"] = "process_mining"
    hybrid_samples = hybrid_df.sample(hybrid_samples_count, random_state=42)
    hybrid_samples["answer"] = "hybrid"
    combined_samples = pd.concat([sim_samples, ver_samples, unrel_samples, factinf_samples, pm_samples, hybrid_samples]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    combined_samples.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL)
    print(f"Generated mixed CSV with {len(combined_samples)} samples and saved to {output_csv}")
    print("Sample distribution per category:")
    print(combined_samples['answer'].value_counts())


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


def generate_answers_dataset(num_simulation=50, num_verification=50):
    sys.path.append(os.path.dirname(__file__))
    sim_csv_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'simulation.csv')
    ver_csv_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'verification.csv')
    sim_df = pd.read_csv(sim_csv_path)
    ver_df = pd.read_csv(ver_csv_path)
    sim_sample_size = min(int(num_simulation * 1.5), len(sim_df))
    sim_sample = sim_df.sample(n=sim_sample_size, random_state=42)
    ver_sample = ver_df.sample(n=min(num_verification, len(ver_df)), random_state=42)
    results = []
    
    print(f"Processing {len(sim_sample)} simulation questions (targeting {num_simulation} numeric results)...")
    for idx, row in sim_sample.iterrows():
        question = row['question']
        answer_json = json.loads(row['answer'])
        
        try:
            task = answer_json.get('task')
            simulation_time = answer_json.get('simulation_time')
            target_pieces = answer_json.get('target_pieces')
            answer_value = None
            
            if task == 'sim_with_time' and simulation_time:
                sim = FactorySimulator(simulation_time=int(simulation_time))
                sim.run()
                stats = sim.get_statistics()
                
                if 'pieces' in question.lower() or 'produced' in question.lower():
                    answer_value = stats['total_pieces_produced']
                elif 'processing time' in question.lower():
                    answer_value = round(stats['total_mean_processing_time'], 2)
                elif 'waiting time' in question.lower():
                    answer_value = round(stats['total_mean_waiting_time'], 2)
                elif 'transfer time' in question.lower():
                    answer_value = round(stats['total_mean_transfer_time'], 2)
                else:
                    answer_value = stats['total_pieces_produced']
                    
            elif task == 'sim_with_number_products' and target_pieces:
                sim = FactorySimulator()
                sim.compute_batch_production_time(int(target_pieces))
                stats = sim.get_statistics()
                
                if 'time' in question.lower() and 'needed' in question.lower():
                    answer_value = round(stats['total_execution_time'], 2)
                elif 'processing time' in question.lower():
                    answer_value = round(stats['total_mean_processing_time'], 2)
                elif 'waiting time' in question.lower():
                    answer_value = round(stats['total_mean_waiting_time'], 2)
                elif 'transfer time' in question.lower():
                    answer_value = round(stats['total_mean_transfer_time'], 2)
                else:
                    answer_value = round(stats['total_execution_time'], 2)
                    
            elif task == 'event_prediction':
                continue
            
            if answer_value is not None:
                results.append([question, 'simulation', answer_value])
                print(f"   Processed: {question[:60]}... -> {answer_value}")
                
                if sum(1 for r in results if r[1] == 'simulation') >= num_simulation:
                    break
            
        except Exception as e:
            print(f"   Error processing simulation question: {question[:60]}... -> {str(e)}")
            continue
    
    print(f"\nProcessing {len(ver_sample)} verification questions...")
    for idx, row in ver_sample.iterrows():
        question = row['question']
        answer_json = json.loads(row['answer'])
        
        try:
            uppaal_query = answer_json.get('uppaal_query')
            
            if uppaal_query:
                result = up.execute_query(uppaal_query)
                answer_value = 'satisfied' in result.lower()
                
                results.append([question, 'verification', answer_value])
                print(f"  ✓ Processed: {question[:60]}... -> {answer_value}")
            
        except Exception as e:
            print(f"  ✗ Error processing verification question: {question[:60]}... -> {str(e)}")
            continue
    
    output_path = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'answers-dataset.csv')
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['question', 'type', 'answer'])
        for row in results:
            writer.writerow(row)
    
    print(f"\n✓ Generated {len(results)} samples and saved to {output_path}")
    print(f"  - Simulation questions: {sum(1 for r in results if r[1] == 'simulation')}")
    print(f"  - Verification questions: {sum(1 for r in results if r[1] == 'verification')}")
    
    return output_path


if __name__ == "__main__":
    main_simulation()
    main_verification()
    generate_unrelated_questions(unrelated_questions)
    generate_factory_info_questions(factory_info_questions)
    generate_process_mining_questions(process_mining_questions)
    generate_hybrid_questions(hybrid_questions)
    generate_answers_dataset(num_simulation=50, num_verification=50)

    sim_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'simulation.csv')
    ver_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'verification.csv')
    unrel_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'unrelated.csv')
    factinf_df = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'factory_info.csv')
    pm_df = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'process_mining.csv')
    hybrid_df = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'hybrid.csv')
    routing_csv = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_sets', 'routing.csv')
    main_routing(sim_csv, ver_csv, unrel_csv, factinf_df, pm_df, hybrid_df, routing_csv, tasks_proportions)

    