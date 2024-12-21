import pytest
import os
import subprocess
from Model import createModel, save_xml_to_file
from DataObjects.ModelSettings import ModelSettings
from JSONParser import parse_time_JSON, parse_projection_JSON_file, parse_protocol_seperatly, parse_protocol_JSON_file
from typing import List, Dict
import json

#verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta" # 5.0.0
verifyta_path = "C:\\Program Files\\UPPAAL-5.1.0-beta5\\app\\bin\\verifyta" # 5.1.0 beta-5

def identify_json_files(folder_path, time_file_name: str = None):
    projection_json_files = set()
    protocol_json_file = None
    time_json_file = None

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)

                    # Check for Time File
                    if ("events" in data or "logs" in data):
                        if time_file_name != None and file_name == (time_file_name + ".json"):
                            time_json_file = file_path
                    
                    # Check for Projection JSON
                    elif "subscriptions" in data:
                        projection_json_files.add(file_path)
                    
                    # Check for SwarmProtocol JSON
                    elif "initial" in data and "transitions" in data and "subscriptions" not in data:
                        protocol_json_file = file_path
                    
            except json.JSONDecodeError:
                print(f"Invalid JSON file found: {file_name}")

    return projection_json_files, protocol_json_file, time_json_file

def count_lines_in_file(file_path: str):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return len(lines)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def do_full_test(base_path: str, name_of_query_file: str, name_amount_dict: Dict[str,int], model_settings: ModelSettings, time_file: str = None):

    projection_json_files, protocol_json_file, time_json_file = identify_json_files(base_path, time_file)
    time_file = None
    if (time_json_file != None):
        time_file = parse_time_JSON(time_json_file)

    model_settings.time_json_transfer = time_file

    jsonTransfers = []
    globalJsonTransfer = None
    if len(projection_json_files) == 0:
        globalJsonTransfer, jsonTransfers = parse_protocol_JSON_file(protocol_json_file)
    else:
        globalJsonTransfer = (parse_protocol_seperatly(protocol_json_file))
        for projection_json_file in projection_json_files:
            jsonTransfers.append(parse_projection_JSON_file(projection_json_file))

    currentModel = createModel(jsonTransfers, globalJsonTransfer, name_amount_dict, model_settings)
    save_xml_to_file(currentModel, "example_file", base_path)

    model_path = base_path + "\\example_file.xml"
    query_string = base_path + f"\\{name_of_query_file}.txt"

    command = [verifyta_path, model_path, query_string]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.fail(result.stderr)
    
    lines = (result.stdout).splitlines()
    satisfied_count = sum(1 for line in lines if "Formula is satisfied." in line)

    expected_satisfied_count = count_lines_in_file(query_string)
    assert satisfied_count == expected_satisfied_count, \
        f"Not all formulas were satisfied. Expected {expected_satisfied_count}, but found {satisfied_count}."

