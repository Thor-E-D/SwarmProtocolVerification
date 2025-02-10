import pytest
import os

from JSONParser import Edge, parse_protocol_JSON_file

base_path = os.path.dirname(os.path.abspath(__file__))
folder_name = "TestCaseBranchingProjections"
path_to_folder = os.path.join(base_path, folder_name)
path_to_json = os.path.join(path_to_folder, "SwarmProtocol.json")

@pytest.mark.unit
def test_edge_comparison():
    e1 = Edge("name", "l1", "l2", "role")
    e2 = Edge("name", "l1", "l2", "role")

    assert e1 == e2
    assert e1 != []

def test_parse_protocol_JSON_file():
    _, jsonTransfers = parse_protocol_JSON_file(path_to_json)

    subscriptions_dict = {"R1": ['e34', 'e17', 'e12', 'e35', 'e23'], "R2": ['e79', 'e78', 'e96', 'e17', 'e12'], "R": ['e46', 'e56', 'e23', 'e79', 'e86', 'e78', 'e17', 'e12', 'e34', 'e35']}
    for jsonTransfer in jsonTransfers:
        assert sorted(subscriptions_dict[jsonTransfer.name]) == sorted(jsonTransfer.subscriptions)