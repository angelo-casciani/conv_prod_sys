import pm4py
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
import tempfile
import os
from datetime import datetime
from extractor import Extractor

class ProcessMiningModule:
    def __init__(self):
        directory_path = os.path.join(os.path.dirname(__file__), '..', 'log')
        files = os.listdir(directory_path)
        files = [f for f in files if os.path.isfile(os.path.join(directory_path, f))]
        
        event_log_files = [f for f in files if f.endswith('.xes') or f.endswith('.csv')]
        if len(event_log_files) == 1:
            self.path_to_log = os.path.join(directory_path, event_log_files[0])
            self.extension = os.path.splitext(self.path_to_log)[1].lower()
            if ".xes" not in self.path_to_log and ".csv" not in self.path_to_log:
                raise ValueError(f"Unsupported file format: {self.extension}. Use '.csv' or '.xes'.")
        elif len(event_log_files) == 0:
            raise ValueError(f"No event log file (.xes or .csv) found in the {directory_path} directory.")
        else:
            raise ValueError(f"There is more than one event log file in the {directory_path} directory. Found: {', '.join(event_log_files)}")
        
        self.output_dir = "pmmOutputs"
        os.makedirs(self.output_dir, exist_ok=True) 
        

    def conversion_from_csv_to_xes(self):
        df = pd.read_csv(self.path_to_log)
        #print(df.head())
        CASE_ID_COL = "part_id"
        ACTIVITY_COL = "activity"
        TIMESTAMP_COL = "time"

        df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL])

        df = df.rename(columns={
            CASE_ID_COL: "case:concept:name",
            ACTIVITY_COL: "concept:name",
            TIMESTAMP_COL: "time:timestamp"
        })

        # if "lifecycle:transition" not in df.columns:
        #     df["lifecycle:transition"] = "complete"
        
        # if "org:resource" not in df.columns:
        #     df["org:resource"] = "nan"

        parameters = {
            "case_id_key": "case:concept:name",
            "activity_key": "concept:name",
            "timestamp_key": "time:timestamp",
            # "lifecycle:transition": "lifecycle:transition",
            # "org:resource": "org:resource"
        }

        

        event_log = log_converter.apply(df, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)

        with tempfile.NamedTemporaryFile(suffix=".xes", delete=False) as tmp:
            xes_exporter.apply(event_log, tmp.name)
            temp_path = tmp.name
        #print(event_log)
        return temp_path
    
    def load_log(self):
        if self.extension == ".csv":
            xes_path = self.conversion_from_csv_to_xes()
            log = pm4py.read_xes(xes_path)
        elif self.extension == ".xes":
            log = pm4py.read_xes(self.path_to_log)
        
        return log

    def save_net_image(self, net, initial_marking, final_marking, file_path="pmmOutputs/petri_net_"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(self.output_dir, f"petri_net_{timestamp}.png")
        pm4py.save_vis_petri_net(net, initial_marking, final_marking, file_path=file_path)
        return file_path

    def discovery_from_log(self, log):
        net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
        file_path = self.save_net_image(net, initial_marking, final_marking)
        return net, initial_marking, final_marking, file_path
    
    def discovery(self):
        log = self.load_log()
        return self.discovery_from_log(log)
    
    def view_petri_net(self, net, initial_marking, final_marking):
        pm4py.view_petri_net(net, initial_marking, final_marking, format="png")


    def conformal_checking(self, net, initial_marking, final_marking, log):
        check = pm4py.conformance.conformance_diagnostics_token_based_replay(log, net, initial_marking, final_marking)
        trace_is_fit = check[0]['trace_is_fit']
        trace_fitness = check[0]['trace_fitness']
        return trace_is_fit, trace_fitness

    def get_avg_throughput_time(self, log):
        case_durations = pm4py.stats.get_all_case_durations(log)
        if len(case_durations) == 0:
            return 0
        return sum(case_durations) / len(case_durations)

    def get_activity_frequencies(self, log):
        return pm4py.stats.get_event_attribute_values(log, "concept:name")

    def get_case_durations(self, log):
        return pm4py.stats.get_all_case_durations(log) 

    def get_process_variants(self, log, k=5):
        variants = pm4py.stats.get_variants(log)
        total_cases = sum(variants.values())

        #print(f"\nTOP {k} VARIANTS:")
        top_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)[:k]
        # for i, (variant_tuple, count) in enumerate(top_variants, 1):
        #     path = " → ".join(variant_tuple)
        #     percentage = round((count / total_cases) * 100, 2)
        #     print(f"{i}. {path} ({count} cases, {percentage}%)")
        
        return top_variants
    
    def get_start_end_activities(self, log):
        start_acts = pm4py.stats.get_start_activities(log)
        end_acts = pm4py.stats.get_end_activities(log)
        return start_acts, end_acts
    
    def filter_by_time_range(self, log, start_date, end_date):
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        if hasattr(start_date, 'to_pydatetime'):
            start_date = start_date.to_pydatetime()
        if hasattr(end_date, 'to_pydatetime'):
            end_date = end_date.to_pydatetime()
        
        filtered_log = pm4py.filtering.filter_time_range(log, start_date, end_date)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        output_path = os.path.join(self.output_dir, f"filtered_log_{start_str}_to_{end_str}_{timestamp}.xes")
        pm4py.write.write_xes(filtered_log, output_path)
        return output_path
    
    def get_resource_analysis(self, log):
        return pm4py.stats.get_event_attribute_values(log, "station_id")

    def filter_top_variants(self, log, k=5):
        return pm4py.filtering.filter_variants_top_k(log, k)
    
    def performance_analysis(self, log, metric, json_question=None):
        if metric == "throughput_time":
            result = self.get_avg_throughput_time(log)
            return {
                "metric": metric,
                "value": result,
                "interpretation": f"The average throughput time is {result:.2f} time units. This represents the mean time it takes for a case to complete from start to finish."
            }
        elif metric == "activity_frequency":
            result = self.get_activity_frequencies(log)
            total = sum(result.values())
            sorted_activities = sorted(result.items(), key=lambda x: x[1], reverse=True)
            top_activity = sorted_activities[0] if sorted_activities else None
            least_activity = sorted_activities[-1] if sorted_activities else None
            
            interpretation = f"Activity frequency analysis:\n"
            interpretation += f"- Total activity occurrences: {total}\n"
            if top_activity:
                interpretation += f"- Most frequent activity: '{top_activity[0]}' with {top_activity[1]} occurrences ({top_activity[1]/total*100:.1f}%)\n"
            if least_activity:
                interpretation += f"- Least frequent activity: '{least_activity[0]}' with {least_activity[1]} occurrences ({least_activity[1]/total*100:.1f}%)\n"
            interpretation += f"- Total unique activities: {len(result)}"
            
            return {
                "metric": metric,
                "data": result,
                "interpretation": interpretation
            }
        elif metric == "top_variants":
            k = json_question.get("k") if json_question else 5
            result = self.get_process_variants(log, k)
            variants = pm4py.stats.get_variants(log)
            total_cases = sum(variants.values())
            
            interpretation = f"Top {k} process variants analysis:\n"
            for i, (variant_tuple, count) in enumerate(result, 1):
                path = " → ".join(variant_tuple)
                percentage = round((count / total_cases) * 100, 2)
                interpretation += f"{i}. {path}\n   ({count} cases, {percentage}%)\n"
            
            interpretation += f"\nThese {k} variants represent {sum(v[1] for v in result)/total_cases*100:.1f}% of all cases."
            
            return {
                "metric": metric,
                "data": result,
                "interpretation": interpretation
            }
        elif metric == "start_end_activities":
            start_end = self.get_start_end_activities(log)
            start_acts, end_acts = start_end
            
            interpretation = f"Start and End Activities Analysis:\n\n"
            interpretation += f"Start Activities (entry points):\n"
            for act, freq in sorted(start_acts.items(), key=lambda x: x[1], reverse=True):
                interpretation += f"  - '{act}': {freq} cases\n"
            
            interpretation += f"\nEnd Activities (exit points):\n"
            for act, freq in sorted(end_acts.items(), key=lambda x: x[1], reverse=True):
                interpretation += f"  - '{act}': {freq} cases\n"
            
            interpretation += f"\nThe process has {len(start_acts)} entry point(s) and {len(end_acts)} exit point(s)."
            
            return {
                "metric": metric,
                "data": {"start_activities": start_acts, "end_activities": end_acts},
                "interpretation": interpretation
            }
        elif metric == "resource_analysis":
            result = self.get_resource_analysis(log)
            sorted_resources = sorted(result.items(), key=lambda x: x[1], reverse=True)
            most_used = sorted_resources[0] if sorted_resources else None
            least_used = sorted_resources[-1] if sorted_resources else None
            total_events = sum(result.values())
            avg_events = total_events / len(result) if result else 0
            
            interpretation = f"Resource Utilization Analysis:\n"
            interpretation += f"- Total events across all resources: {total_events}\n"
            interpretation += f"- Number of unique resources: {len(result)}\n"
            interpretation += f"- Average events per resource: {avg_events:.1f}\n\n"
            
            if most_used:
                interpretation += f"Most Utilized Resources:\n"
                for i, (resource, count) in enumerate(sorted_resources[:3], 1):
                    percentage = (count/total_events*100)
                    deviation = ((count - avg_events) / avg_events * 100) if avg_events > 0 else 0
                    interpretation += f"  {i}. '{resource}': {count} events ({percentage:.1f}%, {deviation:+.1f}% vs avg)\n"
            
            if least_used and len(sorted_resources) > 3:
                interpretation += f"\nLeast Utilized Resources:\n"
                for i, (resource, count) in enumerate(sorted_resources[-3:][::-1], 1):
                    percentage = (count/total_events*100)
                    deviation = ((count - avg_events) / avg_events * 100) if avg_events > 0 else 0
                    interpretation += f"  {i}. '{resource}': {count} events ({percentage:.1f}%, {deviation:+.1f}% vs avg)\n"
            
            # Check for potential bottlenecks or imbalances
            if most_used and least_used:
                ratio = most_used[1] / least_used[1] if least_used[1] > 0 else float('inf')
                if ratio > 3:
                    interpretation += f"\n⚠️  Significant imbalance detected: The most utilized resource handles {ratio:.1f}x more events than the least utilized."
            
            return {
                "metric": metric,
                "data": result,
                "interpretation": interpretation
            }
        else:
            raise ValueError(f"Unknown metric: {metric}") 
        
    def extract(self, failure=False):
        if self.extension != ".xes":
            xes_path = self.conversion_from_csv_to_xes()
        else:
            xes_path = self.path_to_log
        extractor = Extractor()
        _, _, _ = extractor.extract_model(xes_path=xes_path, failure=failure)

if __name__ == "__main__":
    pmm = ProcessMiningModule()
    pmm.extract()
    log = pmm.load_log()
    net, initial_marking, final_marking, file_path = pmm.discovery_from_log(log)
    print("\n\nPreparing the view of the Petri net....")
    pmm.view_petri_net(net, initial_marking, final_marking)
    trace_is_fit, trace_fitness = pmm.conformal_checking(net, initial_marking, final_marking, log)
    print("\n\nI'm doing the conformance checking...")
    if trace_is_fit and trace_fitness >= 0.65:
        print("\n\nThe model fits the trace :) !!!")
        print("\n\n**************************************")
    else:
        print("\n\n\nThe model does not fit the trace :( ...")

    avg_tt = pmm.get_avg_throughput_time(log)
    print(f"\nAverage throughput time: {avg_tt}")

    freqs = pmm.get_activity_frequencies(log)
    print("\nActivity frequencies:")
    for act, freq in freqs.items():
        print(f"{act}: {freq}")

    durations = pmm.get_case_durations(log)
    print("\nCase durations:", durations)

    pmm.get_process_variants(log)

    start_end = pmm.get_start_end_activities(log)
    print(f"\nStart activities with frequencies: {start_end[0]}. \nEnd activities with frequencies: {start_end[1]}")

    start_date = "2025-02-17T17:07:38.885199"
    end_date = "2025-02-17T17:16:12.689944"
    print(f"\nEvent log filtered between {start_date} and {end_date}:", pmm.filter_by_time_range(log, start_date, end_date))

    #print("\nResource analysis:", pmm.get_resource_analysis(log))

    k = 3
    print(f"\nEvent log filtered by top {k} variants:", pmm.filter_top_variants(log, k))
