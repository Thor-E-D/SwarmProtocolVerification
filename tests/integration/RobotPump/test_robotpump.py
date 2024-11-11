import pytest
import os
import subprocess
#from src.Model import parseJsonFiles, createModel, save_xml_to_file
from Model import parseJsonFiles, createModel, save_xml_to_file

verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta"


@pytest.mark.integration
def test_pump_robot():
    base_path = os.path.dirname(os.path.abspath(__file__))
    print(base_path)
    paths = [base_path + "\\Robot.json", base_path + "\\Pump.json"]

    jsonTransfers = parseJsonFiles(paths)

    name_amount_dict = {}
    for jsonTransfer in jsonTransfers:
        if (jsonTransfer.name == "Robot"):
            name_amount_dict[jsonTransfer.name] = 2
        else:
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
    
    expected_satisfied_count = 6

    assert satisfied_count == expected_satisfied_count, \
        f"Not all formulas were satisfied. Expected {expected_satisfied_count}, but found {satisfied_count}."
