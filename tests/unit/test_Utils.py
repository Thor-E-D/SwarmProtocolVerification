import pytest
from Utils import Utils
from DataObjects.Location import Location

@pytest.mark.unit
def test_get_eventtype_UID():
    test_string = "hej"
    result_string = Utils.get_eventtype_UID(test_string)
    expected_string = "hej_ID"
    assert result_string == expected_string

@pytest.mark.unit
def test_find_midpoint():

    l1 = Location (id = Utils.get_next_id(), x=10, y=0)
    l2 = Location (id = Utils.get_next_id(), x=0, y=10)

    (x1, y1) = Utils.find_midpoint(l1,l2)

    assert x1 == 5
    assert y1 == 5

@pytest.mark.unit
def test_python_list_to_uppaal_list():
    int_array = [1,2,3,4]
    res = Utils.python_list_to_uppaal_list(int_array)
    assert res == "{1, 2, 3, 4}"
