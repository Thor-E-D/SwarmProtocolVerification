import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType

@pytest.mark.integration
def test_pump_robot():
    name_of_query_file = "query_file"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    model_settings = ModelSettings({"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = False
    model_settings.delay_amount = {"Robot": 2, "Pump": 2}
    model_settings.log_size = 13

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, name_amount_dict, model_settings, name_of_query_file)

    
@pytest.mark.integration
def test_pump_robot_standard_setting():
    name_of_query_file = "query_file_standard"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    model_settings = ModelSettings({"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = {"Robot": 1, "Pump": 1}
    model_settings.log_size = 10

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, name_amount_dict, model_settings, name_of_query_file)


@pytest.mark.integration
def test_pump_robot_time():
    name_of_query_file = "query_file_time1"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    model_settings = ModelSettings({"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = {"Robot": 1, "Pump": 1}
    model_settings.log_size = 10

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, name_amount_dict, model_settings, name_of_query_file, time_file="time1")


@pytest.mark.integration
def test_pump_robot_timed_log():
    name_of_query_file = "query_file_time2"

    name_amount_dict = {"Robot": 2, "Pump": 1}

    model_settings = ModelSettings({"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = {"Robot": 1, "Pump": 1}
    model_settings.log_size = 10

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, name_amount_dict, model_settings, name_of_query_file, time_file="time2")