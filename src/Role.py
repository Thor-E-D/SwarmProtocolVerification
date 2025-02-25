"""\
Creates and holds all information for a role.
Each role is reposible for emitting the events by directly communicating with its log

"""

from typing import List

import math

from graphviz import Digraph
from DataObjects.Declaration import Declaration
from DataObjects.Transition import Transition
from DataObjects.Location import Location, LocationType
from DataObjects.JSONTransfer import JSONTransfer, EventData
from DataObjects.TimeJSONTransfer import EventTimeData
from Template import Template
from Utils import Utils

class Role(Template):

    def get_evetname_loopcounter(self):
        return self.evetname_loopcounter

    # Using graphViz to space out locations and edges in UPPAAL to get somewhat more readable models
    # Only important when directly using the UPPAAL UI.
    def graphViz_helper(self, locations: List[Location], transitions: List[Transition]):
        graph = Digraph()


        for loc in locations:
            graph.node(str(loc.id), label=str(loc.id))
        
        for transition in transitions:
            if transition.source.id != transition.target.id:
                graph.node(str(transition.id), label=str(transition.id))
                graph.edge(str(transition.source.id), str(transition.id), label=str(transition.id) + "_to")
                graph.edge(str(transition.id), str(transition.target.id), label=str(transition.id) + "_from")
        
        layout_info = graph.pipe(format='plain').decode('utf-8')

        for line in layout_info.splitlines():
            parts = line.split()
            if line.startswith('node'):
                node_id = parts[1]
                x, y = float(parts[2]), float(parts[3])
                if any(location.id == int(node_id) for location in locations):
                    current_l = next((loc for loc in locations if loc.id == int(node_id)), None)
                    current_l.x = math.floor(x * 100)
                    current_l.y = math.floor(y * 100)
                else:
                    current_t = next((tran for tran in transitions if tran.id == int(node_id)), None)
                    current_t.nails = [(math.floor(float(x) * 100 ), math.floor(float(y) * 100 ))]

    def find_location(self, name: str, locations: List[Location]):
        return next((loc for loc in locations if loc.name == name), None)
    
    def find_outgoing_events_from_location(self, source: str, events: List[EventData]):
         return [event.event_name for event in events if event.source == source]


    def __init__(self, parameter: str, jsonTransfer: JSONTransfer, path_bound: int, time_data_list: List[EventTimeData]):
        name = jsonTransfer.name
        self.evetname_loopcounter = {}

        declaration = Declaration()

        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)
        all_location_names = {event.source for event in all_events} | {event.target for event in all_events}

        locations = []
        transitions = []

        for location_name in all_location_names:
            source_event_names = (self.find_outgoing_events_from_location(location_name, all_events))
            matching_time_events = [event_data for event_data in time_data_list if event_data in source_event_names and event_data.event_name in jsonTransfer.own_events]
            time_data_event = None

            if len(matching_time_events) > 0:
                time_data_event = max(
                    matching_time_events,
                    key=lambda event: (event.max_time is None, event.max_time)  # Sort None as highest
                )
            own_event_flag = any(source_event_name in jsonTransfer.own_events for source_event_name in source_event_names)    

            if not own_event_flag and time_data_event != None:
                 locations.append(Location(id = Utils.get_next_id(), name=location_name, x=0, y=0, locationType=LocationType.NEITHER))
            elif not own_event_flag and time_data_event == None:
                 locations.append(Location(id = Utils.get_next_id(), name=location_name, x=0, y=0, locationType=LocationType.NEITHER))
            elif time_data_event == None:
                locations.append(Location(id = Utils.get_next_id(), name=location_name, x=0, y=0, locationType=LocationType.URGENT))
            elif time_data_event.max_time == None:
                 locations.append(Location(id = Utils.get_next_id(), name=location_name, x=0, y=0, locationType=LocationType.NEITHER))
            else:
                locations.append(Location(id = Utils.get_next_id(), name=location_name, x=0, y=0, invariant=f"x <= {time_data_event.max_time}", locationType=LocationType.NEITHER))

        linitial = self.find_location(jsonTransfer.initial, locations)

        time_assignment_addition = ""
        if time_data_list != []:
                    declaration.add_variable("clock x;")
                    time_assignment_addition = "x := 0, "

        declaration.add_variable(f"const int id_start = {jsonTransfer.id_start};")

        # Find own branches to fix invariants
        branch_partitions = {}

        for event in all_events:
            lsource = self.find_location(event.source, locations)
            ltarget = self.find_location(event.target, locations)

            # Reset event for backtracking
            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=ltarget,
                target=lsource,
                assignment= Utils.remove_last_two_chars(time_assignment_addition),
                guard=f"currentEventResetID == {Utils.get_eventtype_UID(event.event_name)}",
                synchronisation=f"{jsonTransfer.backtrack_channel_name}[id]?"
                ))

            # Advance event this when we read this event in log
            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=lsource,
                target=ltarget,
                assignment= Utils.remove_last_two_chars(time_assignment_addition),
                synchronisation=f"{jsonTransfer.advance_channel_names[event.event_name]}[id]?"))
            
            if lsource not in list(branch_partitions.keys()):
                branch_partitions[lsource] = [event]
            else:
                branch_partitions[lsource].append(event)

            # If we emit the even we need to be able to do so with a transition
            if event in jsonTransfer.own_events:
                time_guard_addition = ""
                time_data_event = next((event_data for event_data in time_data_list if event_data == event.event_name), None)
                
                if time_data_event != None:
                    if time_data_event.min_time != None and time_data_event.max_time != None:
                        time_guard_addition = f"x >= {time_data_event.min_time} && x <= {time_data_event.max_time}"
                    elif time_data_event.min_time == None and time_data_event.max_time != None:
                        time_guard_addition = f"x <= {time_data_event.max_time}"
                    elif time_data_event.min_time != None and time_data_event.max_time == None:
                        time_guard_addition = f"x >= {time_data_event.min_time}"
                elif lsource.locationType == LocationType.NEITHER:
                     time_guard_addition = f"x == 0" # Happens only when other branch is timed but this event isn't so we enforce instant emission or none at all.

                exit_path_guard_addition = ""
                exit_path_assignment_addition = ""

                if (event in jsonTransfer.non_exit_events and path_bound > -1):
                    exit_path_guard_addition = f"nonExitCounterMap[id + id_start][{Utils.get_eventtype_UID(event.event_name)}] < {path_bound}"
                    exit_path_assignment_addition = f", nonExitCounterMap[id + id_start][{Utils.get_eventtype_UID(event.event_name)}]++"
                
                if (time_guard_addition != "" and exit_path_guard_addition != ""):
                    time_guard_addition += " && "

                transitions.append(Transition(
                        id=Utils.get_next_id(),
                        source=lsource,
                        target=ltarget,
                        guard=time_guard_addition + exit_path_guard_addition,
                        synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                        assignment=time_assignment_addition + f"""setLogEntryForUpdate(
        {Utils.get_eventtype_UID(event.event_name)},id,
        -2, false)""" + exit_path_assignment_addition))
                    
        # We need to figure out if there are multiple branching events that this roles emits from the same location
        # if there is we need to set the invariant accordingly.
        if (path_bound > -1):
            own_event_names = []
            for own_event in jsonTransfer.own_events:
                own_event_names.append(own_event.event_name)

            event_names_exit = {event.event_name for event in jsonTransfer.non_exit_events}
            for branch_location in branch_partitions:
                if len(branch_partitions[branch_location]) > 1:
                    invariant_result = ""
                    exit_path_event = None
                    for branch_event in branch_partitions[branch_location]:
                        if branch_event.event_name not in event_names_exit:
                            exit_path_event = branch_event

                    source_event_names = (self.find_outgoing_events_from_location(branch_location.name, branch_partitions[branch_location]))
                    matching_time_events = [event_data for event_data in time_data_list if event_data in source_event_names and event_data.event_name in jsonTransfer.own_events]

                    sorted_time = sorted(matching_time_events, key=lambda event: (event.max_time is None, event.max_time), reverse=True)
                    exit_path_time_data_event = next((event_data for event_data in time_data_list if event_data == exit_path_event.event_name), None)
                    parenthesis_counter = 0
                    not_all_own = len(sorted_time) != len(branch_partitions[branch_location])
                    own_and_branching = []

                    if sorted_time != []:
                        if sorted_time[0].event_name != exit_path_event.event_name:
                            for time_data_branch in sorted_time:
                                own_and_branching.append(time_data_branch.event_name)
                                if time_data_branch.event_name != exit_path_event.event_name:
                                    if time_data_branch.max_time != None:
                                        invariant_result += f"x <= {time_data_branch.max_time} && ( nonExitCounterMap[id + id_start][{Utils.get_eventtype_UID(time_data_branch.event_name)}] < {path_bound} || ( "
                                        parenthesis_counter += 2
                                    else:
                                        invariant_result += f"( nonExitCounterMap[id + id_start][{Utils.get_eventtype_UID(time_data_branch.event_name)}] < {path_bound} || ( "
                                        parenthesis_counter += 2
                                else:
                                    if exit_path_time_data_event.max_time != None:
                                        invariant_result += f"x <= {exit_path_time_data_event.max_time}" + (")" * parenthesis_counter)
                                    else:
                                        invariant_result = ""
                                    break

                        if not not_all_own or exit_path_event.event_name in own_event_names:
                            if sorted_time[0].event_name == exit_path_event.event_name and exit_path_time_data_event.max_time != None:
                                invariant_result = f"x <= {exit_path_time_data_event.max_time}" 

                        else:
                            final_invariant = " || "
                            for own_branch_event_name in own_and_branching:
                                final_invariant += f"nonExitCounterMap[id + id_start][{Utils.get_eventtype_UID(own_branch_event_name)}] == "
                            
                            final_invariant += f"{path_bound}"

                            invariant_result = invariant_result[:-5] + (")" * (parenthesis_counter-1)) + final_invariant

                        branch_location.invariant = invariant_result

        self.graphViz_helper(locations, transitions)

        super().__init__(name, parameter, declaration, locations, linitial, transitions)
