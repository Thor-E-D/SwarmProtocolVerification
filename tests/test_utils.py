"""\
Test base keeping code shared for testing to avoid code duplication.
Additionally holds logic for creating automatic queries for testing.
Overall approach is build model and test that all queries are verifed

"""

import pytest
import os
import subprocess
import json
from typing import List, Dict

from ModelBuilder import createModel
from DataObjects.ModelSettings import ModelSettings
from JSONParser import Graph, parse_time_JSON, parse_projection_JSON_file, parse_protocol_seperatly, parse_protocol_JSON_file, build_graph

#verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta" # 5.0.0
verifyta_path = "C:\\Program Files\\UPPAAL-5.1.0-beta5\\app\\bin\\verifyta" # 5.1.0 beta-5

def save_xml_to_file(xml_data: str, file_name: str, file_path: str):
    full_file_path = f"{file_path}/{file_name}.xml"
    
    try:
        with open(full_file_path, 'w', encoding='utf-8') as file:
            file.write(xml_data)
        print(f"XML file saved successfully at {full_file_path}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

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

# Auto generates two queries for a given swarm protocol verifying we reach the end and that the log does not overflow.
def auto_generate_queries(protocol_json_file: str, log_size: int, base_path: str) -> str:
    # Add size of log query
    queries = f"A[] globalLog[logSize - 1].orderCount == 0 \n"

    # Add deadlock query
    # A[] forall(i:R48_t) forall(j:R49_t) (deadlock and globalLog[logSize - 1].orderCount == 0) imply R48(i).l54 and R49(j).l54
    with open(protocol_json_file, 'r') as f:
        data = json.load(f)
    graph = build_graph(data["transitions"])

    # Find edges with outdegree 0
    locations = []
    for edge in graph.nodes:
        current_target = edge.target
        found_end = True
        for edge_inner in graph.nodes:
            if current_target == edge_inner.source:
                found_end = False
                break
        if found_end:
            if current_target[0].isdigit():
                locations.append("l" + current_target)
            else:
                locations.append(current_target)
    
    index = 'i'
    map_role_index = {}

    for role in graph.get_role_names():
        map_role_index[role] = index
        index = chr(ord(index) + 1)

    print(map_role_index)

    deadlock_query = "A[] "
    for role in map_role_index:
        deadlock_query += f"forall({map_role_index[role]}: {role}_t) "

    deadlock_query += "(deadlock and globalLog[logSize - 1].orderCount == 0) imply "

    for role in map_role_index:
        current_index = map_role_index[role]
        current_role_addition = "("
        for location in locations:
            current_role_addition += f"{role}({current_index}).{location} or "
        current_role_addition = current_role_addition[:-4] + ")"
        deadlock_query += current_role_addition + " and "

    queries += deadlock_query[:-5]

    try:
        with open(base_path + "\\example_queries.txt", 'w') as file:
            file.write(queries)
    except Exception as e:
        print(f"An error occurred: {e}")

    return "example_queries"


def do_full_test(base_path: str, model_settings: ModelSettings, name_of_query_file: str = "", time_file: str = None):

    projection_json_files, protocol_json_file, time_json_file = identify_json_files(base_path, time_file)
    name_amount_dict = model_settings.role_amount

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

    currentModel = createModel(jsonTransfers, globalJsonTransfer, model_settings)
    save_xml_to_file(currentModel.to_xml(), "example_file", base_path)

    model_path = base_path + "\\example_file.xml"

    if name_of_query_file == "":
        name_of_query_file = auto_generate_queries(protocol_json_file, model_settings.log_size, base_path)
    
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

