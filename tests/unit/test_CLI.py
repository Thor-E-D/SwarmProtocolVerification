import pytest
from unittest.mock import patch
from io import StringIO
import os
import json
from typing import List

from CLI import main, save_xml_to_file, get_state_data, update_local_state

base_path = os.path.dirname(os.path.abspath(__file__))
verifyta_path = "C:\\Program Files\\UPPAAL-5.1.0-beta5\\app\\bin\\verifyta.exe"

# Paths to internal TestCase
folder_name = "TestCase"
path_to_folder = os.path.join(base_path, folder_name)
path_to_state =  os.path.join(path_to_folder, "state.json")
path_to_test_state = os.path.join(path_to_folder, "test_state.json")
path_to_query_file = os.path.join(path_to_folder, "query_file.txt")
path_to_log = os.path.join(path_to_folder, "log.txt")
path_to_model = os.path.join(path_to_folder, "uppaal_model.xml")

# Paths to internal TestCaseProjection
folder_name_projection = "TestCaseProjection"
path_to_folder_projection = os.path.join(base_path, folder_name_projection)
path_to_model_projection = os.path.join(path_to_folder_projection, "uppaal_model.xml")
path_to_test_state_projection = os.path.join(path_to_folder_projection, "test_state.json")

#Paths to faulty test cases
folder_name_faulty = "TestCaseFaulty"
path_to_folder_faulty = os.path.join(base_path, folder_name_faulty)
path_to_model_faulty = os.path.join(path_to_folder_faulty, "uppaal_model.xml")
path_to_query_file_faulty = os.path.join(path_to_folder_faulty, "query_file.txt")
path_to_test_state_missing = os.path.join(path_to_folder_faulty, "test_state_missing.json")
path_to_test_state_delay_type = os.path.join(path_to_folder_faulty, "test_state_delay_type.json")
path_to_protocol_json_faulty = os.path.join(path_to_folder_faulty, "SwarmProtocol.json")
path_to_faulty_exe = os.path.join(path_to_folder_faulty, "fault.exe")
path_to_faulty_exe2 = os.path.join(path_to_folder_faulty, "verifyta.exe")

set_all_args_cmd = "setArgs -log 16 -path 1 -dta {\"Door\": \"E\", \"Forklift\": \"S\", \"Transport\": \"E\"} -bt t -daa {\"Door\": 2, \"Forklift\": 1, \"Transport\": 2} -ra {\"Door\": 1, \"Forklift\": 1, \"Transport\": 2}"

#Helper function
def run_and_assert(user_inputs: List[str], output_list: List[str]):
    with patch("builtins.input", side_effect=user_inputs), patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()
        for expected_output in output_list:
            assert expected_output in output

# Used when debugging
def run_and_print(user_inputs: List[str], output_list: List[str]):
    output = ""
    with patch("builtins.input", side_effect=user_inputs), patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()
    print(output)

# Test for the "Welcome" message
@pytest.mark.unit
def test_welcome_message():
    user_inputs = ["q"]  # Simulate user typing 'q' to quit
    expected_output = "Welcome to the File Organizer CLI!"
    output_list = [expected_output]

    run_and_assert(user_inputs,output_list)


# Test the help message
@pytest.mark.unit
def test_help_message():
    user_inputs = ["-h", "q"]  # Simulate user typing 'q' to quit
    expected_output = """positional arguments:
  {build,setArgs,showArgs,loadState,writeState,verify,autoVerify,verifyLog,q}"""

    output_list = [expected_output]

    run_and_assert(user_inputs,output_list)

@pytest.mark.unit
def test_verifyta_path():
    user_inputs = [f"setArgs -vp {verifyta_path}", f"setArgs -vp {verifyta_path[:-4]}", "showArgs", "q"]
    expected_output_setVer = f"Tool is present and working at: {verifyta_path}"
    expected_output_showArgs = f"'verifyta_path': '{verifyta_path.replace("\\", "\\\\")}',"

    output_list = [expected_output_setVer, expected_output_showArgs]

    run_and_assert(user_inputs,output_list)

@pytest.mark.unit
def test_base_path():
    user_inputs = [f"setArgs -pf {path_to_folder}", "showArgs", "q"]
    expected_output_setPath = f"Successfully updated base_path in state with {path_to_folder}"
    expected_output_showPath = f"'base_path': '{path_to_folder.replace("\\", "\\\\")}',"

    output_list = [expected_output_setPath, expected_output_showPath]

    run_and_assert(user_inputs,output_list)


@pytest.mark.unit
def test_setArgs():
    user_inputs = [set_all_args_cmd, "showArgs", "q"]
    expected_output = "'delay_type': {'Door': 'E', 'Forklift': 'S', 'Transport': 'E'}, 'path_bound': 1, 'branch_tracking': True, 'log_size': 16, 'delay_amount': {'Door': 2, 'Forklift': 1, 'Transport': 2}, 'role_amount': {'Door': 1, 'Forklift': 1, 'Transport': 2}}"

    output_list = [expected_output]

    run_and_assert(user_inputs,output_list)

@pytest.mark.unit
def test_loading_writing_state():
    user_inputs = [set_all_args_cmd, f"writeState {path_to_state}", "setArgs -bt 0", f"loadState {path_to_state}", "showArgs", "q"]
    expected_output = "'branch_tracking': True"

    output_list = [expected_output]

    run_and_assert(user_inputs,output_list)

    # Compare the two new json file with the test one
    with open(path_to_state, 'r') as f:
        state_date = json.load(f)
    
    with open(path_to_test_state, 'r') as f:
        test_state_date = json.load(f)

    assert state_date == test_state_date

    # Remove the state file
    os.remove(path_to_state)

@pytest.mark.unit
def test_build_and_verify():
    user_inputs = [f"build -pf {path_to_folder} -ps {path_to_test_state}", f"verify {path_to_model} {path_to_query_file}", "q"]
    
    expected_output_build = """No projection files found so auto-generating projections
Found a time json file!
XML file saved successfully at"""

    expected_output_verify = """Verifying query 0: A[] Transport(0).l2 imply globalTime <= 75
Query not satisfied"""

    expected_output_verify_intitial = ['Forklift(0).l1', 'Door(0).l0', 'Transport(0).l0', 'Transport(1).l0']

    output_list = [expected_output_build, expected_output_verify]
    output_list.extend(expected_output_verify_intitial)

    run_and_assert(user_inputs,output_list)

    os.remove(path_to_model)

@pytest.mark.unit
def test_build_and_autoverify():
    user_inputs = [set_all_args_cmd, f"build", f"autoVerify {path_to_model} {path_to_folder} --type validity",
                   f"autoVerify {path_to_model} {path_to_folder} --type sizebound -vp {verifyta_path}",
                    f"autoVerify {path_to_model} {path_to_folder} --type timebound -vp {verifyta_path}" , "q"]
    
    expected_output_build = """No projection files found so auto-generating projections
Found a time json file!
XML file saved successfully at"""

    expected_output_verify_validity = "Query was satisfied"
    expected_output_verify_sizebound = "Recommended log size: 13"
    expected_output_verify_timebound = """
Transport has the following time bounds
Location l0: [0,2]
Location l1: [2,20],[29,217]
Location l2: [5,173]
Location l3: [29,186]
Location l4: [2,INF]"""

    output_list = [expected_output_build, expected_output_verify_validity, expected_output_verify_sizebound, expected_output_verify_timebound]

    run_and_assert(user_inputs,output_list)
    #run_and_print(user_inputs,output_list)
    

    os.remove(path_to_model)

@pytest.mark.unit
def test_build_projection_and_autoverify():
    user_inputs = [set_all_args_cmd, f"build -pf {path_to_folder_projection} -ps {path_to_test_state_projection}", f"autoVerify {path_to_model_projection} {path_to_folder_projection} --type sizebound", "q"]

    expected_output_build = ["Missing the following projections", "No time file found", "XML file saved successfully at"]

    expected_output_verify_sizebound = "Model overflow!! Cannot find optimal logsize"

    output_list = [expected_output_verify_sizebound]
    output_list.extend(expected_output_build)

    run_and_assert(user_inputs,output_list)

    os.remove(path_to_model_projection)


@pytest.mark.unit
def test_build_and_verifyLog():
    user_inputs = [f"build -pf {path_to_folder} -ps {path_to_test_state}",
                   f"verifyLog {path_to_model} {path_to_log}" , "q"]
    
    expected_output_build = """No projection files found so auto-generating projections
Found a time json file!
XML file saved successfully at"""

    expected_output_verifyLog = """Verifying query: E<> globalLog[0].eventID == Open_ID and globalLog[1].eventID == Request_ID and globalLog[2].eventID == Get_ID and globalLog[3].eventID == Deliver_ID and globalLog[4].eventID == Close_ID and globalLog[4].orderCount != 0
Query was satisfied"""

    output_list = [expected_output_build, expected_output_verifyLog]

    run_and_assert(user_inputs,output_list)

    os.remove(path_to_model)

@pytest.mark.unit
def test_build_and_verifyTrueLog():
    user_inputs = [f"build -pf {path_to_folder} -ps {path_to_test_state}",
                   f"verifyLog {path_to_model} {path_to_log} -vo True" , "q"]
    
    expected_output_build = """No projection files found so auto-generating projections
Found a time json file!
XML file saved successfully at"""

    expected_output_verifyLog = """Verifying query: E<> trueGlobalLog[0].eventID == Open_ID and trueGlobalLog[1].eventID == Request_ID and trueGlobalLog[2].eventID == Get_ID and trueGlobalLog[3].eventID == Deliver_ID and trueGlobalLog[4].eventID == Close_ID and trueGlobalLog[4].orderCount != 0
Query was satisfied"""

    output_list = [expected_output_build, expected_output_verifyLog]

    run_and_assert(user_inputs,output_list)

    os.remove(path_to_model)
# ------------------------------------------- test cases for wrong inputs --------------------------------------

@pytest.mark.unit
def test_save_xml_to_file():

    expected_output = "An error occurred while saving the file: [Errno 2] No such file or directory: 'NOTADIRECTORWITHTHISNAME/NOTAFILENAME.xml'"

    with patch("builtins.input", side_effect=[]), patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        save_xml_to_file("", "NOTAFILENAME","NOTADIRECTORWITHTHISNAME")
        output = mock_stdout.getvalue()
        assert expected_output in output


@pytest.mark.unit
def test_build_faulty():
    user_inputs = [f"build -pf {path_to_folder_faulty}", "build -pf helloImNotAFolder" , "q"]
    
    expected_output1 = "Invalid JSON file found: SwarmProtocol.json"

    expected_output2 = "No folder identified at"

    output_list = [expected_output1, expected_output2]

    run_and_assert(user_inputs, output_list)

@pytest.mark.unit
def test_get_state_data():

    expected_output1 = "Error: NOTADIRECTORWITHTHISNAME not found."
    expected_output2 = "Error decoding JSON: Expecting value: line 1 column 1 (char 0)"

    with patch("builtins.input", side_effect=[]), patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        get_state_data("","NOTADIRECTORWITHTHISNAME")
        get_state_data("",path_to_protocol_json_faulty)
        output = mock_stdout.getvalue()
        assert expected_output1 in output
        assert expected_output2 in output

@pytest.mark.unit
def test_write_state_to_path():
    user_inputs = ["writeState NOTADIRECTORWITHTHISNAME\\", f"writeState {folder_name_faulty}" + "\\fail", "q"]
    expected_output1 = "Unexpected error: [Errno 22] Invalid argument: 'NOTADIRECTORWITHTHISNAME\\\\'"
    expected_output2 = "Error: Could not write to TestCaseFaulty\\fail. Make sure it ends in a file name"

    output_list = [expected_output1, expected_output2]

    run_and_assert(user_inputs,output_list)

@pytest.mark.unit
def test_load_state():
    user_inputs = [f"loadState {path_to_test_state_missing}",f"loadState {path_to_protocol_json_faulty}","loadState NOTADIRECTORWITHTHISNAME", "q"]
    expected_output1 = "Fault format missing key path_bound in given json"
    expected_output2 = "Error decoding JSON: Expecting value: line 1 column 1 (char 0)"
    expected_output3 = "Error: NOTADIRECTORWITHTHISNAME not found."

    output_list = [expected_output1, expected_output2, expected_output3]

    run_and_assert(user_inputs, output_list)

@pytest.mark.unit
def test_build_faults():
    user_inputs = [f"build -pf {path_to_folder} -ps {path_to_test_state_missing}", f"build -pf {path_to_folder} -ps {path_to_test_state_delay_type}",f"build -pf {path_to_folder_faulty} -ps {path_to_test_state_delay_type}", "q"]
    expected_output1 = "Failed to build with exception string indices must be integers, not 'str'"
    expected_output2 = "Cannot find protocol JSON aborting attempt"
    expected_output3 = "Fault format missing key path_bound in given json"

    output_list = [expected_output1, expected_output2, expected_output3]

    run_and_assert(user_inputs, output_list)

@pytest.mark.unit
def test_verifyta_path_faults():
    user_inputs = [f"setArgs -vp {verifyta_path[:-13]}", f"setArgs -vp {verifyta_path} + fail",f"setArgs -vp {path_to_faulty_exe}",f"setArgs -vp {path_to_faulty_exe2}", "q"]
    expected_output1 = "Tool is present and working at:"
    expected_output2 = "Tool not found at path"
    expected_output3 = "Error occurred while verifying the tool:"
    expected_output4 = "Not a verifyta distribution. Aborting"


    output_list = [expected_output1, expected_output2, expected_output3, expected_output4]

    run_and_assert(user_inputs, output_list)


@pytest.mark.unit
def test_verify_faults():
    user_inputs = [f"verify {path_to_model} NotAPath", f"verify {path_to_model} {path_to_faulty_exe2}", "q"]
    expected_output1 = "Error: The file 'NotAPath' does not exist"
    expected_output2 = "An error occurred when reading file at"

    output_list = [expected_output1, expected_output2]

    run_and_assert(user_inputs, output_list)

@pytest.mark.unit
def test_build_and_verify_fault():
    user_inputs = [f"build -pf {path_to_folder} -ps {path_to_test_state}", f"verify {path_to_model} {path_to_query_file_faulty} -vp {verifyta_path}", "q"]
    
    expected_output1 = "[error] has no member named LocationThatDoesNotExists"

    output_list = [expected_output1]

    run_and_assert(user_inputs, output_list)

    os.remove(path_to_model)

@pytest.mark.unit
def test_setArgs_faults():
    user_inputs = ["","asd", "setArgs -dta {\"Door\": \"FAIL\"} -daa {\"Door\": \"FAIL\"} -ra {\"Door\": \"FAIL\"}"
                   , "setArgs -dta {\"Door\": FAIL}", "setArgs -dta {\"Door\": FAIL}", "setArgs -bt fail"
                   "setArgs -dta [1,2,3]", "q"]
    expected_output1 = "Provided delay type dictionary must be of the shape {str, Delay Type}"
    expected_output2 = "Provided delay amount dictionary must be of the shape {str, int}"
    expected_output3 = "Provided role amount dictionary must be of the shape {str, int}"
    expected_output4 = "Error: Invalid JSON input. Expecting value: line 1 column 10 (char 9)"
    expected_output5 = "Boolean value expected. Got fail"
    expected_output6 = "Provided JSON must represent a dictionary"

    output_list = [expected_output1, expected_output2, expected_output3, expected_output4, expected_output5, expected_output6]

    run_and_assert(user_inputs, output_list)

@pytest.mark.unit
def test_auto_verification_fault():
    user_inputs = [set_all_args_cmd, f"build -pf {path_to_folder_projection} -ps {path_to_test_state_projection}", f"autoVerify {path_to_model_projection} {path_to_folder_faulty} --type validity", "q"]

    expected_output_verify_validity = "Invalid JSON file found: SwarmProtocol.json"

    output_list = [expected_output_verify_validity]

    run_and_assert(user_inputs, output_list)

    os.remove(path_to_model_projection)
