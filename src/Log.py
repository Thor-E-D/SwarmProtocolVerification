"""\
Creates and holds all information for a log.
Log is constructed differently depeding on given settings,
such as if time is included and what kind of delay in propagation is used.

In the same fashion as a prototype design pattern, a base is first created and
then changed later according to settings.
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
    def __init__(self, parameter: str, json_transfer: JSONTransfer, log_size: int, log_delay_type: DelayType, using_global_event_bound: bool, eventnames_dict: Dict[str,str], log_time_data: LogTimeData = None):
        
        no_delay_flag = False

        if (log_delay_type == DelayType.NOTHING):
            log_delay_type = DelayType.EVENTS_SELF_EMITTED
            no_delay_flag = True
        
        name = json_transfer.name
        declaration = Declaration()

        declaration.add_variable("logEntryType currentLog[logSize];")
        declaration.add_variable("int updatesSincePropagation = 0;")
        declaration.add_variable("bool newUpdates = false;")
        declaration.add_variable("int counter = 0;")

        declaration.add_variable(f"int id_start = {json_transfer.id_start};")

        declaration.add_variable("int emittedOrderCounts[logSize];")
        declaration.add_variable("int discardedEvents[logSize];")
        declaration.add_variable("int discardedDueToCompetionEvents[logSize];")
        declaration.add_variable("bool olderEntryIgnored = false;")
        declaration.add_variable("bool inCompetetion = false;")
        declaration.add_variable("bool backTracking = false;")
        declaration.add_variable("bool didLogChange = false;")
        declaration.add_variable("int currentSizeOfLog = 0;")
        declaration.add_variable("int unSubCount[logSize];") #For query use only

        empty_array_str = ""
        for _ in range (0,log_size):
            empty_array_str += "-1, "

        declaration.add_variable(f"int discardedEventIDs[logSize] = {{ {empty_array_str[0:-2]} }};")
        declaration.add_variable("int resetCount = 0;")
        declaration.add_variable("int eventsToRead = 0;")


        subscription_str = "const bool subscriptions[amountOfUniqueEvents] = {"
        for event_key in eventnames_dict:
            subscription_str += f"{event_key in json_transfer.subscriptions}, ".lower()

        declaration.add_variable(subscription_str[:-2] + "};")

        # Flow list and pointer
        declaration.add_variable(f"int initialLocation = {json_transfer.initial_pointer};")
        declaration.add_variable(f"int currentLocation = {json_transfer.initial_pointer};")
        declaration.add_variable(f"const int eventLocationMap[amountOfUniqueEvents][2] = {Utils.python_list_to_uppaal_list(json_transfer.flow_list)};")

        # Get names of own events and names of other events for function
        own_event_names = []
        other_event_names = []

        UID_subscriptions = list(map(Utils.get_eventtype_UID, json_transfer.subscriptions))

        for eventData in json_transfer.own_events:
            own_event_names.append(Utils.get_eventtype_UID(eventData.event_name))
        
        for eventData in json_transfer.other_events:
            other_event_names.append(Utils.get_eventtype_UID(eventData.event_name))

        # Adding function calls
        declaration.add_function_call(generate_function_handle_log_entry, UID_subscriptions)
        declaration.add_function_call(generate_function_merge_propagation_log) 
        
        l_prop1 = Location (id = Utils.get_next_id(), x=-204, y=-298, name="l_prop1", locationType = LocationType.COMMITTED)
        l_merge_log = Location (id = Utils.get_next_id(), x=-748, y=-136, name="merge_log", locationType = LocationType.COMMITTED)
        l_initial = Location (id = Utils.get_next_id(), x=-204, y=-136, name="initial")
        l_accepting_emitted_1 = Location (id = Utils.get_next_id(), x=8, y=-76, name="accepting_emitted_1", locationType = LocationType.COMMITTED)
        l_accepting_emitted_2 = Location (id = Utils.get_next_id(), x=238, y=-136, name="accepting_emitted_2", locationType = LocationType.COMMITTED)
        l_updating_role_1 = Location (id = Utils.get_next_id(), x=-612, y=34, name="updating_role_1", locationType = LocationType.COMMITTED)
        l_prop2 = Location (id = Utils.get_next_id(), x=238, y=68, name="l_prop2", locationType = LocationType.COMMITTED)
        l_updating_role_2 = Location (id = Utils.get_next_id(), x=-561, y=153, name="updating_role_2", locationType = LocationType.COMMITTED)
        l_backtracking_1 = Location (id = Utils.get_next_id(), x=-977, y=34, name="backtracking_1", locationType = LocationType.COMMITTED)
        l_backtracking_2 = Location (id = Utils.get_next_id(), x=-1079, y=136, name="backtracking_2", locationType = LocationType.COMMITTED)
        l_overflow = Location (id = Utils.get_next_id(), x=-204, y=214, name="overflow", locationType = LocationType.COMMITTED)

        locations = [l_prop1, l_merge_log, l_initial, l_accepting_emitted_1, l_accepting_emitted_2 ,l_updating_role_1, l_prop2, l_updating_role_2, l_backtracking_1, l_backtracking_2, l_overflow]
        transitions = []

        # Normal model based on untimed and using DELAY.EVENT_SELF_EMITTED
        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_initial,
            target=l_prop1,
            guard="newUpdates",
            assignment="""currentLogToPropagate = (id_start + id + 1) % amountOfLogs,
updatesSincePropagation := 0,
newUpdates := false,
setPropagationLog(currentLog)""",
            nails = [(-76, -221), (-76,-263)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_merge_log,
            target=l_backtracking_1,
            guard="didLogChange && resetCount != 0",
            assignment="""counter := currentSizeOfLog - eventsToRead,
setNextLogToPropagate(),
backTracking := true"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_backtracking_1,
            target=l_backtracking_2,
            guard="resetCount != 0",
            assignment="""currentEventResetID = discardedEventIDs[resetCount - 1]""",
            nails = [(-1079, 34)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_backtracking_2,
            target=l_backtracking_1,
            assignment="""discardedEventIDs[resetCount - 1] = -1,
resetCount--""",
            synchronisation=f"{json_transfer.backtrack_channel_name}[id]!",
            nails = [(-978, 136)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_backtracking_1,
            target=l_updating_role_1,
            guard="resetCount == 0"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_prop1,
            target=l_initial,
            synchronisation="propagate_log!",
            nails = [(-347, -255)]
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_initial,
            target=l_accepting_emitted_1,
            synchronisation=f"{json_transfer.do_update_channel_name}[id]?",
            assignment=f"""updateLogEntry(currentLog,emittedOrderCounts,id_start),
updatesSincePropagation++,
newUpdates := true,
currentSizeOfLog++"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_accepting_emitted_1,
            target=l_accepting_emitted_2,
            guard="globalLogIndex != logSize"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_accepting_emitted_2,
            target=l_initial,
            guard=f"!(updatesSincePropagation > maxUpdatesSincePropagation_{json_transfer.name})"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_accepting_emitted_2,
            target=l_prop2,
            guard=f"updatesSincePropagation > maxUpdatesSincePropagation_{json_transfer.name}",
            assignment="""currentLogToPropagate = (id_start + id + 1) % amountOfLogs,
updatesSincePropagation := 0,
newUpdates := false"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_prop2,
            target=l_initial,
            synchronisation="propagate_log!",
            assignment="setPropagationLog(currentLog)"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_initial,
            target=l_merge_log,
            guard="currentLogToPropagate == id_start + id",
            synchronisation="propagate_log?",
            assignment="mergePropagationLog()"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_merge_log,
            target=l_updating_role_1,
            assignment="""counter := currentSizeOfLog - eventsToRead,
setNextLogToPropagate()""",
            guard="!didLogChange || resetCount == 0"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_updating_role_1,
            target=l_initial,
            guard="currentLog[counter].orderCount == 0",
            synchronisation="propagate_log!",
            assignment="""didLogChange := false,
backTracking := false,
eventsToRead := 0"""
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_updating_role_1,
            target=l_updating_role_2,
            guard="currentLog[counter].orderCount != 0"
        ))


        start_y = l_updating_role_2.y + 51
        start_x = l_updating_role_2.x - 85


        for subscription in json_transfer.subscriptions:
            nails = [(start_x + 68, start_y), (start_x, start_y)]
            start_y += 34
            start_x -= 34

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_updating_role_2,
                target=l_updating_role_1,
                guard=f"currentLog[counter].eventID == {Utils.get_eventtype_UID(subscription)}",
                synchronisation=f"{json_transfer.advance_channel_names[subscription]}[id]!",
                assignment="counter++",
                nails=nails
            ))

        nails = [(start_x + 68, start_y), (start_x, start_y)]

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_accepting_emitted_1,
            target=l_overflow,
            guard="globalLogIndex == logSize",
            synchronisation="chan_overflow!"
        ))

        transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_initial,
            target=l_overflow,
            synchronisation="chan_overflow?"
        ))

        # Altering the based model based on time
        if log_time_data != None:
            declaration.add_variable("clock x;")

            assigmentAddition = "x := 0, "
            guard_extension_addition = "&& updatesSincePropagation != 1"

            if log_time_data.max_time != None:
                l_initial.invariant = f"x <= {log_time_data.max_time} || !newUpdates"

            if log_time_data.min_time != None:
                guard_addition = f"x >= {log_time_data.min_time} &&"

            current_transition = self.find_transition(transitions, l_source=l_initial, l_target=l_prop1)
            current_transition.assignment = assigmentAddition + current_transition.assignment
            current_transition.guard = guard_addition + current_transition.guard
                
            current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_initial)
            current_transition.guard = current_transition.guard + guard_extension_addition

            current_transition = self.find_transition(transitions, l_source=l_prop2, l_target=l_initial)
            current_transition.assignment = assigmentAddition + current_transition.assignment
            

            transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_accepting_emitted_2,
                target=l_initial,
                guard=f"!(updatesSincePropagation > maxUpdatesSincePropagation_{json_transfer.name}) && updatesSincePropagation == 1",
                assignment=Utils.remove_last_two_chars(assigmentAddition),
                nails = [(0, 20)]
                ))
            
            # If timed and no delay we have to remove the instant propagation part
            if no_delay_flag:
                current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_prop2)
                transitions.remove(current_transition)
                current_transition = self.find_transition(transitions, l_source=l_prop2, l_target=l_initial)
                transitions.remove(current_transition)
                locations.remove(l_prop2)

                # We have to change some guards.
                current_transitions = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_initial)
                for transition in current_transitions:
                    split_guard = transition.guard.split("&&")
                    transition.guard = split_guard[1]

        # Altering the base model if nessesary finding transitions and changing them as required.
        if using_global_event_bound:
            # Adding nessesary locations
            l_forced_prop_1 = Location (id = Utils.get_next_id(), x=17, y=178, name="forced_prop_1", locationType = LocationType.COMMITTED)
            l_forced_prop_2 = Location (id = Utils.get_next_id(), x=-204, y=68, name="forced_prop_2", locationType = LocationType.COMMITTED)
            locations.append(l_forced_prop_1)
            locations.append(l_forced_prop_2)

            # Changing transitions based on their names
            current_transition = self.find_transition(transitions, l_source=l_prop2, l_target=l_initial)
            current_transition.target = l_forced_prop_1

            current_transition = self.find_transition(transitions, l_source=l_updating_role_1, l_target=l_initial)
            current_transition.guard += " && !anyForcedToPropagate"
            current_transition.nail = (-306, 34)

            current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_initial)
            if log_time_data == None:
                current_transition.synchronisation = "force_propagate!"
            else:
                # Have to find difference in assigment
                for trans in current_transition:
                    if trans.assignment == None:
                        trans.synchronisation = "force_propagate!"
                    else:
                        trans.target = l_forced_prop_2


            # Allowing forced propagation to attempt to propagate once more
            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_updating_role_1,
            target=l_initial,
            guard="""currentLog[counter].orderCount == 0 &&
                anyForcedToPropagate &&
                currentLogToPropagate == id_start + id && 
                !forcedToPropagate[id + id_start]""",
            synchronisation="attempt_propagation!",
            assignment="""didLogChange := false,
                backTracking := false,
                eventsToRead := 0""",
            nails=[(-340,170), (-238, 170), (-238, -68)]
            ))

            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_updating_role_1,
            target=l_initial,
            guard="""currentLog[counter].orderCount == 0 &&
                anyForcedToPropagate &&
                currentLogToPropagate != id_start + id""",
            synchronisation="propagate_log!",
            assignment="""didLogChange := false,
                backTracking := false,
                eventsToRead := 0""",
            nails=[(-612,-102), (-272, -102)]
            ))

            # Adding transitions for propagating before force propagating
            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_forced_prop_1,
            target=l_forced_prop_2,
            guard="""(currentLogToPropagate + 1) % amountOfLogs == id_start + id
                && amountOfPropagation == 0""",
            synchronisation="propagate_log?"
            ))

            transitions.append(Transition(
            id=Utils.get_next_id(),
            source=l_forced_prop_2,
            target=l_initial,
            synchronisation="force_propagate!"
            ))


            if log_delay_type == DelayType.EVENTS_EMITTED:
                l_forced_prop_3 = Location (id = Utils.get_next_id(), x=297, y=-289, name="forced_prop_3", locationType = LocationType.COMMITTED)
                locations.append(l_forced_prop_3)

                current_transition = self.find_transition(transitions, l_source=l_initial, l_target=l_accepting_emitted_1)
                current_transition.assignment=f"updateLogEntry(currentLog,emittedOrderCounts,id_start),currentSizeOfLog++"

                current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_1, l_target=l_accepting_emitted_2)
                current_transition.guard = current_transition.guard +  "&& newUpdates"

                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_accepting_emitted_1,
                target=l_accepting_emitted_2,
                guard="globalLogIndex != logSize && !newUpdates",
                assignment="""updatesSincePropagation := globalLogIndex,
                    newUpdates := true""",
                nails=[(8, 34), (170, -34)]
                ))

                time_guard_addition = ""
                if log_time_data != None:
                    time_guard_addition = " && updatesSincePropagation == globalLogIndex"

                    current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_forced_prop_2)
                    current_transition.guard = f"(updatesSincePropagation + maxUpdatesSincePropagation_{json_transfer.name} > globalLogIndex)" + time_guard_addition

                    time_guard_addition = " && updatesSincePropagation != globalLogIndex"

                current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_initial)
                current_transition.guard = f"(updatesSincePropagation + maxUpdatesSincePropagation_{json_transfer.name} > globalLogIndex)" + time_guard_addition

                current_transition = self.find_transition(transitions, l_source=l_accepting_emitted_2, l_target=l_prop2)
                current_transition.guard = f"!(updatesSincePropagation + maxUpdatesSincePropagation_{json_transfer.name} > globalLogIndex)"

                # Adding the new transitions for ensuring forced propagation happens in order.
                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_updating_role_1,
                target=l_forced_prop_3,
                guard="""currentLog[counter].orderCount == 0 &&
                    anyForcedToPropagate &&
                    currentLogToPropagate == id_start + id && 
                    forcedToPropagate[id + id_start]""",
                synchronisation="attempt_propagation!",
                assignment="""didLogChange := false,
                    backTracking := false,
                    eventsToRead := 0""",
                nails=[(-238, 272), (442, 272), (442, -289)]
                ))
                
                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_initial,
                target=l_forced_prop_3,
                guard=f"newUpdates && !(updatesSincePropagation + maxUpdatesSincePropagation_{json_transfer.name} > globalLogIndex)",
                synchronisation="force_propagate?",
                assignment="forcedToPropagate[id + id_start] := true"
                ))

                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_initial,
                target=l_forced_prop_3,
                synchronisation="attempt_propagation?",
                guard="forcedToPropagate[id + id_start]",
                nails=[(238,-204)]
                ))

                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_forced_prop_3,
                target=l_initial,
                synchronisation="abandon_propagation?",
                nails=[(306,-170)]
                ))

                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_forced_prop_3,
                target=l_forced_prop_3,
                guard="!(forcedToPropagate[forcedPropagationCounter])",
                assignment="forcedPropagationCounter++"
                ))

                transitions.append(Transition(
                id=Utils.get_next_id(),
                source=l_forced_prop_3,
                target=l_prop1,
                guard="""(forcedToPropagate[forcedPropagationCounter]) &&
                    forcedPropagationCounter == (id + id_start)""",
                synchronisation="abandon_propagation!",
                assignment="""forcedToPropagate[forcedPropagationCounter] := false,
                    forcedPropagationCounter := 0,
                    calculateAnyForcedToPropagate(),
                    currentLogToPropagate = (id_start + id + 1) % amountOfLogs,
                    updatesSincePropagation := 0,
                    newUpdates := false,
                    setPropagationLog(currentLog)"""
                ))


        
        super().__init__(name + "_log", parameter, declaration, locations, l_initial, transitions)

    def find_transition(self, transitions, l_source, l_target):
        res_list = []

        for transition in transitions:
            if transition.source == l_source and transition.target == l_target:
                res_list.append(transition)

        if len(res_list) == 1:
            return res_list[0]

        return res_list
