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


    def __init__(self, parameter: str, jsonTransfer: JSONTransfer, loop_bound: int, time_data_list: List[EventTimeData]):
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

                # If exit path then we need to add the guard
                exit_path_guard_addition = ""
                if jsonTransfer.exit_events != None and event in jsonTransfer.exit_events:
                    exit_path_guard_addition = f" || exitEventMap[{Utils.get_eventtype_UID(event.event_name)}]"

                exit_path_check_assigment_addition = ""
                if jsonTransfer.check_loop_exit_events != None and event in jsonTransfer.check_loop_exit_events.keys():
                    for inner_event in jsonTransfer.check_loop_exit_events[event]:
                        exit_path_check_assigment_addition += (f", updateExitPathGuards({Utils.get_eventtype_UID(inner_event.event_name)})")

                if(jsonTransfer.loop_events != [] and event.event_name in jsonTransfer.loop_events):
                        loop_counter_name = Utils.get_next_loopcount()
                        self.evetname_loopcounter[Utils.get_eventtype_UID(event.event_name)] = loop_counter_name

                        if (time_guard_addition != ""):
                            time_guard_addition += " && "

                        # Add disabeling part to invariant
                        if (lsource.invariant != None):
                            lsource.invariant += f" || {loop_counter_name}[id] == 1 || loopCountMap[{Utils.get_eventtype_UID(event.event_name)}] == {loop_bound}"
                        else:
                            lsource.invariant = f"{loop_counter_name}[id] == 1 || loopCountMap[{Utils.get_eventtype_UID(event.event_name)}] == {loop_bound}"

                        transitions.append(Transition(
                        id=Utils.get_next_id(),
                        source=lsource,
                        target=ltarget,
                        guard=time_guard_addition + f"{loop_counter_name}[id] < 1 && loopCountMap[{Utils.get_eventtype_UID(event.event_name)}] < {loop_bound}" + exit_path_guard_addition,
                        synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                        assignment=time_assignment_addition + f"""setLogEntryForUpdate(
        {Utils.get_eventtype_UID(event.event_name)},id,
        -2, false), {loop_counter_name}[id]++""" + exit_path_check_assigment_addition))
                        
                else:
                    if not (time_guard_addition != "" and exit_path_guard_addition != ""):
                         exit_path_guard_addition = exit_path_guard_addition[4:]

                    transitions.append(Transition(
                        id=Utils.get_next_id(),
                        source=lsource,
                        target=ltarget,
                        guard=time_guard_addition + exit_path_guard_addition,
                        synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                        assignment=time_assignment_addition + f"""setLogEntryForUpdate(
        {Utils.get_eventtype_UID(event.event_name)},id,
        -2, false)""" + exit_path_check_assigment_addition))

        self.graphViz_helper(locations, transitions)

        super().__init__(name, parameter, declaration, locations, linitial, transitions)
