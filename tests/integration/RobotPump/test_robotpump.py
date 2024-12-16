import pytest
import os
from test_utils import do_full_test

@pytest.mark.integration
def test_pump_robot():
    names_of_files = ["Robot", "Pump"]
    name_of_query_file = "query_file"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = False)

    
@pytest.mark.integration
def test_pump_robot_standard_setting():
    names_of_files = ["Robot", "Pump"]
    name_of_query_file = "query_file_standard"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = True)


@pytest.mark.integration
def test_pump_robot_time():
    names_of_files = ["Robot", "Pump"]
    name_of_query_file = "query_file_time"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = True, time_file="time")