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

    def find_shortes_path_to_exit(self, event: EventData) -> set[EventData]:
        visited = set()
        path_stack = []
        event_stack = []  # List of events in current path

        exit_paths = []

        def dfs(location: str, original_event: EventData):
            # We found end
            if self.outgoing[location] == []:
                #print(f"original event: {original_event}")
                #print(f"event_stack: {event_stack}")
                exit_path = []
                for i in range(len(event_stack) - 1, -1, -1):
                    event = event_stack[i]
                    #if event.source == original_event.source:
                    #    break
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
        
        dfs(event.target, event)

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


    def analyse_graph(self, initial_name: str) -> Dict[str, Union[Dict[EventData, Set[EventData]], Set[EventData]]]:
        loop_events = self.find_loops()
        branching_events = self.find_branching_events()

        preceding_events = {}
        for event in self.events:
            preceding = self.find_preceding_branch_events(event,branching_events)
            if preceding:  # Only include if there are preceding events
                preceding_events[event] = preceding

        for event in preceding_events:
            if event.source == initial_name and any(e not in loop_events for e in preceding_events[event]):
                preceding_events[event] = {}

        # If a loop start is not branching or all branches are loop start then we need to find exit route
        start_loop_events = []
        for start_loop in loop_events:
            start_loop_events.append(start_loop)

        exit_paths = {}
        
        current_shortest_path = None
        for start_loop in start_loop_events:
            if start_loop not in branching_events:
                current_shortest_path = self.find_shortes_path_to_exit(start_loop)
            else:
                current_branch_partion = []
                for branching_event in branching_events:
                    if branching_event.source == start_loop.source:
                        current_branch_partion.append(branching_event)

                all_looping = True
                for part_of_branch_partition in current_branch_partion:
                    if part_of_branch_partition not in start_loop_events:
                        all_looping = False
                        break
                
                if all_looping:
                    current_shortest_path = self.find_shortes_path_to_exit(start_loop)
            if current_shortest_path != None:
                exit_paths[start_loop] = current_shortest_path
        # return preceding_events
        return {
            'preceding_events': preceding_events,
            'branching_events': branching_events,
            'loop_events': loop_events,
            'exit_paths': exit_paths
        }