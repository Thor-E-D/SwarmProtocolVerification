"""\
Creates and holds all information for a log.
Log is constructed differently depeding on given settings,
such as if time is included and what kind of delay in propagation is used.

"""

from typing import Dict

from DataObjects.Declaration import Declaration
from DataObjects.Transition import Transition
from DataObjects.Location import Location, LocationType
from DataObjects.JSONTransfer import JSONTransfer
from DataObjects.TimeJSONTransfer import LogTimeData
from DataObjects.ModelSettings import DelayType
from Template import Template
from Utils import Utils
from Functions import generate_function_merge_propagation_log, generate_function_handle_log_entry

class Log(Template):
    def __init__(self, parameter: str, jsonTransfer: JSONTransfer, evetname_loopcounter: Dict[str,str], log_size: int, log_delay_type: DelayType, log_time_data: LogTimeData = None):
        
        # We set a flag if our delay is nothing
        delay_nothing = (log_delay_type == DelayType.NOTHING)
        
        name = jsonTransfer.name
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
        declaration.add_variable("bool backTracking = false;")
        declaration.add_variable("bool didLogChange = false;")
        declaration.add_variable("int currentSizeOfLog = 0;")

        empty_array_str = ""
        for _ in range (0,log_size):
            empty_array_str += "-1, "

        declaration.add_variable(f"int discardedEventIDs[logSize] = {{ {empty_array_str[0:-2]} }};")
        declaration.add_variable("int resetCount = 0;")
        declaration.add_variable("int eventsToRead = 0;")

        subscription_str = "int subscriptions[amountOfUniqueEvents] = {"
        subscription_counter = 0
        for subscription in jsonTransfer.subscriptions:
            subscription_counter += 1
            subscription_str += Utils.get_eventtype_UID(subscription) +", "

        subscription_str += "-1, " * (jsonTransfer.total_amount_of_events - subscription_counter)
        declaration.add_variable(subscription_str[:-2] + "};")

        # Flow list and pointer
        declaration.add_variable(f"int initialLocation = {jsonTransfer.initial_pointer};")
        declaration.add_variable(f"int currentLocation = {jsonTransfer.initial_pointer};")
        declaration.add_variable(f"const int eventLocationMap[amountOfUniqueEvents][2] = {Utils.python_list_to_uppaal_list(jsonTransfer.flow_list)};")

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
        
        l1 = Location (id = Utils.get_next_id(), x=-204, y=-298, name="l_prop1", locationType = LocationType.COMMITTED)
        l2 = Location (id = Utils.get_next_id(), x=-748, y=-136, locationType = LocationType.COMMITTED)
        l3 = Location (id = Utils.get_next_id(), x=-204, y=-136)
        l4 = Location (id = Utils.get_next_id(), x=229, y=-127, locationType = LocationType.COMMITTED)
        l5 = Location (id = Utils.get_next_id(), x=-612, y=34, locationType = LocationType.COMMITTED)
        if (not delay_nothing):
            l6 = Location (id = Utils.get_next_id(), x=25, y=76, name="l_prop2", locationType = LocationType.COMMITTED)
        l7 = Location (id = Utils.get_next_id(), x=-561, y=153, locationType = LocationType.COMMITTED)
        l8 = Location (id = Utils.get_next_id(), x=-977, y=34, locationType = LocationType.COMMITTED)
        l9 = Location (id = Utils.get_next_id(), x=-1079, y=136, locationType = LocationType.COMMITTED)

        locations = []
        if (delay_nothing):
            locations = [l1, l2, l3, l4, l5, l7, l8, l9]
        else:
            locations = [l1, l2, l3, l4, l5, l6, l7, l8, l9]

        transitions = []

        intitial_location = l3
        waiting_location = l3

        assigmentAddition = ""
        guard_addition = ""
        guard_extension_addition = ""

        if log_time_data != None:
            declaration.add_variable("clock x;")

            assigmentAddition = "x := 0, "
            guard_extension_addition = "&& updatesSincePropagation != 1"

            intitial_location = Location (id = Utils.get_next_id(), x=-204, y=-186, locationType = LocationType.COMMITTED)
            waiting_location = Location (id = Utils.get_next_id(), x=-204, y=-246, locationType = LocationType.NEITHER)
            locations.append(intitial_location)
            locations.append(waiting_location)

            if log_time_data.max_time != None:
                waiting_location.invariant = f"x <= {log_time_data.max_time}"

            if log_time_data.min_time != None:
                guard_addition = f"x >= {log_time_data.min_time} &&"

            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=intitial_location,
            target=l3,
            guard="!newUpdates"
            ))

            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=intitial_location,
            target=waiting_location,
            guard="newUpdates"
            ))
            
            if (delay_nothing):
                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l4,
                target=intitial_location,
                guard=f"updatesSincePropagation == 1", # We know it is the first since propagation and need to reset the clock.
                assignment=Utils.remove_last_two_chars(assigmentAddition),
                ))

                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l4,
                target=intitial_location,
                guard=f"updatesSincePropagation != 1",
                nails = [(0, 20)]
                ))
            else:
                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l4,
                target=intitial_location,
                guard=f"!(updatesSincePropagation > maxUpdatesSincePropagation_{jsonTransfer.name}) && updatesSincePropagation == 1",
                assignment=Utils.remove_last_two_chars(assigmentAddition),
                nails = [(0, 20)]
                ))

            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=waiting_location,
            target=l2,
            guard="currentLogToPropagate == log_id_start + id",
            synchronisation="propagate_log?",
            assignment="mergePropagationLog()"
            ))

            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=waiting_location,
            target=l4,
            synchronisation=f"{jsonTransfer.do_update_channel_name}[id]?",
            assignment=f"""updateLog{jsonTransfer.name}(currentLog,emittedOrderCounts,log_id_start),
                    updatesSincePropagation++,
                    newUpdates := true,
                    currentSizeOfLog++""",
            nails = [(0, -61)]
            ))


        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=waiting_location,
            target=l1,
            guard=guard_addition + "newUpdates",
            assignment=assigmentAddition + """currentLogToPropagate = (log_id_start + id + 1) % amountOfLogs,
updatesSincePropagation := 0,
newUpdates := false,
setPropagationLog(currentLog)""",
            nails = [(-76, -221), (-76,-263)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l2,
            target=l8,
            guard="didLogChange && resetCount != 0",
            assignment="""counter := currentSizeOfLog - eventsToRead,
setNextLogToPropagate(),
backTracking := true"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l8,
            target=l9,
            guard="resetCount != 0",
            assignment="""currentEventResetID = discardedEventIDs[resetCount - 1]""",
            nails = [(-1079, 34)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l9,
            target=l8,
            assignment="""discardedEventIDs[resetCount - 1] = -1,
resetCount--""",
            synchronisation=f"{jsonTransfer.reset_channel_name}[id]!",
            nails = [(-978, 136)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l9,
            target=l8,
            guard="!isInSubsciptions(subscriptions, currentEventResetID)",
            assignment="""discardedEventIDs[resetCount - 1] = -1,
resetCount--""",
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l8,
            target=l5,
            guard="resetCount == 0"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l1,
            target=l3,
            synchronisation="propagate_log!",
            nails = [(-347, -255)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l3,
            target=l4,
            synchronisation=f"{jsonTransfer.do_update_channel_name}[id]?",
            assignment=f"""updateLog{jsonTransfer.name}(currentLog,emittedOrderCounts,log_id_start),
updatesSincePropagation++,
newUpdates := true,
currentSizeOfLog++""",
            nails = [(0, -51)]
        ))

        if (not delay_nothing):
            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l4,
                target=intitial_location,
                guard=f"!(updatesSincePropagation > maxUpdatesSincePropagation_{jsonTransfer.name})" + guard_extension_addition
            ))

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l4,
                target=l6,
                guard=f"updatesSincePropagation > maxUpdatesSincePropagation_{jsonTransfer.name}",
                assignment="""currentLogToPropagate = (log_id_start + id + 1) % amountOfLogs,
    updatesSincePropagation := 0,
    newUpdates := false"""
            ))

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l6,
                target=intitial_location,
                synchronisation="propagate_log!",
                assignment=assigmentAddition + "setPropagationLog(currentLog)"
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
            assignment="""counter := currentSizeOfLog - eventsToRead,
setNextLogToPropagate()""",
            guard="!didLogChange || resetCount == 0"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l5,
            target=intitial_location,
            guard="currentLog[counter].orderCount == 0",
            synchronisation="propagate_log!",
            assignment="""didLogChange := false,
backTracking := false,
eventsToRead := 0"""
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
        
        super().__init__(name + "_log", parameter, declaration, locations, l3, transitions)
