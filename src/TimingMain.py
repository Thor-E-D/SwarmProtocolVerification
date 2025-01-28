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
from itertools import product
from copy import deepcopy

from DataObjects.Model import Model
from DataObjects.ModelSettings import DelayType, ModelSettings
from JSONParser import parse_time_JSON, parse_projection_JSON_file, parse_protocol_JSON_file, build_graph
from ModelBuilder import createModel
from QueryGenerator import QueryGenerator, generate_log_query
from CLI import build_model
from TimingExperiments import get_scaling_experiments

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

# Experiments
experiment_configs = get_scaling_experiments()


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
    else:
        data = value
    
    with open(path_to_current_state, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_base_state(key: Any, value: Any):
    with open(path_to_base_state, 'r') as json_file:
        data = json.load(json_file)
    
    if (key != ""):
        data[key] = value
    
    with open(path_to_base_state, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def generate_experiments_nested(config):
    varying_params = []
    varying_keys = []
    
    # Extract varying parameters and their keys
    for key, subdict in config.items():
        if isinstance(subdict, dict):
            for subkey, value in subdict.items():
                if isinstance(value, range) or isinstance(value, list):
                    varying_params.append(value)
                    varying_keys.append((key, subkey))
        else:
            if isinstance(subdict, (range, list)):
                varying_params.append(subdict)
                varying_keys.append((key, ""))

    # Generate combinations
    combinations = product(*varying_params)
    experiments = []

    for combo in combinations:
        experiment = deepcopy(config)
        for (key, subkey), value in zip(varying_keys, combo):
            if subkey != "":
                experiment[key][subkey] = value
            else:
                experiment[key] = value
        experiments.append(experiment)

    return experiments

def get_highest_settings(config):
    highest_config = deepcopy(config)

    for key, subdict in highest_config.items():
        if isinstance(subdict, dict):
            for subkey, value in subdict.items():
                if isinstance(value, (range, list)):
                    subdict[subkey] = max(value)  # Replace with max value
        else:
            if isinstance(subdict, (range, list)):
                highest_config[key] = max(subdict) 

    return highest_config

if __name__ == "__main__":

        counter = 1
        for experiment_config in experiment_configs:
            experiments = generate_experiments_nested(experiment_config)

            highest_exp = get_highest_settings(experiment_config)

            print(f"running experiment {counter} with higest setting: {highest_exp}")


            current_optimal_logsize = 0
            
            update_current_state("", highest_exp)
            if highest_exp["log_size"] == -1:

                update_current_state("log_size", 200)

                    # Buld model
                build_args = Namespace(
                command="build",
                path_to_folder = path_to_folder,
                path_to_state = path_to_current_state
                )

                build_model(build_args)

                # verify 
                result, recorded_time = (verify_query(path_to_model, path_to_logsize_query, verifyta_path, 0))
                current_optimal_logsize = int(result) + 1
                print(f"found optimal log size for this expriment: {current_optimal_logsize}")
            
            path_to_csv =  os.path.join(path_to_folder, f"output{counter}.csv")

            # Run experiments
            for exp in experiments:

                # Set settings
                update_current_state("", exp)
                if exp["log_size"] == -1:
                    update_current_state("log_size", current_optimal_logsize)

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
            
            print(f"Done with experiment {counter}")
            counter += 1


