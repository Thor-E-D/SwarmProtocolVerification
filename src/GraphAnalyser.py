from typing import List, Set, Dict
from dataclasses import dataclass
from collections import defaultdict

from DataObjects.JSONTransfer import EventData


class GraphAnalyzer:
    def __init__(self, events: List[EventData]):
        self.events = events
        
        # Create adjacency lists for quick lookup
        self.outgoing = defaultdict(list)  # source -> [events]
        self.incoming = defaultdict(list)  # target -> [events]
        
        # Get all unique locations (states)
        locations = []
        
        for event in events:
            self.outgoing[event.source].append(event)
            self.incoming[event.target].append(event)
            locations.append(event.source)
            locations.append(event.target)

        self.locations = sorted(set(locations))

    
    def find_immediate_preceding_events(self, event: EventData,branching_events: Set[EventData] , joining_events: Set[EventData]) -> Set[EventData]:
        incoming_to_source = self.incoming[event.source]
        for incoming in incoming_to_source:
            if incoming in joining_events:
                return {e for e in joining_events if e.target == event.target}
            if incoming in branching_events:
                return(incoming)

        if incoming_to_source == []:
            return event
            
        return self.find_immediate_preceding_events(incoming_to_source[0], branching_events, joining_events)

    def find_loops(self) -> Set[EventData]:
        """Find events that start loops using DFS."""
        loop_starters = set()
        visited = set()
        path_stack = []
        event_stack = []  # List of events in current path

        def dfs(location: str, current_event: EventData = None):
            if location in path_stack:
                # We found a loop! Find the event that first leads to a location in our current path
                target_index = path_stack.index(location)  # Where the loop ends
                
                #print(event_stack)
                #print(location)

                # Look through events in our path to find the first one that creates the loop
                for i in range(len(event_stack) - 1, -1, -1):  # Go backwards through events
                    event = event_stack[i]
                    # Go backwards through events untill we find the one which started this loop so source == target
                    if event.source == location:
                        loop_starters.add(event)
                        break
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
        """Find events where a location has multiple outgoing paths."""
        branching = set()
        for location in self.outgoing:
            if len(self.outgoing[location]) > 1:
                branching.update(self.outgoing[location])
        return branching

    def find_joining_events(self) -> Set[EventData]:
        """Find events where multiple paths lead to the same location."""
        joining = set()
        for location in self.incoming:
            if len(self.incoming[location]) > 1:
                joining.update(self.incoming[location])
        return joining


def analyze_graph(eventData: List[EventData], initial_name: str):

    """Analyze a graph and return all special transitions."""
    analyzer = GraphAnalyzer(eventData)
    
    loop_events = analyzer.find_loops()
    branching_events = analyzer.find_branching_events()
    joining_events = analyzer.find_joining_events()

    preceding_events = {}
    for event in eventData:
        preceding = analyzer.find_immediate_preceding_events(event,branching_events,joining_events)
        if preceding:  # Only include if there are preceding events
            preceding_events[event] = [preceding]

    for event in preceding_events:
        if event.source == initial_name and any(e not in loop_events for e in preceding_events[event]):
            preceding_events[event] = {}

    #return preceding_events
    return {
        'preceding_events': preceding_events,
        'branching_events': branching_events,
        'loop_events': loop_events
    }