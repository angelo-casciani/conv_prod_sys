import requests
import os 
import process_mining

pmm = process_mining.ProcessMiningModule(os.path.join(os.path.dirname(__file__), '..', '10-Minute Sample.csv'))
xes_path = pmm.conversion_from_csv_to_xes()
url = "http://127.0.0.1:6662/"
files = {"xes_file": open(xes_path, "rb")}
data = {
    "simthreshold": "0.9",
    "eta": "0.01",
    "eps": "0.001"
}

response = requests.post(url, files=files, data=data)
print(response.json())
