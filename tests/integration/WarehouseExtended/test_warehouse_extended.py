import pytest
import os
from test_utils import do_full_test

@pytest.mark.integration
def test_warehouse_extended():
    names_of_files = ["Door", "Forklift", "Transport"]
    name_of_query_file = "query_file"

    name_amount_dict = {}
    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 1}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = False)


@pytest.mark.integration
def test_warehouse_two_transport_two_forklift():
    names_of_files = ["Door", "Forklift", "Transport"]
    name_of_query_file = "query_file2"

    name_amount_dict = {}
    name_amount_dict = {"Door": 1, "Forklift": 2, "Transport": 2}

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, names_of_files, name_of_query_file, name_amount_dict, loop_counter = 2, standardSetting = False)