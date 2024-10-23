from Template import Template
from DataObjects.Declaration import Declaration
from DataObjects.Transition import Transition
from DataObjects.Location import Location
from DataObjects.JSONTransfer import JSONTransfer, EventData
from Utils import Utils

class Role(Template):
    def __init__(self, name: str, parameter: str, jsonTransfer: JSONTransfer):
        declaration = Declaration()

        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)
        all_events_set = {event.source for event in all_events} | {event.target for event in all_events}

        locations = []
        transitions = []
        current_x = 0
        current_y = 0
        for event in all_events_set:
            locations.append(Location(id = Utils.get_next_id(), name=event, x=current_x, y=current_y, urgent=True))
            current_x += 40
            current_y += 40



        linitial = next((loc for loc in locations if loc.name == jsonTransfer.initial), None)

        for event in all_events_set:
            levent= next((loc for loc in locations if loc.name == event), None)
            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=levent,
                target=linitial,
                synchronisation=f"{jsonTransfer.reset_channel_name}[id]?"))


        for event in jsonTransfer.own_events:
            lsource = next((loc for loc in locations if loc.name == event.source), None)
            ltarget = next((loc for loc in locations if loc.name == event.target), None)

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=lsource,
                target=ltarget,
                synchronisation=f"{jsonTransfer.advance_channel_names[event.event_name]}[id]?"))

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


        for event in jsonTransfer.other_events:
            lsource = next((loc for loc in locations if loc.name == event.source), None)
            ltarget = next((loc for loc in locations if loc.name == event.target), None)

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=lsource,
                target=ltarget,
                synchronisation=f"{jsonTransfer.advance_channel_names[event.event_name]}[id]?"))       

        super().__init__(name, parameter, declaration, locations, linitial, transitions)
