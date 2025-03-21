import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType

@pytest.mark.integration
def test_warehouse_extended():
    name_of_query_file = "query_file"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 1}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_SELF_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_SELF_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Door": 1, "Forklift": 1, "Transport": 1}
    model_settings.log_size = 16

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)


@pytest.mark.integration
def test_warehouse_two_transport():
    name_of_query_file = "query_file2"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_SELF_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_SELF_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Door": 1, "Forklift": 1, "Transport": 1}
    model_settings.log_size = 25

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)

@pytest.mark.integration
def test_warehouse_two_transports_time():
    name_of_query_file = "query_file_time"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Door": 3, "Forklift": 1, "Transport": 2}
    model_settings.log_size = 16

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file, time_file="time")

@pytest.mark.integration
def test_warehouse_two_transports_global_emitted_no_branch_tracking():
    name_of_query_file = "query_file4"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_EMITTED})
    model_settings.branch_tracking = False
    model_settings.delay_amount = {"Door": 5, "Forklift": 1, "Transport": 3}
    model_settings.log_size = 20

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)

@pytest.mark.integration
def test_warehouse_two_transports_global_emitted():
    name_of_query_file = "query_file3"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Door": 5, "Forklift": 1, "Transport": 3}
    model_settings.log_size = 15

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)

@pytest.mark.integration
def test_warehouse_two_transports_eventual_fidelity():
    name_of_query_file = "query_file5"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_EMITTED})
    model_settings.branch_tracking = True
    model_settings.path_bound = 1
    model_settings.delay_amount = {"Door": 2, "Forklift": 2, "Transport": 2}
    model_settings.log_size = 20

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)