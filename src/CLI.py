"""\
Command Line Interface.
Using argparse to keep track of commands and help messages.
Contains all arguments, along with relevant helper methods for necessary functionality
such as formatting the output of fault traces to only contain relevant information for user.

"""

import argparse
import json
import os
import subprocess
from typing import Any, List
import re

from DataObjects.Model import Model
from DataObjects.ModelSettings import DelayType, ModelSettings
from JSONParser import parse_time_JSON, parse_projection_JSON_file, parse_protocol_JSON_file, build_graph
from ModelBuilder import createModel
from QueryGenerator import QueryGenerator, generate_log_query

base_path = os.path.dirname(os.path.abspath(__file__))
state_path = "PermanentState\\state.json" # Hardcoded relative path to local state file
autoQuery_path = "PermanentState\\autoQueries.txt" # Hardcoded relative path to local state file.

str_validity = "validity"
str_sizebound = "sizebound"
str_eventualfidelity = "fidelity"
str_timebound = "timebound"
auto_query_choices = [str_validity, str_sizebound, str_eventualfidelity, str_timebound]

# Mapping user-friendly strings to DelayType values
DELAY_TYPE_MAPPING = {
    "N": DelayType.NOTHING,
    "E": DelayType.EVENTS_EMITTED,
    "S": DelayType.EVENTS_SELF_EMITTED
}

def save_xml_to_file(xml_data: str, file_name: str, file_path: str):
    full_file_path = f"{file_path}/{file_name}.xml"
    
    try:
        with open(full_file_path, 'w', encoding='utf-8') as file:
            file.write(xml_data)
        print(f"XML file saved successfully at {full_file_path}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

def identify_json_files(folder_path: str):
    projection_json_files = set()
    protocol_json_file = None
    time_json_file = None
    try: 
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.json'):
                file_path = os.path.join(folder_path, file_name)
                try:
                    with open(file_path, 'r') as file:
                        data = json.load(file)

                        # Check for Time File
                        if ("events" in data or "logs" in data):
                            time_json_file = file_path
                        
                        # Check for Projection JSON
                        elif "subscriptions" in data:
                            projection_json_files.add(file_path)
                        
                        # Check for SwarmProtocol JSON
                        elif "initial" in data and "transitions" in data and "subscriptions" not in data:
                            protocol_json_file = file_path
                        
                except json.JSONDecodeError:
                    print(f"Invalid JSON file found: {file_name}")
    except:
        print(f"No folder identified at {folder_path}")
    return projection_json_files, protocol_json_file, time_json_file

def get_verifyta_path(verifyta_path: str) -> str:
    if verifyta_path == None:
        verifyta_path = get_state_data("verifyta_path")
    else:
        verifyta_path = " ".join(verifyta_path)
    return verifyta_path

def get_state_data(key: Any, file_path: str = "") -> Any:
    try:
        if file_path == "":
            file_path = os.path.join(base_path, state_path)
        # Read the existing data from the file
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        
        if key == "":
            return data
        else:
            return data[key]
        
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


def update_local_state(key: Any, value: Any):
    file_path = os.path.join(base_path, state_path)
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    
    if (key != ""):
        data[key] = value
    
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Successfully updated {key} in state with {data[key]}")

def write_state_to_path(path: str):
    file_path = os.path.join(base_path, state_path)
    # Read the existing data from the file
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)

    try:
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Successfully wrote json to {path}")
    except FileNotFoundError:
        print(f"Error: Could not write to {path}. Make sure it ends in a file name")
    except Exception as e: 
        print(f"Unexpected error: {e}")

def check_state_data(data: Any):
    json_required_keys = [
        "verifyta_path",
        "base_path",
        "delay_type",
        "path_bound",
        "branch_tracking",
        "log_size",
        "delay_amount",
        "role_amount"
        ]

    for key in json_required_keys:
        if key not in data:
            print (f"Fault format missing key {key} in given json")
            return None
        
    return data
            
def load_state_from_path(path: str):
    try:
        file_path = os.path.join(base_path, state_path)
        with open(path, 'r') as json_file:
            data = json.load(json_file)
    
        data = check_state_data(data)
        if data == None:
            return

        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Successfully loaded json into local state")
    except FileNotFoundError:
        print(f"Error: {path} not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


def load_state_into_model_settings(state_data):
    new_delay_type = {}
    current_delay_type = state_data["delay_type"]
    delay_type_keys = list(DELAY_TYPE_MAPPING.keys())

    for delay_type_single in current_delay_type:
        if current_delay_type[delay_type_single] in delay_type_keys:
            new_delay_type[delay_type_single] = DELAY_TYPE_MAPPING[current_delay_type[delay_type_single]]
        else:
            new_delay_type[delay_type_single] = current_delay_type[delay_type_single]

    model_settings = ModelSettings(role_amount=state_data["role_amount"],delay_type=new_delay_type)
    model_settings.path_bound = state_data["path_bound"]
    model_settings.branch_tracking = state_data["branch_tracking"]
    model_settings.log_size = state_data["log_size"]
    model_settings.delay_amount = state_data["delay_amount"]

    return model_settings

def build_model(args):
    try:
        state_data = None
        if args.path_to_state == None:
            state_data = get_state_data("")
        else:
            full_path_state = " ".join(args.path_to_state)
            state_data = get_state_data("", full_path_state)

        state_data = check_state_data(state_data)
        if state_data == None:
            return

        model_settings = load_state_into_model_settings(state_data)

        path_to_files = None
        if args.path_to_folder == None:
            path_to_files = state_data["base_path"]
        else:
            path_to_files = " ".join(args.path_to_folder)

        print(f"Attempt to identify relevant json files at local location {path_to_files}")
        
        projection_json_files, protocol_json_file, time_json_file = identify_json_files(path_to_files)

        if protocol_json_file == None:
            print("Cannot find protocol JSON aborting attempt")
            print("Please review the folder path with \"setPath\"")
            return

        json_transfers = []
        global_json_transfer = None
        if len(projection_json_files) == 0:
            print("No projection files found so auto-generating projections")
            global_json_transfer, json_transfers = parse_protocol_JSON_file(protocol_json_file)
        else:
            global_json_transfer, auto_json_transfers = parse_protocol_JSON_file(protocol_json_file)

            name_list = []
            for auto_json_transfer in auto_json_transfers:
                name_list.append(auto_json_transfer.name)

            for projection_json_file in projection_json_files:
                current_json_transfer = parse_projection_JSON_file(projection_json_file)
                if current_json_transfer.name in name_list:
                    name_list.remove(current_json_transfer.name)
                    json_transfers.append(current_json_transfer)

            if len(name_list) != 0:
                print(f"Missing the following projections {name_list} so auto generating them")
                for auto_json_transfer in auto_json_transfers:
                    if auto_json_transfer.name in name_list:
                        json_transfers.append(auto_json_transfer)

        time_transfer = None

        if time_json_file != None:
            print("Found a time json file!")
            time_transfer = parse_time_JSON(time_json_file)
            model_settings.time_json_transfer = time_transfer
        else:
            print("No time file found")

        currentModel = createModel(json_transfers, global_json_transfer, model_settings)
        save_xml_to_file(currentModel.to_xml(), "uppaal_model", path_to_files)
    except Exception as e:
        print(f"Failed to build with exception {e}")

def set_verifyta_path(newPath: str):
    # First we format the given path a little
    if newPath.endswith("verifyta"):
        newPath = newPath + ".exe"
    elif newPath.endswith("bin"):
        newPath = os.path.join(newPath, "verifyta.exe")

    if not os.path.isfile(newPath):
        print(f"Tool not found at path: {newPath}")
        return
    
    try:
        result = subprocess.run([newPath, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"Tool is present and working at: {newPath}")
            print(f"Version Output: {result.stdout.strip()}")
            if "UPPAAL" not in result.stdout.strip():
                print("Not a verifyta distribution. Aborting")
            else:
                update_local_state("verifyta_path", newPath)
    except Exception as e:
        print(f"Error occurred while verifying the tool: {e}")

def get_lines_in_file(file_path: str) -> List[str]:
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return lines
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred when reading file at {file_path}: {e}")

def filter_output(file_path_input: str) -> str:
    # Define regular expressions for the patterns
    state_pattern = re.compile(r"State:")
    transition_pattern = re.compile(r"Transition:")
    role_transition_pattern = re.compile(r"setLogEntryForUpdate\(\w+_ID,")
    propagation_pattern = re.compile(r"log\(\d+\).l_prop[1-9]->")
    property_satisfied_pattern = re.compile(r"-- Formula is satisfied.")
    delay_pattern = re.compile(r"Delay: \d+")
    global_time_pattern = re.compile(r"globalTime=\d+")

    sup_result_pattern = re.compile(r"-- Result: \d+")

    result = ""

    with open(file_path_input, "r") as infile:
        next_is_state = False
        next_is_transition = False
        current_state = None
        current_global_time = None

        content = infile.read()

        if "Error " in content or "syntax error:" in content or " [error] " in content:
            print("Error during verification")
            print(content)
            return result
        
        if (property_satisfied_pattern.search(content) != None):
            result += "Query was satisfied \n"
        else:
            result += "Query not satisfied \n"
        
        for line in content.splitlines():
            state_match = state_pattern.search(line)

            sup_result_match = sup_result_pattern.search(line)
            if sup_result_match != None:
                grouped = sup_result_match.group()
                result += grouped
                return result
            
            if "globalTime: " in line:
                result += "Giving the resulting bound: " + line[12:]
                return result

            if state_match != None:
                next_is_state = True
                continue

            if next_is_state:
                lines_to_save = [role for role in line.split() if "log" not in role and role != "(" and role != ")"]
                if lines_to_save != current_state:
                    result += (f"State: {lines_to_save}" + "\n")
                    current_state = lines_to_save
                next_is_state = False
            
            transition_match = transition_pattern.search(line)
            if transition_match != None:
                next_is_transition = True
                continue
            
            if next_is_transition:
                propagation_match = propagation_pattern.search(line)
                role_transition_match = role_transition_pattern.search(line)
                transition = line.partition("{")[0]
                if propagation_match != None:
                    role = line.partition("_log")
                    result += (f"Role {role[0]}({role[2][1]}) propagated to all other roles\n")
                if role_transition_match != None:
                    grouped = role_transition_match.group()
                    result += (f"Transition: {transition} {(grouped.partition("(")[2])[:-4]}\n")
                next_is_transition = False

            delay_match = delay_pattern.search(line)
            if delay_match != None:
                result += (delay_match.group() + "  ")

            global_time_match = global_time_pattern.search(line)
            if global_time_match != None and current_global_time != global_time_match.group():
                current_global_time = global_time_match.group()
                result += current_global_time + "\n"
    
    return result

def verify_model(model_path: str, query_path: str, verifyta_path: str):
    verifyta_path = get_verifyta_path(verifyta_path)
    
    queries = get_lines_in_file(query_path)
    if queries == None:
        return

    for i in range(len(queries)):
        print(f"Verifying query {i}: {queries[i]}")
        filtered_output = verify_query(model_path, query_path, verifyta_path, i)
        print(filtered_output)

def verify_query(model_path, query_path, verifyta_path, index):
    command = [verifyta_path, model_path, query_path, "--query-index", f"{index}","--diagnostic", "0"]
    file_path = os.path.join(base_path, state_path[:-11], "trace.txt")

        # Run the command and write the output directly to the file
    with open(file_path, "w") as file:
        subprocess.run(command, stdout=file, stderr=subprocess.STDOUT, text=True)
        
        # We must filter the output file into a format that the user can understand
    filtered_output = filter_output(file_path)
    return filtered_output

# Checks correct format of given information.
def parse_json_dict(key, json_input: str):
    try:
        updates = json.loads(json_input)
        if (not isinstance(updates, dict)):
            print("Provided JSON must represent a dictionary")
        else:
            if key == "delay_amount":
                if (not all(isinstance(k, str) and isinstance(v, int) for k, v in updates.items())):
                    print("Provided delay amount dictionary must be of the shape {str, int}")
                    return
                update_local_state(key, updates)
            elif key == "role_amount":
                if (not all(isinstance(k, str) and isinstance(v, int) for k, v in updates.items())):
                    print("Provided role amount dictionary must be of the shape {str, int}")
                    return
                update_local_state(key, updates)
            elif key == "delay_type":
                if (not all(isinstance(k, str) and v in DELAY_TYPE_MAPPING.keys() for k, v in updates.items())):
                    print("Provided delay type dictionary must be of the shape {str, Delay Type}")
                    return
                new_delay_type = {}
                for key_type in updates:
                    new_delay_type[key_type] = DELAY_TYPE_MAPPING[updates[key_type]]
                update_local_state(key, updates)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input. {e}")

def auto_verify_model(model_path: str, base_folder_path: str, type: str, verifyta_path: str):
    verifyta_path = get_verifyta_path(verifyta_path)

    try:
        projection_json_files, protocol_json_file, _ = identify_json_files(base_folder_path)
        query_generator = QueryGenerator(protocol_json_file, projection_json_files)
    except Exception as e:
        print(f"Failed with exception: {e}")
        return
    
    query_path = os.path.join(base_path, autoQuery_path)

    if (type == str_validity):
        validity_query = query_generator.generate_end_state_query()

        # Write to local query file
        with open(query_path, 'w') as file:
            file.write(validity_query)

        queries = get_lines_in_file(query_path)
        print(f"Verifying query {0}: {queries[0]}")
        print(verify_query(model_path, query_path, verifyta_path, 0))
    elif (type == str_sizebound):
        overflow_query = query_generator.generate_overflow_query()
        # Write to local query file
        with open(query_path, 'w') as file:
            file.write(overflow_query)

        result = verify_query(model_path, query_path, verifyta_path, 0)
        if "Query was satisfied" in result:
            print("Model did not overflow finding smallest possible log size")
            size_bound_query = query_generator.generate_sizebound_query()

            with open(query_path, 'w') as file:
                file.write(size_bound_query)

            result = verify_query(model_path, query_path, verifyta_path, 0)
            match = re.search(r"Result:\s*(\d+)", result)
            if match:
                print(f"Recommended log size: {int(match.group(1)) + 1}")
        else:
            print("Model overflow!! Cannot find optimal logsize")
            print("Set a larger logsize before trying again.")

    elif (type == str_eventualfidelity):
        role_queries_dict = query_generator.generate_eventual_fidelity_queries()

        for role in role_queries_dict:
            with open(query_path, 'w') as file:
                file.write(role_queries_dict[role])
            print(f"Verifying query for {role}: {role_queries_dict[role]}")
            print(verify_query(model_path, query_path, verifyta_path, 0)) 
    
    elif (type == str_timebound):
        role_queries_dict = query_generator.generate_timebound_queries()
        for role in role_queries_dict:
            print(f"{role} has the following time bounds")
            for query in role_queries_dict[role]:
                with open(query_path, 'w') as file:
                    file.write(query)

                result = verify_query(model_path, query_path, verifyta_path, 0)
                result = result.replace("âˆž)", "INF]")
                match_query = re.search(r"\.(l\d+)", query)
                if match_query:
                    print (f"Location {match_query.group(1)}: {result.split(": ")[1]}")
        
        print ("---------------------------")

def verify_log(model_path: str, log_path: str, verifyta_path: str, valid_only: bool):
    if valid_only == None:
        valid_only = False

    verifyta_path = get_verifyta_path(verifyta_path)
    
    log_line = get_lines_in_file(log_path)
    log_list = [event.strip() for event in log_line[0].split(",") if event.strip()]

    query_path = os.path.join(base_path, autoQuery_path)
    query_to_verify = generate_log_query(log_list, valid_only)

    print(f"Verifying query: {query_to_verify}")

    with open(query_path, 'w') as file:
        file.write(query_to_verify)

    filtered_output = verify_query(model_path, query_path, verifyta_path, 0)
    print(filtered_output)


# For parsing booleans from strings
def str2bool(value: str) -> bool:
    if value.lower() in {'yes', 'true', 't', 'y', '1'}:
        return True
    elif value.lower() in {'no', 'false', 'f', 'n', '0'}:
        return False
    else:
        print(f'Boolean value expected. Got {value}')

# For model setting arguments
def set_arguments(args):
    if args.verifyta_path != None:
        full_path = " ".join(args.verifyta_path)
        set_verifyta_path(full_path)

    if args.path_to_folder != None:
        full_path = " ".join(args.path_to_folder)
        update_local_state("base_path", full_path)

    if args.branch_tracking != None:
        update_local_state("branch_tracking", args.branch_tracking)

    if args.log_size != None:
        update_local_state("log_size", args.log_size)

    if args.path_counter != None:
        update_local_state("path_bound", args.path_counter)

    if args.delay_type_all != None:
        args.delay_type_all = " ".join(args.delay_type_all)
        parse_json_dict("delay_type", args.delay_type_all)

    if args.delay_amount_all != None:
        args.delay_amount_all = " ".join(args.delay_amount_all)
        parse_json_dict("delay_amount", args.delay_amount_all)

    if args.role_amount != None:
        args.role_amount = " ".join(args.role_amount)
        parse_json_dict("role_amount", args.role_amount)

def create_parser():
    parser = argparse.ArgumentParser(description="Model cheking swarm protocols CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the model")
    build_parser.add_argument(
        "-pf", "--path-to-folder",
        type=str,
        nargs='+',
        help="Path to folder containing the relevant json files. Default is currently saved",
        required=False
    )

    build_parser.add_argument(
        "-ps", "--path-to-state",
        type=str,
        nargs='+',
        help="Path to json file containing state information. Default is currently saved",
        required=False
    )

    # For setting arguments for the model
    argument_parser = subparsers.add_parser("setArgs", help="Set the arguments for the build")
    argument_parser.add_argument(
        "-vp", "--verifyta-path",
        type=str,
        nargs='+',
        help="The absolute path to a verifyta distribution",
        required=False
    )

    argument_parser.add_argument(
        "-pf", "--path-to-folder",
        type=str,
        nargs='+',
        help="The absolute path to a folder with relevant json files",
        required=False
    )

    argument_parser.add_argument(
        "-log", "--log-size",
        type=int,
        help="Size of the log that will be used within UPPAAL",
        required=False
    )

    argument_parser.add_argument(
        "-path", "--path-counter",
        type=int,
        help="Maximum amount of times a path in the model can be taken. Does not apply to exit paths",
        required=False
    )

    argument_parser.add_argument(
        "-dta", "--delay-type-all",
        type=str,
        nargs='+',
        help="""Specified which type of delay can possibly be taken for all roles input as (e.g., {\"R1\": \"N\", \"R2\": \"E\"}) Where: \n
                N is no form of delay \n
                E is delay from a global amount of events before propagation is forced \n
                S is delay from a local amount of emitted events before propagation is forced""",
        required=False
    )

    argument_parser.add_argument(
        "-bt", "--branch-tracking",
        type=str2bool,
        help="Wether or not to use branch tracking default is true",
        required=False
    )

    argument_parser.add_argument(
        "-daa", "--delay-amount-all",
        type=str,
        nargs='+',
        help="Specified how much delay is required for each role (e.g., {\"R1\": 1, \"R2\": 2})",
        required=False
    )

    argument_parser.add_argument(
        "-ra", "--role-amount",
        type=str,
        nargs='+',
        help="Specified how many instances/machines are replicated for each role (e.g., {\"R1\": 1, \"R2\": 2})",
        required=False
    )

    subparsers.add_parser("showArgs", help="Displays the current settings for the model")

    load_state_parser = subparsers.add_parser("loadState", help="Load state from path, overwriting internal state file")
    load_state_parser.add_argument(
        "path",
        type=str,
        nargs='+',
        help="The absolute path to the desired json file",
    )

    write_state_parser = subparsers.add_parser("writeState", help="Write internal state json file to path")
    write_state_parser.add_argument(
        "path",
        type=str,
        nargs='+',
        help="The absolute path to where the file should be saved"
    )

    verify_parser = subparsers.add_parser("verify", help="Verifies a given model with a set of given queries")
    verify_parser.add_argument(
        "model_path",
        type=str,
        nargs='+',
        help="Path to the UPPAAL xml file"
    )

    verify_parser.add_argument(
        "query_path",
        type=str,
        nargs='+',
        help="Path to the txt file containing newline seperated queries"
    )

    verify_parser.add_argument(
        "-vp", "--verifyta-path",
        type=str,
        nargs='+',
        help="Path to the verifyta distribution if not specified local will be used ",
        required=False
    )

    auto_verify_parser = subparsers.add_parser("autoVerify", help="Verifies a given model using automatically generated queries")
    auto_verify_parser.add_argument(
        "model_path",
        type=str,
        nargs='+',
        help="Path to the UPPAAL xml file"
    )

    auto_verify_parser.add_argument(
        "base_path",
        type=str,
        nargs='+',
        help="Path to the folder containing the json files used to build the model"
    )

    auto_verify_parser.add_argument(
    "--type",
    type=str,
    choices=auto_query_choices,
    default=str_validity,
    help=f"""Type of auto query wanted:
    - {str_validity}: (Defualt). Ensures all roles reach an endstate eventually. 
    - {str_sizebound}: Returns the smalles log size that does not cause overflow.
    - {str_eventualfidelity}: Returns wether or not eventual fidelity holds for all roles of the gives model.
    - {str_timebound}: Returns the global time reachable for all locations of all roles (Warning SLOW) (ONLY WORKS WITH UPPAAL 5.1.0-beta)"""
    )

    auto_verify_parser.add_argument(
        "-vp", "--verifyta-path",
        type=str,
        nargs='+',
        help="Path to the verifyta distribution if not specified local will be used ",
        required=False
    )

    verify_log_parser = subparsers.add_parser("verifyLog", help="Verifies if a given global can exists in the model")
    verify_log_parser.add_argument(
        "model_path",
        type=str,
        nargs='+',
        help="Path to the UPPAAL xml file"
    )

    verify_log_parser.add_argument(
        "log_file_path",
        type=str,
        nargs='+',
        help="Path to the txt file containing a log as comma(,) seperated strings"
    )

    verify_log_parser.add_argument(
    "-vp", "--verifyta-path",
    type=str,
    nargs='+',
    help="Path to the verifyta distribution if not specified local will be used ",
    required=False
    )

    verify_log_parser.add_argument(
        "-vo", "--valid-only",
        type=str2bool,
        help="Wether or not to check the global log or only the parts that are valid events. Default is false",
        required=False
    )

    subparsers.add_parser("q", help="Quit the CLI.") 

    return parser

def main():
    parser = create_parser()

    print("Welcome to the File Organizer CLI!")
    print("Type '-h' for a list of commands or 'q' to quit.")

    while True:
        user_input = input("\n> ").strip()
        if not user_input:
            continue

        try:
            # Parse the command line arguments
            args = parser.parse_args(user_input.split())
            if args.command == "build":
                build_model(args)
            elif args.command == "setArgs":
                set_arguments(args)
            elif args.command == "showArgs":
                state_data = get_state_data("")
                print(state_data)
            elif args.command == "loadState":
                full_path = " ".join(args.path)
                load_state_from_path(full_path)
            elif args.command == "writeState":
                full_path = " ".join(args.path)
                write_state_to_path(full_path)
            elif args.command == "verify":
                model_path = " ".join(args.model_path)
                query_path = " ".join(args.query_path)
                verify_model(model_path, query_path, args.verifyta_path)
            elif args.command == "autoVerify":
                model_path = " ".join(args.model_path)
                base_path = " ".join(args.base_path)
                auto_verify_model(model_path, base_path, args.type, args.verifyta_path)
            elif args.command == "verifyLog":
                model_path = " ".join(args.model_path)
                log_path = " ".join(args.log_file_path)
                verify_log(model_path, log_path, args.verifyta_path, args.valid_only)
            elif args.command == "q":
                print("Goodbye!")
                break
        except SystemExit:
            # Handle argparse exiting on errors
            print("Invalid command. Type '-h' or '--help' for valid commands")

if __name__ == "__main__":
    main()