import pytest
import os
from test_utils import do_full_test
import copy
from DataObjects.ModelSettings import ModelSettings, DelayType


@pytest.mark.integration
def test_looping_loops():
    name_of_query_file = "query_file"

    model_settings = ModelSettings(None, None)
    model_settings.branch_tracking = True
    model_settings.delay_amount = None
    model_settings.log_size = 30

    base_path = os.path.dirname(os.path.abspath(__file__))

    do_full_test(base_path, model_settings, name_of_query_file)