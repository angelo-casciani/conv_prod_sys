import pm4py
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
import tempfile
import os

class ProcessMiningModule:
    def __init__(self, path_to_csv):
        self.path_to_csv = path_to_csv

    def conversion_from_csv_to_xes(self):
        df = pd.read_csv(self.path_to_csv)
        print(df.head())
        CASE_ID_COL = "part_id"
        ACTIVITY_COL = "activity"
        TIMESTAMP_COL = "time"

        df[TIMESTAMP_COL] = pd.to_datetime(df[TIMESTAMP_COL])

        df = df.rename(columns={
            "part_id": "case:concept:name",
            "activity": "concept:name",
            "time": "time:timestamp"
        })

        parameters = {
            "case_id_key": CASE_ID_COL,
            "activity_key": ACTIVITY_COL,
            "timestamp_key": TIMESTAMP_COL
        }
        event_log = log_converter.apply(df, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)

        with tempfile.NamedTemporaryFile(suffix=".xes", delete=False) as tmp:
            xes_exporter.apply(event_log, tmp.name)
            temp_path = tmp.name

        return temp_path
    
    def extract_log_from_csv(self):
        xes_path = self.conversion_from_csv_to_xes()
        log = pm4py.read_xes(xes_path)
        return log
    
    def discovery_from_log(self, log):
        net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
        return net, initial_marking, final_marking
    
    def discovery_from_csv(self):
        xes_path = self.conversion_from_csv_to_xes()
        log = pm4py.read_xes(xes_path)
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

    def performance_analysis(self, log, metric, net=None, initial_marking=None, final_marking=None):
        if metric == "throughput_time":
            return self.get_throughput_time(log)
        elif metric == "activity_frequency":
            return self.get_activity_frequency(log)
        elif metric == "bottlenecks":
            if net is None or initial_marking is None or final_marking is None:
                raise ValueError("Bottleneck analysis requires a Petri net with markings.")
            return self.get_bottlenecks(log, net, initial_marking, final_marking)
        else:
            raise ValueError(f"Unknown metric: {metric}") 

if __name__ == "__main__":
    pmm = ProcessMiningModule(os.path.join(os.path.dirname(__file__), '..', '10-Minute Sample.csv'))
    xes_path = pmm.conversion_from_csv_to_xes()

    print("\n**************************************")
    print("\n\nI'm converting the csv logs into xes format...")

    log = pmm.extract_log_from_csv()
    net, initial_marking, final_marking = pmm.discovery_from_log(log)
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