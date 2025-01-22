import pytest
import os
from test_utils import do_full_test
import copy
from DataObjects.ModelSettings import ModelSettings, DelayType

# Test every protocol nested in directories in the directory protocols
@pytest.mark.integration
def test_generated_file():
    model_settings = ModelSettings(None, None)
    model_settings.loop_counter = 2
    model_settings.standard_setting = True
    model_settings.delay_amount = None
    model_settings.log_size = None

    base_path = os.path.dirname(os.path.abspath(__file__))
    directory_path = os.path.join(base_path, "Protocols")

    try:
        # Get all folders in dir
        entries = os.listdir(directory_path)
        folders = [entry for entry in entries if os.path.isdir(os.path.join(directory_path, entry))]
    except:
        folders = []

    for folder in folders:
        if folder != "2_max_10_roles_max_10_commands":
            folder_path = os.path.join(directory_path, folder)
            do_full_test(folder_path, copy.deepcopy(model_settings))