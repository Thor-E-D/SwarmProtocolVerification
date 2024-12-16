import pytest
import os
from test_utils import do_full_test

@pytest.mark.integration
def test_branch_join():
    names_of_files = ["R", "O"]
    name_of_query_file = "query_file"

    name_amount_dict = {"O": 1, "R": 2}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = True)
    

@pytest.mark.integration
def test_branch_join_time():
    names_of_files = ["R", "O"]
    name_of_query_file = "query_file_time"

    name_amount_dict = {"O": 1, "R": 2}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = True, time_file="time")
