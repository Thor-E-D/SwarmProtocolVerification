import pytest
import os
import subprocess
#from src.Model import parseJsonFiles, createModel, save_xml_to_file
from Model import parseJsonFiles, createModel, save_xml_to_file
from JSONParser import parse_time_JSON
from typing import List, Dict

verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta"

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

def do_full_test(base_path: str, names_of_files: List[str], name_of_query_file: str, name_amount_dict: Dict[str,int], loop_counter: int, standardSetting: bool, time_file: str = ""):
    paths = []
    for name in names_of_files:
        paths.append(base_path + f"\\{name}.json")

    if (time_file != ""):
        time_file = parse_time_JSON(base_path + f"\\{time_file}.json")
    else:
        time_file = None

    jsonTransfers = parseJsonFiles(paths)

    currentModel = createModel(jsonTransfers, name_amount_dict, loop_counter, standardSetting, time_file)
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

