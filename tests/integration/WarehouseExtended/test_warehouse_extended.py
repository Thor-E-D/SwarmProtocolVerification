import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType

@pytest.mark.integration
def test_warehouse_extended():
    name_of_query_file = "query_file"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 1}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_SELF_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = False
    model_settings.delay_amount = {"Door": 1, "Forklift": 1, "Transport": 1}
    model_settings.log_size = 16

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)


@pytest.mark.integration
def test_warehouse_two_transport_two_forklift():
    name_of_query_file = "query_file2"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_SELF_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = {"Door": 1, "Forklift": 1, "Transport": 1}
    model_settings.log_size = 16

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)

@pytest.mark.integration
def test_warehouse_two_transports_time():
    name_of_query_file = "query_file_time"

    name_amount_dict = {"Door": 1, "Forklift": 1, "Transport": 2}

    model_settings = ModelSettings(name_amount_dict, {"Door": DelayType.EVENTS_SELF_EMITTED, "Forklift": DelayType.EVENTS_SELF_EMITTED, "Transport": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = {"Door": 1, "Forklift": 1, "Transport": 1}
    model_settings.log_size = 16

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file, time_file="time")