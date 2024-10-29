from Template import Template
from DataObjects.Declaration import Declaration
from DataObjects.Transition import Transition
from DataObjects.Location import Location
from DataObjects.JSONTransfer import JSONTransfer, EventData
from Utils import Utils
from typing import List

from graphviz import Digraph
import math

class Role(Template):

    # TODO: Make this used only if debugging of some sort is enabled
    def graphVizHelper(self, locations, transitions):
        graph = Digraph()


        for loc in locations:
            graph.node(str(loc.id), label=str(loc.id))
        
        for transition in transitions:
            graph.edge(str(transition.source.id), str(transition.target.id), label=str(transition.id))
        
        layout_info = graph.pipe(format='plain').decode('utf-8')

        for line in layout_info.splitlines():
            parts = line.split()
            if line.startswith('node'):
                node_id = parts[1]
                x, y = float(parts[2]), float(parts[3])
                current_l = next((loc for loc in locations if loc.id == int(node_id)), None)
                current_l.x = math.floor(x * 100)
                current_l.y = math.floor(y * 100)

            elif line.startswith('edge'):
                trans_id = parts[-5:-4][0]
                source_id = parts[1]
                target_id = parts[2]
                nail_coords = (math.floor(float(parts[4]) * 100 ), math.floor(float(parts[5]) * 100 ))
                current_t = next((tran for tran in transitions if tran.id == int(trans_id)), None)
                if (source_id != target_id):
                    current_t.nails = [nail_coords]

    def findLocation(self, name: str, locations: List[Location]):
        return next((loc for loc in locations if loc.name == name), None)


    def __init__(self, name: str, parameter: str, jsonTransfer: JSONTransfer):
        declaration = Declaration()

        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)
        all_events_set = {event.source for event in all_events} | {event.target for event in all_events}

        locations = []
        transitions = []
        for event in all_events_set:
            locations.append(Location(id = Utils.get_next_id(), name=event, x=0, y=0, urgent=True))


        linitial = self.findLocation(jsonTransfer.initial, locations)

        for event in all_events_set:
            levent= self.findLocation(event, locations)
            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=levent,
                target=linitial,
                synchronisation=f"{jsonTransfer.reset_channel_name}[id]?"))


        for event in all_events:
            lsource = self.findLocation(event.source, locations)
            ltarget = self.findLocation(event.target, locations)

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=lsource,
                target=ltarget,
                synchronisation=f"{jsonTransfer.advance_channel_names[event.event_name]}[id]?"))

            if event in jsonTransfer.own_events:
                if (event.source == linitial.name):
                    transitions.append(Transition(
                    id=Utils.get_next_id(),
                    source=lsource,
                    target=ltarget,
                    synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                    assignment=f"""setLogEntryForUpdate(
    {Utils.get_eventtype_UID(event.event_name)},id,
    -1,false)"""))
                else:
                    transitions.append(Transition(
                    id=Utils.get_next_id(),
                    source=lsource,
                    target=ltarget,
                    synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                    assignment=f"""setLogEntryForUpdate(
    {Utils.get_eventtype_UID(event.event_name)},id,
    -2,false)"""))

        self.graphVizHelper(locations, transitions)

        super().__init__(name, parameter, declaration, locations, linitial, transitions)
