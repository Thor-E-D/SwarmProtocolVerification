"""\
Test base keeping code shared for testing to avoid code duplication.
Additionally holds logic for creating automatic queries for testing.
Overall approach is build model and test that all queries are verifed

"""

import pytest
import os
import subprocess
import json
from typing import Set

from GraphAnalyser import GraphAnalyser
from QueryGenerator import QueryGenerator
from ModelBuilder import createModel
from DataObjects.ModelSettings import ModelSettings, DelayType
from JSONParser import Graph, parse_time_JSON, parse_projection_JSON_file, parse_protocol_seperatly, parse_protocol_JSON_file, build_graph

#verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta" # 5.0.0
verifyta_path = "C:\\Program Files\\UPPAAL-5.1.0-beta5\\app\\bin\\verifyta" # 5.1.0 beta-5

all_events = None
analysis_results = None
protocol_json_transfer = None
projection_jsonTransfers = None


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

def get_event_info():
    global protocol_json_transfer

    global all_events
    all_events = protocol_json_transfer.own_events.copy()
    all_events.extend(protocol_json_transfer.other_events)

    global analysis_results
    analyzer = GraphAnalyser(all_events)
    analysis_results = (analyzer.analyse_graph(protocol_json_transfer.initial))


# Auto generates two queries for a given swarm protocol verifying we reach the end and that the log does not overflow.
def auto_generate_queries(protocol_json_file: str, projection_json_files: Set[str], base_path: str) -> str:
    
    query_generator = QueryGenerator(protocol_json_file, projection_json_files)

    # Add size of log query
    overflow_query = query_generator.generate_overflow_query()
    queries = overflow_query + "\n"
    queries += query_generator.generate_end_state_query()

    try:
        with open(base_path + "\\example_queries.txt", 'w') as file:
            file.write(queries)
    except Exception as e:
        print(f"An error occurred: {e}")

    return "example_queries"

def calculate_approximate_log_size(events_to_amounts, all_events, branching_events, loop_events, loop_bound, initial):
    start_loops = set()
    for key in loop_events:
        start_loops.add(key)

    checked_branches = set()

    def calculate_loop(current_event, extra):
        res = events_to_amounts[current_event.event_name]
        for event in loop_events[current_event]:
            if event in branching_events and event not in checked_branches:
                extra += recursize_size_calculate(event)
            else:
                res += events_to_amounts[event.event_name]
        return res, extra

    def recursize_size_calculate(current_event):
        if current_event in branching_events and current_event not in checked_branches:
            # We need to get the other branching events for this branch
            branching_event_partition = []
            for event in all_events:
                if event.source == current_event.source:
                    branching_event_partition.append(event)
            
            branch_total = 0
            for branching_event in branching_event_partition:
                checked_branches.add(branching_event)
                current_branch = recursize_size_calculate(branching_event)
                branch_total += current_branch * events_to_amounts[branching_event.event_name]
            return branch_total

        elif current_event in start_loops:
            loop_total, extra = calculate_loop(current_event, 0)
            loop_total *= loop_bound
            return loop_total + extra

        else:
            next_event = next((event for event in all_events if event.source == current_event.target), None)
            if next_event == None:
                return events_to_amounts[current_event.event_name]
            return recursize_size_calculate(next_event) + events_to_amounts[current_event.event_name]

    # We first get initial
    initial_event = None
    for event in all_events:
        if event.source == initial:
            initial_event = event

    return recursize_size_calculate(initial_event)


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
        delay_type[role] = DelayType.NOTHING # If we have any type of delay it massively slows down the bigger swarm protocols
        delay_amount[role] = 1

    # Only change those set to None
    if model_settings.role_amount == None:
        model_settings.role_amount = role_amount
    if model_settings.delay_type == None:
        model_settings.delay_type = delay_type
    if model_settings.delay_amount == None:
        model_settings.delay_amount = delay_amount

    # Checking for log size and calulating a very rough estimate.
    # Be aware this could still cause overflow
    if model_settings.log_size == None:
        jsonTransfer = parse_protocol_seperatly(protocol_json_file)
        events_to_amounts = {}

        for transition in data["transitions"]:
            for event in all_events:
                if event.event_name == transition["label"]["logType"][0]:
                    events_to_amounts[event.event_name] = model_settings.role_amount[transition["label"]["role"]]

        branching_events = analysis_results["branching_events"]
        loop_events = analysis_results["loop_events"]

        model_settings.log_size = (calculate_approximate_log_size(events_to_amounts, all_events,branching_events,loop_events, model_settings.loop_bound, jsonTransfer.initial)) + 1


def do_full_test(base_path: str, model_settings: ModelSettings, name_of_query_file: str = "", time_file: str = None):

    projection_json_files, protocol_json_file, time_json_file = identify_json_files(base_path, time_file)

    time_file = None
    if (time_json_file != None):
        time_file = parse_time_JSON(time_json_file)

    model_settings.time_json_transfer = time_file


    global projection_jsonTransfers
    projection_jsonTransfers = []
    global protocol_json_transfer
    protocol_json_transfer = None
    if len(projection_json_files) == 0:
        protocol_json_transfer, projection_jsonTransfers = parse_protocol_JSON_file(protocol_json_file)
    else:
        protocol_json_transfer = (parse_protocol_seperatly(protocol_json_file))
        for projection_json_file in projection_json_files:
            projection_jsonTransfers.append(parse_projection_JSON_file(projection_json_file))
    
    # We need the model settings so if None we will auto generate
    if model_settings.role_amount == None or model_settings.delay_type == None or model_settings.delay_amount == None or model_settings.log_size == None or name_of_query_file == "":
        get_event_info()
    if model_settings.role_amount == None or model_settings.delay_type == None or model_settings.delay_amount == None or model_settings.log_size == None:
        generate_standard_settings(model_settings, protocol_json_file)

    currentModel = createModel(projection_jsonTransfers, protocol_json_transfer, model_settings)
    save_xml_to_file(currentModel.to_xml(), "example_file", base_path)

    model_path = base_path + "\\example_file.xml"

    if name_of_query_file == "":
        name_of_query_file = auto_generate_queries(protocol_json_file, projection_json_files, base_path)
    
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

