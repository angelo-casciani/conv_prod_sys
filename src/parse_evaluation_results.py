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
from collections import defaultdict

import matplotlib.pyplot as plt


def parse_time_to_hours(time_str):
    """Convert time string to hours (handles formats like '2.06 hours')."""
    match = re.search(r'([\d.]+)\s*hour', time_str)
    if match:
        return float(match.group(1))
    return None


def parse_results_file(file_path):
    """Parse a single results file and extract metrics."""
    data = {
        'llm_id': None,
        'interaction_modality': None,
        'accuracy': None,
        'precision': None,
        'recall': None,
        'f1_score': None,
        'elapsed_hours': None
    }
    
    # Temporary storage for all LLM IDs
    llm_gateway = None
    llm_simulation = None
    llm_verification = None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse run information
        llm_gateway_match = re.search(r'LLM ID Gateway:\s*(.+)', content)
        if llm_gateway_match:
            llm_gateway = llm_gateway_match.group(1).strip()
        
        llm_simulation_match = re.search(r'LLM ID Simulation:\s*(.+)', content)
        if llm_simulation_match:
            llm_simulation = llm_simulation_match.group(1).strip()
        
        llm_verification_match = re.search(r'LLM ID Verification:\s*(.+)', content)
        if llm_verification_match:
            llm_verification = llm_verification_match.group(1).strip()
        
        interaction_match = re.search(r'Interaction Modality:\s*(.+)', content)
        if interaction_match:
            data['interaction_modality'] = interaction_match.group(1).strip()
            
            # Determine which LLM to use based on interaction modality
            modality = data['interaction_modality'].lower()
            if 'simulation' in modality:
                data['llm_id'] = llm_simulation
            elif 'verification' in modality:
                data['llm_id'] = llm_verification
            else:  # routing, hybrid, factory_info, process_mining
                data['llm_id'] = llm_gateway
        
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
        
        elapsed_match = re.search(r'Elapsed:\s*(.+)', content)
        if elapsed_match:
            data['elapsed_hours'] = parse_time_to_hours(elapsed_match.group(1))
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return data


def plot_accuracy_distributions(all_data, evaluation_dir, timestamp):
    """Generate two box plots: few-shot and zero-shot accuracy by LLM."""
    valid_rows = [
        row for row in all_data
        if row.get('accuracy') is not None
        and row.get('interaction_modality')
        and row.get('llm_id')
    ]

    if not valid_rows:
        print("No valid rows found to plot accuracy distributions.")
        return []

    generated_plots = []

    # Define the desired model order
    model_order = [
        'Meta-Llama-3-8B',
        'Llama-3.1-8B',
        'Llama-3.2-1B',
        'Llama-3.2-3B',
        'Mistral-7B-Instruct-v0.2',
        'Mistral-7B-Instruct-v0.3',
        'Mistral-Nemo',
        'Ministral-8B',
        'Qwen2.5-7B',
        'gemma-2-9b',
        'phi-4',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gpt-5.1',
    ]

    def get_model_order_key(model_name):
        """Return the index of the model in the desired order."""
        model_name_lower = model_name.lower()
        for i, pattern in enumerate(model_order):
            if pattern.lower() in model_name_lower:
                return i
        return len(model_order)

    split_to_llm_values = {
        'fewshot': defaultdict(list),
        'zeroshot': defaultdict(list)
    }

    for row in valid_rows:
        modality = row['interaction_modality'].lower()
        split = 'zeroshot' if 'zeroshot' in modality else 'fewshot'
        split_to_llm_values[split][row['llm_id']].append(row['accuracy'])

    for split in ['fewshot', 'zeroshot']:
        llm_groups = split_to_llm_values[split]
        if not llm_groups:
            continue

        # Sort by the desired model order
        llm_labels = sorted(llm_groups.keys(), key=get_model_order_key)
        llm_values = [llm_groups[label] for label in llm_labels]

        fig, ax = plt.subplots(figsize=(max(9, len(llm_labels) * 0.9), 6))
        ax.boxplot(llm_values, patch_artist=True)
        ax.set_xlabel('Language model', fontsize=14)
        ax.set_ylabel('Accuracy', fontsize=14)
        ax.set_ylim(0.0, 1.05)
        ax.set_xticks(range(1, len(llm_labels) + 1))
        ax.set_xticklabels(llm_labels, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        fig.tight_layout()

        plot_path = evaluation_dir / f"accuracy_boxplot_{split}_{timestamp}.pdf"
        fig.savefig(plot_path)
        plt.close(fig)
        generated_plots.append(plot_path)

    return generated_plots


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
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = evaluation_dir / f"evaluation_summary_{timestamp}.csv"
    
    fieldnames = [
        'llm_id',
        'interaction_modality',
        'accuracy',
        'precision',
        'recall',
        'f1_score',
        'elapsed_hours'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f"\nCSV file generated: {output_file}")
    print(f"Total records: {len(all_data)}")

    generated_plots = plot_accuracy_distributions(all_data, evaluation_dir, timestamp)
    if generated_plots:
        print("\nGenerated accuracy distribution plots:")
        for plot_path in generated_plots:
            print(f"- {plot_path}")
    
    # Print summary
    if all_data:
        print("\n" + "="*80)
        print("Summary Statistics:")
        print("="*80)
        
        # Calculate averages for numeric fields
        numeric_fields = ['accuracy', 'precision', 'recall', 'f1_score', 'elapsed_hours']
        for field in numeric_fields:
            values = [d[field] for d in all_data if d[field] is not None]
            if values:
                avg = sum(values) / len(values)
                print(f"{field.replace('_', ' ').title()}: {avg:.4f} (avg of {len(values)} values)")


if __name__ == "__main__":
    main()
