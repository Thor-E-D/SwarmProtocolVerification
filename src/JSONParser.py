"""\
Responsible for parsing JSON files such as
full protocol json, projection json and time json in
to either of the two json transfer classes.
Only works if jsons are formattet correctly.

Also capable of constructing projections.

"""

from dataclasses import dataclass
from typing import Dict, List, Any, Set
from pathlib import Path
import json
import copy
from collections import defaultdict

from DataObjects.JSONTransfer import JSONTransfer, EventData
from DataObjects.TimeJSONTransfer import LogTimeData, EventTimeData, TimeJSONTransfer

@dataclass
class Edge:
    name: str
    source: str
    target: str
    role: str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if not isinstance(other, Edge):
            return False
        return (self.name == other.name and 
                self.source == other.source and 
                self.target == other.target and
                self.role == other.role)

class Graph:
    def __init__(self):
        self.edges = set()
        self.initial = ""

    def set_edges(self, edges: Set[Edge]):
        self.edges = edges

    def add_edge(self, edge: Edge):
        self.edges.add(edge)

    def remove_edge(self, edge_name: str):
        if edge_name in self.edges:
            edge_for_removal = next(edge for edge in self.edges if edge.name == edge_name)
            for edge_new in self.edges:
                if edge_new.target == edge_for_removal.source:
                    edge_new.target = edge_for_removal.target
            self.edges.remove(edge_for_removal)

    def get_role_names(self):
        names = set()
        for edge in self.edges:
            names.add(edge.role)
        return names


def build_graph(transitions: List[Dict[str, Any]]) -> Graph:
    graph = Graph()
    for t in transitions:
        edge = Edge(t["label"]["logType"][0], t["source"], t["target"], t["label"]["role"])
        graph.add_edge(edge)
    return graph

def build_graph_internal(role_own_events_dict: Dict[str, List[EventData]]) -> Graph:
    graph = Graph()
    for role in role_own_events_dict:
        for event in role_own_events_dict[role]:
            edge = Edge(event.event_name, event.source, event.target, role)
            graph.add_edge(edge)
    return graph

# Build an index to quickly find edges from a given node
def build_index(graph: Graph):
    index = defaultdict(list)
    for edge in graph.edges:
        index[edge.source].append(edge)
    return index

def find_reachable_edges(graph: Graph, start: str) -> Set[Edge]:
    
    index = build_index(graph)
    
    visited_nodes = set()
    reachable_edges = set()
    
    # Use a list as a stack for DFS.
    stack: List[str] = [start]
    
    while stack:
        node = stack.pop()
        if node in visited_nodes:
            continue
        
        visited_nodes.add(node)
        
        for edge in index[node]:
            reachable_edges.add(edge)
            if edge.target not in visited_nodes:
                stack.append(edge.target)
    
    return reachable_edges

def generate_projection(graph: Graph, role: str) -> Graph:
    copyGraph = Graph()
    copyGraph.set_edges(copy.deepcopy(graph.edges))
    copyGraph.initial = graph.initial

    # First we find own events
    own_edges = set()
    own_edges_sources = set()
    for edge in graph.edges:
        if edge.role == role:
            own_edges.add(edge)
            own_edges_sources.add(edge.source)

    # Find those that come before
    preceding_edges = set()
    for edge in graph.edges:
        if edge.target in own_edges_sources:
            preceding_edges.add(edge)

    # Find those that are branching:
    all_sources = set()
    branching_sources = set()
    for edge in graph.edges:
        if edge.source in all_sources:
            branching_sources.add(edge.source)
        all_sources.add(edge.source)

    sources_to_branch_events = {}

    for edge in graph.edges:
        if edge.source in branching_sources:
            if edge.source not in list(sources_to_branch_events.keys()):
                sources_to_branch_events[edge.source] = [edge]
            else:
                sources_to_branch_events[edge.source].append(edge)

    # Paths from branching locations to all other
    branchLoc_to_events = {}
    for current_source in branching_sources:
        reachable = find_reachable_edges(graph, current_source)
        branchLoc_to_events[current_source] = reachable

    nesesary_branching_edges = set()

    for loc in branchLoc_to_events:
        if len(set.intersection(own_edges, branchLoc_to_events[loc])) > 0:
            nesesary_branching_edges.update(sources_to_branch_events[loc])


    project_edges = own_edges | preceding_edges | nesesary_branching_edges

    nesesary_branching_edges_names = set()
    for branch_event in nesesary_branching_edges:
        nesesary_branching_edges_names.add(branch_event.name)

    for edge in graph.edges:
        if edge not in project_edges:
            # We need to get the one from copyGraph as it might have changed the target
            copy_edge_for_removal = next(copy_edge for copy_edge in copyGraph.edges if edge.name == copy_edge)
            if copy_edge_for_removal.source == copyGraph.initial:
                copyGraph.initial = copy_edge_for_removal.target

            copyGraph.remove_edge(copy_edge_for_removal)
    
    return copyGraph

def create_JSONTransfer(graph: Graph, role: str) -> JSONTransfer:
    own_events = []
    other_events = []
    subscriptions = []

    for edge in graph.edges:
        if edge.role == role:
            own_events.append(EventData(event_name=edge.name, source=edge.source, target=edge.target))
        else:
            other_events.append(EventData(event_name=edge.name, source=edge.source, target=edge.target))
        subscriptions.append(edge.name)

    return JSONTransfer(
        name=role,
        initial=graph.initial,
        subscriptions=subscriptions,
        own_events=own_events,
        other_events=other_events
    )

def parse_protocol_JSON_file(json_file: str) -> tuple[JSONTransfer, List[JSONTransfer]]:
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    graph = build_graph(data["transitions"])
    graph.initial = data["initial"]

    jsonTransfers = []
    globalJsonTransfer = (create_JSONTransfer(graph,"GlobalProtocol"))

    for role in graph.get_role_names():
        newGraph = generate_projection(graph,role)
        jsonTransfers.append(create_JSONTransfer(newGraph,role))
        
    return globalJsonTransfer, jsonTransfers

def parse_protocol_seperatly(json_file: str) -> JSONTransfer: 
    with open(json_file, 'r') as f:
        data = json.load(f)

    graph = build_graph(data["transitions"])
    graph.initial = data["initial"]

    return create_JSONTransfer(graph,"GlobalProtocol")


def parse_projection_JSON_file(json_file: str) -> JSONTransfer:
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    initial_state = data['initial']
    subscriptions = data['subscriptions']
    
    own_event_names = []
    own_events = []
    other_events = []
    
    for transition in data['transitions']:
        source = transition.get('source')
        target = transition.get('target')
        label = transition.get('label', {})
        tag = label.get('tag')
        
        if tag == 'Execute':
            log_types = label.get('logType', [])
            for log_type in log_types:
                own_event_names.append(log_type)
        
        elif tag == 'Input':
            event_type = label.get('eventType')
            if any(event_type == event_name for event_name in own_event_names):  # Own event
                own_events.append(EventData(event_name=event_type, source=source, target=target))

            elif not any(event.event_name == event_type for event in own_events):
                other_events.append(EventData(event_name=event_type, source=source, target=target))
    
    return JSONTransfer(
        name=Path(json_file).stem,
        initial=initial_state,
        subscriptions=subscriptions,
        own_events=own_events,
        other_events=other_events
    )


def parse_time_JSON(json_file: str) -> TimeJSONTransfer:
    event_time_data = []
    log_time_data = []
    with open(json_file, 'r') as file:
        data = json.load(file)
        event_time_data = [
            EventTimeData(
                event_name=event_data["logType"],
                min_time=event_data.get("min_time"),
                max_time=event_data.get("max_time")
            )
            for event_data in data.get("events", [])
        ]
        log_time_data = [
            LogTimeData(
                role_name=event_data["role_name"],
                min_time=event_data.get("min_time"),
                max_time=event_data.get("max_time")
            )
            for event_data in data.get("logs", [])
        ]

    time_json_transfer = TimeJSONTransfer(log_time_data=log_time_data, event_time_data=event_time_data)
    return time_json_transfer
    