import argparse
import json
import os
import subprocess
from DataObjects.Model import Model
from DataObjects.ModelSettings import DelayType, ModelSettings
from JSONParser import Graph, parse_time_JSON, parse_projection_JSON_file, parse_protocol_seperatly, parse_protocol_JSON_file, build_graph
from ModelBuilder import createModel, save_xml_to_file
from typing import Dict
import re

state_path = "PermanentState\\state.json"
base_path = os.path.dirname(os.path.abspath(__file__)) 
current_model = None

# Mapping user-friendly strings to DelayType values
DELAY_TYPE_MAPPING = {
    "N": DelayType.NOTHING,
    "E": DelayType.EVENTS_EMITTED,
    "S": DelayType.EVENTS_SELF_EMITTED
}

def identify_json_files(folder_path):
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

def get_state_data(key, file_path = ""):
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
    except Exception as e:
        print(f"Unexpected error: {e}")


def update_local_state(key, value):
    try:
        file_path = os.path.join(base_path, state_path)
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        
        if (key == ""):
            data = value
        else:
            data[key] = value
        
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Successfully updated {key} in state with {data[key]}")
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def write_state_to_path(path: str):
    try:
        file_path = os.path.join(base_path, state_path)
        # Read the existing data from the file
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Successfully wrote json to {path}")
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def load_state_from_path(path: str):
    try:
        file_path = os.path.join(base_path, state_path)
        with open(path, 'r') as json_file:
            data = json.load(json_file)
        
        json_required_keys = [
        "verifyta_path",
        "base_path",
        "delay_type",
        "loop_bound",
        "standard_setting",
        "log_size",
        "delay_amount",
        "subsets",
        "role_amount"
        ]

        for key in json_required_keys:
            if key not in data:
                print (f"Fault format missing key {key} in given json")
                return 

        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Successfully loaded json into local state")
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def load_state_into_model_settings(state_data):
    model_settings = ModelSettings(role_amount=state_data["role_amount"],delay_type=state_data["delay_type"])
    model_settings.loop_bound = state_data["loop_bound"]
    model_settings.standard_setting = state_data["standard_setting"]
    model_settings.log_size = state_data["log_size"]
    model_settings.delay_amount = state_data["delay_amount"]

    return model_settings

def build_model(args):
    # Load model settings:
    state_data = None
    if args.path_to_state == None:
        state_data = get_state_data("")
    else:
        state_data = get_state_data("", args.path_to_state)

    model_settings = load_state_into_model_settings(state_data)

    if model_settings.role_amount == None:
        print("No role amount set please set using setArgs -ra")
        return
    if model_settings.delay_type == None:
        print("No delay type set please set using setArgs -dta")
        return
    if model_settings.delay_amount == None:
        print("No delay amount set please set using setArgs -daa")
        return

    path_to_files = None
    if args.path_to_folder == None:
        path_to_files = get_state_data("base_path")
    else:
        path_to_files = args.path_to_folder

    print(f"Attempt to identify relevant json files at local location {path_to_files}")
    
    projection_json_files, protocol_json_file, time_json_file = identify_json_files(path_to_files)

    if protocol_json_file == None:
        print("Cannot find protocol JSON aborting attempt")
        print("Please review the folder path with \"setPath\" and \"showPath\"")
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
            update_local_state("verifyta_path", newPath)
        else:
            print(f"Tool found at {newPath} but returned error code: {result.returncode}")
            print(f"Error Output: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error occurred while verifying the tool: {e}")

def get_lines_in_file(file_path: str):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return lines
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def filter_ouput(file_path_input: str) -> str:
    # Define regular expressions for the patterns
    state_pattern = re.compile(r"State:")
    transition_pattern = re.compile(r"Transition:")
    propagation_pattern = re.compile(r"l_prop[0-9]->")
    property_satisfied_pattern = re.compile(r"-- Formula is satisfied.")

    result = ""

    # Open the input file for reading and the output file for writing
    with open(file_path_input, "r") as infile:
        next_is_state = False
        next_is_transition = False
        current_state = None

        content = infile.read()
        if (property_satisfied_pattern.search(content) != None):
            return "Query was satisfied \n"
        else:
            result += "Query not satified. Printing Trace: \n"
        
        for line in content.splitlines():
            state_match = state_pattern.search(line)

            if state_match != None:
                next_is_state = True
                continue

            if next_is_state:
                lines_to_save = [role for role in line.split() if "log" not in role and role != "(" and role != ")"]
                if lines_to_save != current_state:
                    result += (f"State: {lines_to_save}\n")
                    current_state = lines_to_save
                next_is_state = False
            
            transition_match = transition_pattern.search(line)
            if transition_match != None:
                next_is_transition = True
                continue
            
            if next_is_transition:
                propagation_match = propagation_pattern.search(line)
                transition = line.partition("{")[0]
                if propagation_match != None:
                    role = line.partition("_log")[0]
                    result += (f"Role {role} propagted to all other roles\n")
                if "_log" not in transition:
                    result += (f"Transition: {transition}\n")
                next_is_transition = False
    
    return result

def verify_model(model_path, query_path, verifyta_path):
    if verifyta_path == None:
        verifyta_path = get_state_data("verifyta_path")
    else:
        verifyta_path = " ".join(verifyta_path)
    
    queries = get_lines_in_file(query_path)

    for i in range(len(queries)):
        print(f"Verifying query {i}: {queries[i]}")
        #command = [verifyta_path, model_path, query_path, "--query-index", f"{i}","--diagnostic", "0", "--save-trace", "C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\SingleLoop\\trace.txt"]
        command = [verifyta_path, model_path, query_path, "--query-index", f"{i}","--diagnostic", "0"]
        #result = subprocess.run(command, capture_output=True, text=True)
        output_file = "trace.txt"
        file_path = os.path.join(base_path, state_path[:-11], output_file)

        # Run the command and write the output directly to the file
        with open(file_path, "w") as file:
            subprocess.run(command, stdout=file, stderr=subprocess.STDOUT, text=True)
        
        # We must filter the output file into a format that the user can understand
        filtered_output = filter_ouput(file_path)
        print(filtered_output)


def parse_json_dict(key, json_input):
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
                    print("Provided delay amount dictionary must be of the shape {str, Delay Type}")
                    return
                new_delay_type = {}
                for key in updates:
                    new_delay_type[key] = DELAY_TYPE_MAPPING[updates[key]]
                update_local_state(key, updates)
            #update_state_file(key,updates)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input. {e}")

def set_arguments(args):
    if args.standard_setting != None:
        update_local_state("standard_setting", args.standard_setting)

    if args.log_size != None:
        update_local_state("log_size", args.log_size)

    if args.loop_counter != None:
        update_local_state("loop_bound", args.loop_bound)

    if args.delay_type_all != None:
        args.delay_type_all = " ".join(args.delay_type_all)
        parse_json_dict("delay_type", args.delay_type_all)

    if args.delay_amount_all != None:
        args.delay_amount_all = " ".join(args.delay_amount_all)
        parse_json_dict("delay_amount", args.delay_amount_all)

    if args.role_amount != None:
        args.role_amount = " ".join(args.role_amount)
        parse_json_dict("role_amount", args.role_amount)

def set_base_path(path_to_files):
    update_local_state("base_path", path_to_files)

def create_parser():
    parser = argparse.ArgumentParser(description="Model cheking swarm protocols CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # For setting 
    set_uppaal_path_parser = subparsers.add_parser("setVer", help="Set the path to a verifyta distribution")
    set_uppaal_path_parser.add_argument(
        "path",
        type=str,
        nargs='+',
        help="The absolute path to a verifyta distribution"
    )

    subparsers.add_parser("showVer", help="Displays the current path to a verifyta distribution")

    base_path_parser = subparsers.add_parser("setPath", help="Sets the path to the folder containing relevant json files")
    base_path_parser.add_argument(
        "path",
        type=str,
        nargs='+',
        help="The absolute path to a folder with relevant json files"
    )

    subparsers.add_parser("showPath", help="Displays the path to the folder containing relevant json files")

    # For the builder
    build_parser = subparsers.add_parser("build", help="build the model")
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
        help="Path to json files containing state information. Default is currently saved",
        required=False
    )

    # For setting arguments for the verifier
    argument_parser = subparsers.add_parser("setArgs", help="set the arguments for the build")
    argument_parser.add_argument(
        "-log", "--log-size",
        type=int,
        help="Size of the log that will be used within UPPAAL",
        required=False
    )

    argument_parser.add_argument(
        "-loop", "--loop-counter",
        type=int,
        help="Maximum amount of times a loop in the model can be taken",
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
        "-ss", "--standard-setting",
        type=bool,
        help="Wether or not to use standard setting default is false",
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

    load_state_parser = subparsers.add_parser("loadState", help="load state from path")
    load_state_parser.add_argument(
        "path",
        type=str,
        nargs='+',
        help="The absolute path to the desired json file",
    )

    write_state_parser = subparsers.add_parser("writeState", help="write state to path")
    write_state_parser.add_argument(
        "path",
        type=str,
        nargs='+',
        help="The absolute path to where the file should be saved"
    )

    verify_parser = subparsers.add_parser("verify", help="Verify a given model")
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
            if args.command == "setVer":
                full_path = " ".join(args.path)
                set_verifyta_path(full_path)
            elif args.command == "showVer":
                verifyta_path = get_state_data("verifyta_path")
                print(f"Current path to verifyta set to: {verifyta_path}")
            elif args.command == "setPath":
                full_path = " ".join(args.path)
                set_base_path(full_path)
            elif args.command == "showPath":
                path_to_files = get_state_data("base_path")
                print(f"Current path to relevant folder set to: {path_to_files}")
            elif args.command == "build":
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
            elif args.command == "q":
                print("Goodbye!")
                break
        except SystemExit:
            # Handle argparse exiting on errors
            print("Invalid command. Type '-h' or '--help' for assistance.")

if __name__ == "__main__":
    main()