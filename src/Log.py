from Template import Template
from DataObjects.Declaration import Declaration
from DataObjects.Transition import Transition
from DataObjects.Location import Location
from DataObjects.JSONTransfer import JSONTransfer
from Utils import Utils
from Functions import generate_function_merge_propagation_log, generate_function_handle_log_entry
from typing import Dict

class Log(Template):
    def __init__(self, name: str, parameter: str, jsonTransfer: JSONTransfer, evetname_loopcounter: Dict[str,str]):
        declaration = Declaration()

        declaration.add_variable("logEntryType currentLog[logSize];")
        declaration.add_variable("int updatesSincePropagation = 0;")
        declaration.add_variable("bool newUpdates = false;")
        declaration.add_variable("int counter = 0;")

        declaration.add_variable(f"int log_id_start = {jsonTransfer.log_id_start};")

        declaration.add_variable("int emittedOrderCounts[logSize];")
        declaration.add_variable("int discardedEvents[logSize];")
        declaration.add_variable("int discardedDueToCompetionEvents[logSize];")
        declaration.add_variable("bool olderEntryIgnored = false;")
        declaration.add_variable("bool inCompetetion = false;")

        subscription_str = "int subscriptions[amountOfUniqueEvents] = {"
        subscription_counter = 0
        for subscription in jsonTransfer.subscriptions:
            subscription_counter += 1
            subscription_str += Utils.get_eventtype_UID(subscription) +", "

        subscription_str += "-1, " * (jsonTransfer.total_amount_of_events - subscription_counter)
        declaration.add_variable(subscription_str[:-2] + "};")

        # Get names of own events and names of other events for function
        own_event_names = []
        other_event_names = []

        for eventData in jsonTransfer.own_events:
            own_event_names.append(Utils.get_eventtype_UID(eventData.event_name))
        
        for eventData in jsonTransfer.other_events:
            other_event_names.append(Utils.get_eventtype_UID(eventData.event_name))

        # Adding function calls
        declaration.add_function_call(generate_function_handle_log_entry, own_event_names, other_event_names)
        declaration.add_function_call(generate_function_merge_propagation_log,evetname_loopcounter) 
        
        l1 = Location (id = Utils.get_next_id(), x=-204, y=-238, committed=True)
        l2 = Location (id = Utils.get_next_id(), x=-748, y=-136, committed=True)
        l3 = Location (id = Utils.get_next_id(), x=-204, y=-136)
        l4 = Location (id = Utils.get_next_id(), x=229, y=-127, committed=True)
        l5 = Location (id = Utils.get_next_id(), x=-612, y=34, committed=True)
        l6 = Location (id = Utils.get_next_id(), x=25, y=76, committed=True)
        l7 = Location (id = Utils.get_next_id(), x=-561, y=153, committed=True)

        locations = [l1, l2, l3, l4, l5, l6, l7]
        transitions = []

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l3,
            target=l1,
            guard="newUpdates",
            assignment="""currentLogToPropagate = (log_id_start + id + 1) % amountOfLogs,
updatesSincePropagation := 0,
newUpdates := false,
setPropagationLog(currentLog)""",
            nails = [(-136, -187)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l1,
            target=l3,
            synchronisation="propagate_log!",
            nails = [(-272, -195)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l3,
            target=l4,
            synchronisation=f"{jsonTransfer.do_update_channel_name}[id]?",
            assignment=f"""updateLog{jsonTransfer.name}(currentLog,emittedOrderCounts,log_id_start),
updatesSincePropagation++,
newUpdates := true""",
            nails = [(0, -51)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l4,
            target=l3,
            guard="!(updatesSincePropagation > maxUpdatesSincePropagation)"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l4,
            target=l6,
            guard="updatesSincePropagation > maxUpdatesSincePropagation",
            assignment="""currentLogToPropagate = (log_id_start + id + 1) % amountOfLogs,
updatesSincePropagation := 0,
newUpdates := false"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l6,
            target=l3,
            synchronisation="propagate_log!",
            assignment="setPropagationLog(currentLog)"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l3,
            target=l2,
            guard="currentLogToPropagate == log_id_start + id",
            synchronisation="propagate_log?",
            assignment="mergePropagationLog()"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l2,
            target=l5,
            synchronisation=f"{jsonTransfer.reset_channel_name}[id]!",
            assignment="""counter := 0,
setNextLogToPropagate()"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l5,
            target=l3,
            guard="currentLog[counter].orderCount == 0",
            synchronisation="propagate_log!"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l5,
            target=l7,
            guard="currentLog[counter].orderCount != 0"
        ))


        start_y = l7.y + 51
        start_x = l7.x - 85


        for subscription in jsonTransfer.subscriptions:
            nails = [(start_x + 68, start_y), (start_x, start_y)]
            start_y += 34
            start_x -= 34

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l7,
                target=l5,
                guard=f"currentLog[counter].eventID == {Utils.get_eventtype_UID(subscription)}",
                synchronisation=f"{jsonTransfer.advance_channel_names[subscription]}[id]!",
                assignment="counter++",
                nails=nails
            ))

        nails = [(start_x + 68, start_y), (start_x, start_y)]

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l7,
            target=l5,
            guard=f"!isInSubsciptions(subscriptions, currentLog[counter].eventID)",
            assignment="counter++",
            nails=nails
        ))
        
        # Initialize the superclass with the data
        super().__init__(name + "_log", parameter, declaration, locations, l3, transitions)
