import pytest

from JSONParser import Edge

@pytest.mark.unit
def test_edge_comparison():
    e1 = Edge("name", "l1", "l2", "role")
    e2 = Edge("name", "l1", "l2", "role")

    assert e1 == e2
    assert e1 != []