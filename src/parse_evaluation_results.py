#!/usr/bin/env python3
"""
Script to parse evaluation results from tests/evaluation folder and generate a CSV.
Reads all results_*.txt files and extracts metrics into a CSV file.
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime


def parse_time_to_hours(time_str):
    """Convert time string to hours (handles formats like '2.06 hours')."""
    match = re.search(r'([\d.]+)\s*hour', time_str)
    if match:
        return float(match.group(1))
    return None


def parse_results_file(file_path):
    """Parse a single results file and extract metrics."""
    data = {
        'filename': os.path.basename(file_path),
        'timestamp': None,
        'llm_id_gateway': None,
        'llm_id_simulation': None,
        'llm_id_verification': None,
        'max_generated_tokens': None,
        'interaction_modality': None,
        'accuracy': None,
        'precision': None,
        'recall': None,
        'f1_score': None,
        'mcc': None,
        'auc': None,
        'elapsed_hours': None
    }
    
    # Extract timestamp from filename (results_YYYY-MM-DD_HH-MM-SS.txt)
    timestamp_match = re.search(r'results_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.txt', data['filename'])
    if timestamp_match:
        data['timestamp'] = timestamp_match.group(1).replace('_', ' ')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse run information
        llm_gateway_match = re.search(r'LLM ID Gateway:\s*(.+)', content)
        if llm_gateway_match:
            data['llm_id_gateway'] = llm_gateway_match.group(1).strip()
        
        llm_simulation_match = re.search(r'LLM ID Simulation:\s*(.+)', content)
        if llm_simulation_match:
            data['llm_id_simulation'] = llm_simulation_match.group(1).strip()
        
        llm_verification_match = re.search(r'LLM ID Verification:\s*(.+)', content)
        if llm_verification_match:
            data['llm_id_verification'] = llm_verification_match.group(1).strip()
        
        max_tokens_match = re.search(r'Max Generated Tokens LLM:\s*(\d+)', content)
        if max_tokens_match:
            data['max_generated_tokens'] = int(max_tokens_match.group(1))
        
        interaction_match = re.search(r'Interaction Modality:\s*(.+)', content)
        if interaction_match:
            data['interaction_modality'] = interaction_match.group(1).strip()
        
        # Parse metrics
        accuracy_match = re.search(r'Accuracy:\s*([\d.]+)', content)
        if accuracy_match:
            data['accuracy'] = float(accuracy_match.group(1))
        
        precision_match = re.search(r'Precision:\s*([\d.]+)', content)
        if precision_match:
            data['precision'] = float(precision_match.group(1))
        
        recall_match = re.search(r'Recall:\s*([\d.]+)', content)
        if recall_match:
            data['recall'] = float(recall_match.group(1))
        
        f1_match = re.search(r'F1-score:\s*([\d.]+)', content)
        if f1_match:
            data['f1_score'] = float(f1_match.group(1))
        
        mcc_match = re.search(r'Matthews Corr\. Coeff\. \(MCC\):\s*([\d.-]+)', content)
        if mcc_match:
            data['mcc'] = float(mcc_match.group(1))
        
        auc_match = re.search(r'Area Under Curve \(AUC\):\s*([\d.]+)', content)
        if auc_match:
            data['auc'] = float(auc_match.group(1))
        
        elapsed_match = re.search(r'Elapsed:\s*(.+)', content)
        if elapsed_match:
            data['elapsed_hours'] = parse_time_to_hours(elapsed_match.group(1))
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return data


def main():
    """Main function to parse all results files and generate CSV."""
    # Define paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    evaluation_dir = workspace_root / "tests" / "evaluation"
    
    # Find all results files
    results_files = list(evaluation_dir.glob("results_*.txt"))
    
    if not results_files:
        print(f"No results files found in {evaluation_dir}")
        print("Looking for files matching pattern: results_*.txt")
        return
    
    print(f"Found {len(results_files)} results file(s)")
    
    # Parse all files
    all_data = []
    for file_path in sorted(results_files):
        print(f"Parsing: {file_path.name}")
        data = parse_results_file(file_path)
        all_data.append(data)
    
    # Generate CSV
    output_file = evaluation_dir / f"evaluation_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    
    fieldnames = [
        'filename',
        'timestamp',
        'llm_id_gateway',
        'llm_id_simulation',
        'llm_id_verification',
        'max_generated_tokens',
        'interaction_modality',
        'accuracy',
        'precision',
        'recall',
        'f1_score',
        'mcc',
        'auc',
        'elapsed_hours'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"\nCSV file generated: {output_file}")
    print(f"Total records: {len(all_data)}")
    
    # Print summary
    if all_data:
        print("\n" + "="*80)
        print("Summary Statistics:")
        print("="*80)
        
        # Calculate averages for numeric fields
        numeric_fields = ['accuracy', 'precision', 'recall', 'f1_score', 'mcc', 'auc', 'elapsed_hours']
        for field in numeric_fields:
            values = [d[field] for d in all_data if d[field] is not None]
            if values:
                avg = sum(values) / len(values)
                print(f"{field.replace('_', ' ').title()}: {avg:.4f} (avg of {len(values)} values)")


if __name__ == "__main__":
    main()
