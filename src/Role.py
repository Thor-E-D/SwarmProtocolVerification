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

    def get_evetname_loopcounter(self):
        return self.evetname_loopcounter

    # TODO: Make this used only if debugging of some sort is enabled
    def graphVizHelper(self, locations, transitions):
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

    def findLocation(self, name: str, locations: List[Location]):
        return next((loc for loc in locations if loc.name == name), None)


    def __init__(self, name: str, parameter: str, jsonTransfer: JSONTransfer, loop_bound: int):
        self.evetname_loopcounter = {}

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
                basedOnstr = "-2" if event.source == linitial.name else "-2"
                
                if(jsonTransfer.loop_events != [] and event.event_name in jsonTransfer.loop_events):
                        loop_counter_name = Utils.get_next_loopcount()
                        self.evetname_loopcounter[Utils.get_eventtype_UID(event.event_name)] = loop_counter_name

                        transitions.append(Transition(
                        id=Utils.get_next_id(),
                        source=lsource,
                        target=ltarget,
                        guard=f"{loop_counter_name} < {loop_bound}",
                        synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                        assignment=f"""setLogEntryForUpdate(
        {Utils.get_eventtype_UID(event.event_name)},id,
        {basedOnstr},false), {loop_counter_name}++"""))
                else:
                    transitions.append(Transition(
                        id=Utils.get_next_id(),
                        source=lsource,
                        target=ltarget,
                        synchronisation=f"{jsonTransfer.do_update_channel_name}[id]!",
                        assignment=f"""setLogEntryForUpdate(
        {Utils.get_eventtype_UID(event.event_name)},id,
        {basedOnstr},false)"""))

        self.graphVizHelper(locations, transitions)

        super().__init__(name, parameter, declaration, locations, linitial, transitions)
