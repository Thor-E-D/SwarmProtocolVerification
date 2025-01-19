"""\
Used to analyse swarms to find loops, branching events and
what each event should use for branch tracking

"""

from typing import List, Set, Dict, Union
from collections import defaultdict

from DataObjects.JSONTransfer import EventData


class GraphAnalyzer:
    def __init__(self, events: List[EventData]):
        self.events = events
        
        # Create adjacency lists for quick lookup
        self.outgoing = defaultdict(list)  # source -> [events]
        self.incoming = defaultdict(list)  # target -> [events]
        
        locations = []
        
        for event in events:
            self.outgoing[event.source].append(event)
            self.incoming[event.target].append(event)
            locations.append(event.source)
            locations.append(event.target)

        self.locations = sorted(set(locations))

    # For branch tracking    
    def find_preceding_branch_events(self, event: EventData,branching_events: Set[EventData]) -> Set[EventData]:
        incoming_to_source = self.incoming[event.source]
        for incoming in incoming_to_source:
            if incoming in branching_events:
                return({incoming})

        if incoming_to_source == []:
            return {event}

        res_list = set()
        for incoming in incoming_to_source:
            set_of_events = self.find_preceding_branch_events(incoming, branching_events)
            for part in set_of_events:
                res_list.add(part)
        return res_list

    # Using dfs to find loops
    def find_loops(self) -> Set[EventData]:
        loop_starters = dict()
        visited = set()
        path_stack = []
        event_stack = []  # List of events in current path

        def dfs(location: str, current_event: EventData = None):
            if location in path_stack:
                loop_events = set()

                for i in range(len(event_stack) - 1, -1, -1):
                    event = event_stack[i]
                    if event.source == location:
                        loop_starters[event] = loop_events
                        break
                    loop_events.add(event)
                return

            path_stack.append(location)
            visited.add(location)

            for event in self.outgoing[location]:
                event_stack.append(event)
                if event.target not in visited or event.target in path_stack:
                    dfs(event.target, event)
                event_stack.pop()

            path_stack.pop()

        # Start DFS from each unvisited location
        for location in self.locations:
            if location not in visited:
                dfs(location)

        return loop_starters

    def find_branching_events(self) -> Set[EventData]:
        branching = set()
        for location in self.outgoing:
            if len(self.outgoing[location]) > 1:
                branching.update(self.outgoing[location])
        return branching


def analyze_graph(eventData: List[EventData], initial_name: str) -> Dict[str, Union[Dict[EventData, Set[EventData]], Set[EventData]]]:
    analyzer = GraphAnalyzer(eventData)
    
    loop_events = analyzer.find_loops()
    branching_events = analyzer.find_branching_events()

    preceding_events = {}
    for event in eventData:
        preceding = analyzer.find_preceding_branch_events(event,branching_events)
        if preceding:  # Only include if there are preceding events
            preceding_events[event] = preceding

    for event in preceding_events:
        if event.source == initial_name and any(e not in loop_events for e in preceding_events[event]):
            preceding_events[event] = {}

    # return preceding_events
    return {
        'preceding_events': preceding_events,
        'branching_events': branching_events,
        'loop_events': loop_events
    }