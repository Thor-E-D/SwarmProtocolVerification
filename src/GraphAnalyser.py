"""\
Used to analyse swarms to find loops, branching events and
what each event should use for branch tracking

"""

from typing import List, Set, Dict, Union
from collections import defaultdict

from DataObjects.JSONTransfer import EventData


class GraphAnalyser:
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

    def find_branching_events(self) -> Set[EventData]:
        branching = set()
        for location in self.outgoing:
            if len(self.outgoing[location]) > 1:
                branching.update(self.outgoing[location])
        return branching

    def find_shortes_path_to_exit(self, event: EventData) -> set[EventData]:
        visited = set()
        path_stack = []
        event_stack = []

        exit_paths = []

        def dfs(location: str, original_event: EventData):
            # We found end
            if self.outgoing[location] == []:
                exit_path = []
                for i in range(len(event_stack) - 1, -1, -1):
                    event = event_stack[i]
                    exit_path.append(event)
                exit_paths.append(exit_path)
                return
            
            if location in path_stack:
                return

            path_stack.append(location)
            visited.add(location)

            for event in self.outgoing[location]:
                event_stack.append(event)
                dfs(event.target, original_event)
                event_stack.pop()

            path_stack.pop()

        dfs(event.source, event)

        if len(exit_paths) != 0:
            exit_paths.sort(key=len)
            return exit_paths[0]
        
        return None

    def find_tiedto(self, branching_events: list[EventData]):

        def find_tiedto_location(loc: str, current_tied_to_set: Set[EventData]):
            incoming_events = self.incoming[loc]
            for incoming_event in incoming_events:
                if incoming_event in branching_events:
                    current_tied_to_set.add(incoming_event)
                elif incoming_event.source != incoming_event.target:
                    find_tiedto_location(incoming_event.source, current_tied_to_set)

        resulting_tied_to_dict = {}
        for event in self.events:
            current_tied_to_set = set()
            find_tiedto_location(event.source, current_tied_to_set)
            resulting_tied_to_dict[event.event_name] = current_tied_to_set

        return resulting_tied_to_dict

    # Using dfs to find loops
    def find_loops(self) -> Set[EventData]:
        loop_starters = dict()
        visited = set()
        path_stack = []
        event_stack = []  # List of events in current path

        def dfs(location: str):
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
                dfs(event.target)
                event_stack.pop()

            path_stack.pop()

        # Start DFS from each unvisited location
        for location in self.locations:
            if location not in visited:
                dfs(location)

        return loop_starters

    def analyse_graph_loops_branches(self):
        loop_events = self.find_loops()
        branching_events = self.find_branching_events()

        return {
            'branching_events': branching_events,
            'loop_events': loop_events
        }


    def analyse_graph(self, initial_name: str) -> Dict[str, Union[Dict[EventData, Set[EventData]], Set[EventData]]]:
        branching_events = self.find_branching_events()
        # If a loop start is not branching or all branches are loop start then we need to find exit route
        exit_paths = set()
        
        current_shortest_path = None
        for event in self.events:
            current_shortest_path = self.find_shortes_path_to_exit(event)
            exit_paths.update(current_shortest_path)

        all_events = set(self.events)
        non_exit_paths = set.difference(all_events, exit_paths)

        return {
            'branching_events': branching_events,
            'non_exit_paths': non_exit_paths
        }