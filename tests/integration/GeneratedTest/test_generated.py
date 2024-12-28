import pytest
import os
from test_utils import do_full_test
from DataObjects.ModelSettings import ModelSettings, DelayType


@pytest.mark.integration
def test_generated_file():
    name_of_query_file = "query_file"
    model_settings = ModelSettings({"R48": 1, "R49": 2}, {"R48": DelayType.EVENTS_SELF_EMITTED, "R49": DelayType.EVENTS_SELF_EMITTED})
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = {"R48": 1, "R49": 1}
    model_settings.log_size = 12

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings)