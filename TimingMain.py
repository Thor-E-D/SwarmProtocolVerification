import argparse
import json
import os
import subprocess
from typing import Any, List
import re
import time
from unittest.mock import patch
from io import StringIO
from argparse import Namespace
import csv

from DataObjects.Model import Model
from DataObjects.ModelSettings import DelayType, ModelSettings
from JSONParser import parse_time_JSON, parse_projection_JSON_file, parse_protocol_JSON_file, build_graph
from ModelBuilder import createModel
from QueryGenerator import QueryGenerator, generate_log_query
from CLI import build_model

base_path = os.path.dirname(os.path.abspath(__file__))
verifyta_path = "C:\\Program Files\\UPPAAL-5.1.0-beta5\\app\\bin\\verifyta.exe"

# Internal paths
folder_name = "TimingProtocol"
path_to_folder = os.path.join(base_path, folder_name)
path_to_base_state =  os.path.join(path_to_folder, "base_state.json")
path_to_current_state =  os.path.join(path_to_folder, "current_state.json")
path_to_base_query = os.path.join(path_to_folder, "query_base.txt")
path_to_logsize_query = os.path.join(path_to_folder, "query_logsize.txt")
path_to_model = os.path.join(path_to_folder, "uppaal_model.xml")
path_to_trace =  os.path.join(path_to_folder, "trace.txt")
path_to_csv =  os.path.join(path_to_folder, "output.csv")

# Experiments
ex1 = {"log_size": (50,1000,50)}
ex2 = {"role_amount": {"Transport": (1,10,1),"Door": 1,"Forklift": 1}, "delay_amount": {"Transport": (1,5,1),"Door": 1,"Forklift": 1}}

experiments = [ex1, ex2]


def filter_output(file_path_input: str) -> str:
    property_satisfied_pattern = re.compile(r"-- Formula is satisfied.")
    sup_result_pattern = re.compile(r"-- Result: (\d+)")

    with open(file_path_input, "r") as infile:
        content = infile.read()

        result = ""
        if "Error " in content or "syntax error:" in content or " [error] " in content:
            result = "Error"
        
        if (property_satisfied_pattern.search(content) != None):
            result = "True"
        else:
            result = "False"
        
        for line in content.splitlines():
            sup_result_match = sup_result_pattern.search(line)
            if sup_result_match != None:
                result = sup_result_match.group(1)
                return result

    return result

def verify_query(model_path, query_path, verifyta_path, index):
    command = [verifyta_path, model_path, query_path, "--query-index", f"{index}","--diagnostic", "0"]

    # Run the command and write the output directly to the file
    start_time = time.time()  # Start timing
    with open(path_to_trace, "w") as file:
        subprocess.run(command, stdout=file, stderr=subprocess.STDOUT, text=True)
    end_time = time.time()  # End timing
    elapsed_time = end_time - start_time

    # Check if query was satisfied
    verified = filter_output(path_to_trace)

    return verified, elapsed_time

def write_json_to_csv(json_file, csv_file, extra_fields=None):
    """
    Write JSON contents to a CSV file in columns.
    
    Parameters:
        json_file (str): Path to the JSON file.
        csv_file (str): Path to the CSV file.
        extra_fields (dict): Additional key-value pairs to include in the CSV.
    """
    # Load the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Exclude specific keys
    excluded_keys = {"verifyta_path", "base_path", "subsets"}
    filtered_data = {k: v for k, v in data.items() if k not in excluded_keys}
    
    # Add extra fields if provided
    if extra_fields:
        filtered_data.update(extra_fields)
    
    # Flatten nested dictionaries
    flattened_data = {}
    for key, value in filtered_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flattened_data[f"{key}.{sub_key}"] = sub_value
        else:
            flattened_data[key] = value

    # Check if the CSV file exists to determine appending headers or values
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            # Write the headers (keys) if the file doesn't exist
            writer.writerow(flattened_data.keys())
        
        # Write the values (data) as a new row
        writer.writerow(flattened_data.values())

def overwrite_json(source_file, target_file):
    # Read the source JSON file
    with open(source_file, 'r') as src:
        data = json.load(src)

    # Write the data to the target JSON file, overwriting its contents
    with open(target_file, 'w') as tgt:
        json.dump(data, tgt, indent=4)

def update_current_state(key: Any, value: Any):
    with open(path_to_current_state, 'r') as json_file:
        data = json.load(json_file)
    
    if (key != ""):
        data[key] = value
    
    with open(path_to_current_state, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_base_state(key: Any, value: Any):
    with open(path_to_base_state, 'r') as json_file:
        data = json.load(json_file)
    
    if (key != ""):
        data[key] = value
    
    with open(path_to_base_state, 'w') as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    experiment_index = 0

    while (experiment_index < len(experiments)):
        current_expriment = experiments[experiment_index]
        base_log_size = 0

        # Reset current state
        overwrite_json(path_to_base_state, path_to_current_state)

        # Set max settings and find logsize
        for key in current_expriment:
            if isinstance(key, dict):
                max_dict = {}
                for role in key:
                    triple = current_expriment[key][role]
                    if isinstance(triple, int):
                        max_dict[role] = triple
                    else:
                        max_dict[role] = triple[1]

                update_current_state(key, max_dict)
            else:
                update_current_state(key, current_expriment[key][1])

        # set a high log size:
        update_current_state("log_size", 200)

        build_args = Namespace(
        command="build",
        path_to_folder = path_to_folder,
        path_to_state = path_to_current_state
        )

        build_model(build_args)

        result, recorded_time = (verify_query(path_to_model, path_to_logsize_query, verifyta_path, 0))
        base_log_size = result + 1


        update_base_state("log_size", base_log_size)
        

        for i in range(len(list(current_expriment.keys()))):
            

        # Set settings


        # Buld model
        build_args = Namespace(
        command="build",
        path_to_folder = path_to_folder,
        path_to_state = path_to_current_state
        )

        build_model(build_args)

        # verify 
        result, recorded_time = (verify_query(path_to_model, path_to_base_query, verifyta_path, 0))

        # Write to csv file.
        extra_fields = {"verification_result": result, "time": recorded_time}
        write_json_to_csv(path_to_current_state, path_to_csv, extra_fields)


