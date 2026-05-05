import subprocess
import os

DOMAIN_PATH = os.path.join(os.path.dirname(__file__), 'pddl', 'domain.pddl')
PLANNER_PATH = os.path.join(os.path.dirname(__file__), 'downward', "fast-downward.py")
if DOMAIN_PATH and PLANNER_PATH:
    print("Domain and planner are set.\n")
    print(f"Domain path: {DOMAIN_PATH},\nPlanner path: {PLANNER_PATH}")
    
def run_planner(problem):
    
    cmd = ['python3',
           PLANNER_PATH, 
           DOMAIN_PATH,
           problem,
           '--search',
           'astar(blind())'
           ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)

    if process.returncode != 0:
        stdout_text = (process.stdout or "").strip()
        stderr_text = (process.stderr or "").strip()
        details = "\n".join([part for part in [stdout_text, stderr_text] if part])
        if not details:
            details = f"Planner returned non-zero exit code {process.returncode} with no stdout/stderr."
        raise RuntimeError(f"Planner failed (exit code {process.returncode}). Details: {details}")

    output = process.stdout    
    plan = extract_plan(output)

    return plan

def extract_plan(_plan):
    plan = []
    for line in _plan.splitlines():
        line = line.strip()
        if line.endswith(")") and "(" in line:
            action = line[:line.rfind("(")].strip()
            plan.append(action)
    return plan