import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType

@pytest.mark.integration
def test_tricky_invariant_time():
    name_of_query_file = "query_file_time"
    model_settings = ModelSettings({"R": 2},{"R": DelayType.EVENTS_EMITTED})
    model_settings.path_bound = 1
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"R": 2}
    model_settings.log_size = 20

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file, time_file="time")

@pytest.mark.integration
def test_tricky_invariant_time_no_path_bound():
    name_of_query_file = "query_file_time2"
    model_settings = ModelSettings({"R": 2},{"R": DelayType.EVENTS_EMITTED})
    model_settings.path_bound = -1
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"R": 2}
    model_settings.log_size = 6

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file, time_file="time")