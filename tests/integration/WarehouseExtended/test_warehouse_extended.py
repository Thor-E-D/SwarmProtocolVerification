import pytest
import os
import subprocess
#from src.Model import parseJsonFiles, createModel, save_xml_to_file
from Model import parseJsonFiles, createModel, save_xml_to_file

verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta"


@pytest.mark.integration
def test_warehouse_extended():
    base_path = os.path.dirname(os.path.abspath(__file__))
    print(base_path)
    paths = [base_path + "\\Door.json", base_path + "\\Forklift.json", base_path + "\\Transport.json"]

    jsonTransfers = parseJsonFiles(paths)

    name_amount_dict = {}
    for jsonTransfer in jsonTransfers:
            name_amount_dict[jsonTransfer.name] = 1

    currentModel = createModel(jsonTransfers, name_amount_dict)
    save_xml_to_file(currentModel, "example_file", base_path)

    model_path = base_path + "\\example_file.xml"
    query_string = base_path + "\\query_file.txt"

    command = [verifyta_path,model_path , query_string]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.fail(result.stderr)
    
    output = result.stdout
    lines = output.splitlines()
    satisfied_count = sum(1 for line in lines if "Formula is satisfied." in line)
    
    expected_satisfied_count = 2

    assert satisfied_count == expected_satisfied_count, \
        f"Not all formulas were satisfied. Expected {expected_satisfied_count}, but found {satisfied_count}."


@pytest.mark.integration
def test_warehouse_two_transport_two_forklift():
    base_path = os.path.dirname(os.path.abspath(__file__))
    print(base_path)
    paths = [base_path + "\\Door.json", base_path + "\\Forklift.json", base_path + "\\Transport.json"]

    jsonTransfers = parseJsonFiles(paths)

    name_amount_dict = {}
    for jsonTransfer in jsonTransfers:
        if (jsonTransfer.name == "Forklift" or jsonTransfer.name == "Transport"):
            name_amount_dict[jsonTransfer.name] = 2
        else:
            name_amount_dict[jsonTransfer.name] = 1

    currentModel = createModel(jsonTransfers, name_amount_dict)
    save_xml_to_file(currentModel, "example_file", base_path)

    model_path = base_path + "\\example_file.xml"
    query_string = base_path + "\\query_file2.txt"

    command = [verifyta_path,model_path , query_string]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.fail(result.stderr)
    
    output = result.stdout
    lines = output.splitlines()
    satisfied_count = sum(1 for line in lines if "Formula is satisfied." in line)
    
    expected_satisfied_count = 3

    assert satisfied_count == expected_satisfied_count, \
        f"Not all formulas were satisfied. Expected {expected_satisfied_count}, but found {satisfied_count}."