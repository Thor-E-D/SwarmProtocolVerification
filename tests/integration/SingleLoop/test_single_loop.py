import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType

@pytest.mark.integration
def test_single_loop():
    name_of_query_file = "query_file"
    model_settings = ModelSettings({"O": 1, "R": 2}, {"O": DelayType.EVENTS_EMITTED, "R": DelayType.EVENTS_EMITTED})
    model_settings.branch_tracking = True
    model_settings.delay_amount = {"O": 1, "R": 2}
    model_settings.log_size = 16

    base_path = os.path.dirname(os.path.abspath(__file__))
    do_full_test(base_path, model_settings, name_of_query_file)

@pytest.mark.integration
def test_single_loop_no_branch_tracking():
    name_of_query_file = "query_file2"
    model_settings = ModelSettings({"O": 1, "R": 2}, {"O": DelayType.EVENTS_SELF_EMITTED, "R": DelayType.EVENTS_SELF_EMITTED})
    model_settings.branch_tracking = False
    model_settings.delay_amount = {"O": 1, "R": 1}
    model_settings.log_size = 9

    base_path = os.path.dirname(os.path.abspath(__file__))
    do_full_test(base_path, model_settings, name_of_query_file)
