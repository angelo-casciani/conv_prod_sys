import pm4py
import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
import tempfile

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



if __name__ == "__main__":
    pmm = ProcessMiningModule("/Users/fabrizioitalia/Documents/AI_Robotics/Tesi/conv_prod_sys/10-Minute Sample.csv")
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