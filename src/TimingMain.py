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

# example protocols
example_protocols = "example_protocols"
path_to_protocols = os.path.join(base_path, example_protocols)
path_to_current_state_protocols =  os.path.join(path_to_protocols, "current_state.json")
path_to_protocols_output =  os.path.join(path_to_protocols, "output.csv")


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
    # verifyta --hashtable-size 32 model.xml query.q

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
    excluded_keys = {"verifyta_path", "base_path"}
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

def run_verify_timing_experiment():
    counter = 1
    for experiment_config in experiment_configs:
        experiments = generate_experiments_nested(experiment_config)

        highest_exp = get_highest_settings(experiment_config)

        print(f"running experiment {counter} with higest setting: {highest_exp}")


        current_optimal_logsize = 0
            
        update_current_state("", highest_exp)
        if highest_exp["log_size"] == -1:
            update_current_state("log_size", 120)

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

def fetch_json_files(root_dir):
    json_files = []
    
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".json"):
                file_path = os.path.join(foldername, "")
                json_files.append(file_path)
    
    return json_files

def update_current_state_protocol(json_path: str, model_settings: ModelSettings):
    # Load existing JSON file
    with open(json_path, "r") as file:
        existing_data = json.load(file)

    # Convert ModelSettings to dictionary
    settings_dict = model_settings.to_dict()

    print(settings_dict)

    # Update only matching fields
    for key, value in settings_dict.items():
        existing_data[key] = value
            

    # Write back to JSON file
    with open(json_path, "w") as file:
        json.dump(existing_data, file, indent=4)


def generate_standard_settings(model_settings: ModelSettings, protocol_json_file: str):
    with open(protocol_json_file, 'r') as f:
        data = json.load(f)
    graph = build_graph(data["transitions"])

    # Need to get all roles and figure out who the first one is so they can have amount 1 and the rest 2
    # Find edges with indegree 0
    roles = set()
    firstRole = ""
    for edge in graph.edges:
        roles.add(edge.role)

        current_source = edge.source
        found_start = True
        for edge_inner in graph.edges:
            if current_source == edge_inner.target:
                found_start = False
                break
        if found_start:
            firstRole = edge.role
    
    # We now need to make role_amount: Dict[str, int], delay_type: Dict[str, DelayType], delay_amount: Optional[Dict[str, int]]
    role_amount = {}
    delay_type = {}
    delay_amount = {}
    for role in roles:
        if firstRole == role:
            role_amount[role] = 1
        else:
            role_amount[role] = 1 # Set to 2 will slow it down
        delay_type[role] = "N" # If we have any type of delay it massively slows down the bigger swarm protocols
        delay_amount[role] = 1

    # Only change those set to None
    if model_settings.role_amount == None:
        model_settings.role_amount = role_amount
    if model_settings.delay_type == None:
        model_settings.delay_type = delay_type
    if model_settings.delay_amount == None:
        model_settings.delay_amount = delay_amount


def sort_paths_numerically(paths):
    def extract_number(path):
        match = re.search(r'\d+', path)  # Find the first number in the path
        return int(match.group()) if match else float('inf')  # Sort non-numeric last

    return sorted(paths, key=extract_number)


def run_building_experiment(json_files):
    json_files.pop(0)
    json_files = sort_paths_numerically(json_files)

    for json_file_folder in json_files:
        model_settings = ModelSettings(None, None)
        model_settings.path_bound = 2
        model_settings.branch_tracking = True
        model_settings.delay_amount = None
        model_settings.log_size = 50

        def find_json_file(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".json"):
                    return os.path.join(folder_path, file)
            return None

        json_file = find_json_file(json_file_folder)
        print(f"Processing file: {json_file}")

        with open(json_file, 'r') as f:
            data = json.load(f)

        transitions_amount = len(data["transitions"])
        roles = {transition["label"]["role"] for transition in data["transitions"]}
        roles_amount = len(roles)

        generate_standard_settings(model_settings, json_file)
        update_current_state_protocol(path_to_current_state_protocols, model_settings)

        build_args = Namespace(
            command="build",
            path_to_folder=json_file_folder,
            path_to_state=path_to_current_state_protocols
        )

        current_build_times = []
        for _ in range(10):

            build_time, _ = build_model(build_args)
            current_build_times.append(build_time)

            
        append_to_csv(path_to_protocols_output, [transitions_amount, roles_amount] + current_build_times)



def append_to_csv(file_path, value_list):
    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(value_list)

def move_json_files(json_files):
    for file_path in json_files:
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        folder_name = os.path.splitext(filename)[0]
        new_folder_path = os.path.join(directory, folder_name)
        
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        
        new_file_path = os.path.join(new_folder_path, filename)
        os.rename(file_path, new_file_path)


if __name__ == "__main__":
    #run_verify_timing_experiment()

    json_files = fetch_json_files(path_to_protocols)
    run_building_experiment(json_files)

    #move_json_files(json_files)
    #print("Found JSON files:")
    #for file in json_files:
    #    print(file)


