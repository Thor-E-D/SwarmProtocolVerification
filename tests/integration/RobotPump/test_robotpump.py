import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType

    
@pytest.mark.integration
def test_pump_robot_standard_setting():
    name_of_query_file = "query_file_standard"
    model_settings = ModelSettings({"Robot": 2, "Pump": 1}, {"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Robot": 1, "Pump": 1}
    model_settings.log_size = 10

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)


@pytest.mark.integration
def test_pump_robot_time():
    name_of_query_file = "query_file_time1"
    model_settings = ModelSettings({"Robot": 2, "Pump": 1}, {"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Robot": 1, "Pump": 1}
    model_settings.log_size = 10

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file, time_file="time1")


@pytest.mark.integration
def test_pump_robot_timed_log():
    name_of_query_file = "query_file_time2"
    model_settings = ModelSettings({"Robot": 2, "Pump": 1}, {"Robot": DelayType.EVENTS_SELF_EMITTED, "Pump": DelayType.EVENTS_SELF_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"Robot": 1, "Pump": 1}
    model_settings.log_size = 10

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file, time_file="time2")