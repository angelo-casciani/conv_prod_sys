import subprocess
import re
import os
from utility import extract_json

DOMAIN_PATH = os.path.join(os.path.dirname(__file__), 'pddl', 'domain.pddl')
PLANNER_PATH = os.path.join(os.path.dirname(__file__), 'pddl', 'downward', "fast-downward.py")
PROBLEM_PATH = os.path.join(os.path.dirname(__file__), 'pddl', 'problem.pddl')
if DOMAIN_PATH and PLANNER_PATH and PROBLEM_PATH:
    print("Domain, planner and problem paths are set.\n")
    print(f"Domain path: {DOMAIN_PATH},\nPlanner path: {PLANNER_PATH}, \nProblem path: {PROBLEM_PATH}\n")
def run_planner(problem):
    
    cmd = ['python3',
           PLANNER_PATH, 
           DOMAIN_PATH,
           problem,
           '--search',
           'lazy_greedy([ff()], preferred=[ff()])'
           ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)

    if process.returncode != 0:
        raise RuntimeError(f"Planner failed with error {process.stderr}")

    output = process.stdout
    
    plan = extract_plan(output)
    print(plan)
    return plan



def extract_plan(_plan):
    plan = []
    for line in _plan.splitlines():
        line = line.strip()
        if line.endswith(")") and "(" in line:
            action = line[:line.rfind("(")].strip()
            plan.append(action)
    return plan

            
try:
    plan = run_planner()
    print("Piano generato:")
    for i, action in enumerate(plan):
        print(f"{i}: {action}")
except Exception as e:
    print(e)