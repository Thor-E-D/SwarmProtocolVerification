"""\
Creates and holds all information for a log.
Log is constructed differently depeding on given settings,
such as if time is included and what kind of delay in propagation is used.

"""
from typing import List, Dict, Set
from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from DataObjects.Declaration import Declaration
from DataObjects.JSONTransfer import JSONTransfer, EventData
from DataObjects.Channel import Channel
from DataObjects.ModelSettings import ModelSettings, DelayType
from DataObjects.Model import Model
from Utils import Utils
from Functions import *
from Log import Log
from Role import Role
from GraphAnalyser import GraphAnalyser

def add_branching_functionality(declaration: Declaration, branching_events: Set[EventData], eventname_to_UID_dict: Dict[str, int]):
    # Handling branching events
    # based on source partition the branching events into set so we have a list of sets
    sorted_events = sorted(branching_events, key=attrgetter('source'))
    partioned_branching_events = [{Utils.get_eventtype_UID(event.event_name) for event in group}
        for _, group in groupby(sorted_events, key=attrgetter('source'))]
    
    outer_size = len(partioned_branching_events)
    inner_size_max = 0

    for partition in partioned_branching_events:
        if (len(partition) > inner_size_max):
            inner_size_max = len(partition)

    # We now generate two list one which holds a boolean for if each event is branching 
    # and one with which partition the branching event is in
    is_branching_list = [False] * len(eventname_to_UID_dict)
    is_in_branching_partion = [-1] * len(eventname_to_UID_dict)

    for eventname in eventname_to_UID_dict:
        count = eventname_to_UID_dict[eventname]
        for index, s in enumerate(partioned_branching_events):
            if eventname in s:
                is_branching_list[count] = True
                is_in_branching_partion[count] = index

    partioned_branching_events_UID = []
    for partition in partioned_branching_events:
        partition_list = []
        for e in partition:
            partition_list.append(eventname_to_UID_dict[e])
        partioned_branching_events_UID.append(partition_list)

    # add padding
    for partition in partioned_branching_events_UID:
        current_partition_len = len(partition)
        for _ in range(inner_size_max - current_partition_len):
            partition.append(-1)

    if len(branching_events) == 0 :
        declaration.add_variable(f"const int outerSizeBranchingList = 1;")
        declaration.add_variable(f"const int innerSizeBranchingList = 1;")
        declaration.add_variable("const int branchingList[outerSizeBranchingList][innerSizeBranchingList] = { {-1 } };")
    else:
        declaration.add_variable(f"const int outerSizeBranchingList = {outer_size};")
        declaration.add_variable(f"const int innerSizeBranchingList = {inner_size_max};")
        declaration.add_variable("const int branchingList[outerSizeBranchingList][innerSizeBranchingList] =" +
                                            f"{Utils.python_list_to_uppaal_list(partioned_branching_events_UID)};")
    declaration.add_variable(f"const int isBranchingList[amountOfUniqueEvents] = {Utils.python_list_to_uppaal_list(is_branching_list).lower()};")
    declaration.add_variable(f"const int isInBranchingPartion[amountOfUniqueEvents] = {Utils.python_list_to_uppaal_list(is_in_branching_partion)};")

def calculate_relevant_mappings(jsonTransfers: List[JSONTransfer]):
    eventnames_dict = {} # Maps eventname/logtypes to Unique names 
    amount_names = {} # Maps role name to typedef name. 
    advance_channels = {} # Maps role name to advance channel.
    update_channels = {} # Maps role name to update channel.
    reset_channels = {} # Maps role name to reset channel

    for jsonTransfer in jsonTransfers:
        current_advance_channel_names = []
        current_advance_channel_dict = {}
        for subscription in jsonTransfer.subscriptions:
            advance_channel_name = (f"advance_{jsonTransfer.name}_{subscription}")
            current_advance_channel_names.append(advance_channel_name)
            current_advance_channel_dict[subscription] = advance_channel_name
            eventnames_dict[subscription] = (Utils.get_eventtype_UID(subscription))

        jsonTransfer.advance_channel_names = current_advance_channel_dict
        advance_channels[jsonTransfer.name] = current_advance_channel_names
        jsonTransfer.do_update_channel_name = f"do_log_update_{jsonTransfer.name}"
        update_channels[jsonTransfer.name] = (f"do_log_update_{jsonTransfer.name}")
        jsonTransfer.reset_channel_name = f"reset_{jsonTransfer.name}"
        reset_channels[jsonTransfer.name] = (f"reset_{jsonTransfer.name}")

        amount_names[jsonTransfer.name] = f"{jsonTransfer.name}_t"

    return eventnames_dict, amount_names, advance_channels, update_channels, reset_channels

def add_functions(declaration: Declaration, using_global_event_bound: bool, exit_paths_exist: bool):
    # Ordering is important as some functions depend on others.
    if exit_paths_exist:
        declaration.add_function_call(generate_function_update_exit_path_guards)
    if using_global_event_bound:
        declaration.add_function_call(generate_function_calculate_any_forced_to_propagte)
    declaration.add_function_call(generate_function_is_in_subsciption)
    declaration.add_function_call(generate_function_is_int_in_list)
    declaration.add_function_call(generate_function_is_order_count_in_log)
    declaration.add_function_call(generate_function_get_entry_from_order_count)
    declaration.add_function_call(generate_function_add_int_to_list)
    declaration.add_function_call(generate_function_get_event_id_from_order_count)
    declaration.add_function_call(generate_function_set_next_log_to_propagate)
    declaration.add_function_call(generate_function_get_order_count)
    declaration.add_function_call(generate_function_set_log_entry_for_update)
    declaration.add_function_call(generate_function_find_difference_in_logs)
    declaration.add_function_call(generate_function_find_and_set_difference_in_logs)
    declaration.add_function_call(generate_function_find_and_set_tiedto)
    declaration.add_function_call(generate_function_set_propagation_log)
    declaration.add_function_call(generate_function_is_In_branching_conflict)
    declaration.add_function_call(generate_function_consolidate_logs)
    declaration.add_function_call(generate_function_check_and_fix_branch_competetion)
    declaration.add_function_call(generate_function_handle_branching_event_standard_setting)
    declaration.add_function_call(generate_function_handle_branching_event)
    declaration.add_function_call(generate_function_handle_standard_setting)
    declaration.add_function_call(generate_function_handle_standard_event)
    declaration.add_function_call(generate_function_handle_own_event)
    declaration.add_function_call(generate_function_update_true_global_log)
    declaration.add_function_call(generate_function_update_global_log)
    declaration.add_function_call(generate_function_update_log)

# Creates the list and variables for keeping track of where the role currently is.
def create_flow_list(jsonTransfer: JSONTransfer, eventname_to_UID_dict: Dict[str, int]) -> tuple[int, List[List[int]]]:
    # We first need to map all locations to a unigue int ID
    location_map = {}
    counter = 0

    all_events = jsonTransfer.own_events.copy()
    all_events.extend(jsonTransfer.other_events)

    for event in all_events:
        if event.source not in location_map.keys():
            location_map[event.source] = counter
            counter += 1
        if event.target not in location_map.keys():
            location_map[event.target] = counter
            counter += 1

    flow_list = [[-1, -1] for _ in range(len(eventname_to_UID_dict))]
    for event_name in eventname_to_UID_dict:
        current_event_name = event_name[:-3]
        current_index = eventname_to_UID_dict[event_name]

        current_event = next(
            (event for event in all_events if event.event_name == current_event_name),
            None  # Default value if no match is found
        )

        if current_event is None:
            continue

        flow_list[current_index][0] = location_map[current_event.source]
        flow_list[current_index][1] = location_map[current_event.target]

    return location_map[jsonTransfer.initial], flow_list

def enrich_json(start_exit_path_events: List[EventData], jsonTransfers: List[JSONTransfer], eventnames_dict: Dict[str,str]):
    for jsonTransfer in jsonTransfers:
        jsonTransfer.total_amount_of_events = len(eventnames_dict)

    set_of_preceding_events = defaultdict(set)
    max_amount_of_preceding_events = 1
    branching_events = None
    all_loop_events = set()
    
    target_start_loop_events = {}

    for jsonTransfer in jsonTransfers:
        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)

        analyzer = GraphAnalyser(all_events)
        analysis_results = (analyzer.analyse_graph(jsonTransfer.initial))
        preceding_events = analysis_results["preceding_events"]
        branching_events = analysis_results["branching_events"]
        loop_events = analysis_results["loop_events"]

        # For bound loop events
        jsonTransfer.loop_events = []
        for loop_event in loop_events:
            if loop_event in jsonTransfer.own_events:
                jsonTransfer.loop_events.append(loop_event.event_name)

            # add to all loop events
            all_loop_events = all_loop_events.union(loop_events[loop_event])
            all_loop_events.add(loop_event)

            # Find events that lead to the start of loop as they have to check if
            # Exit should be enabled.
            if loop_event in start_exit_path_events:
                for inner_event in all_events:
                    if inner_event.target == loop_event.source:
                        if inner_event in target_start_loop_events.keys():
                            target_start_loop_events[inner_event].append(loop_event)
                        else:    
                            target_start_loop_events[inner_event] = [loop_event]

        for key_event in preceding_events:
            name_of_event = Utils.get_eventtype_UID(key_event.event_name)
            for event in preceding_events[key_event]:
                set_of_preceding_events[name_of_event].add(Utils.get_eventtype_UID(event.event_name))
            
            if len(set_of_preceding_events[name_of_event]) > max_amount_of_preceding_events:
                max_amount_of_preceding_events = len(set_of_preceding_events[name_of_event])
        
        # Have to set what events need exit path guards
        # and what events needs to test for end of loop.
        exit_own_events = []
        check_loop_exit_events = {}
        for own_event in jsonTransfer.own_events:
            if own_event in all_loop_events and own_event.target != own_event.source and start_exit_path_events != []:
                exit_own_events.append(own_event.event_name)

            if own_event in target_start_loop_events.keys():
                check_loop_exit_events[own_event] = target_start_loop_events[own_event]
            
        
        if exit_own_events != []:
            jsonTransfer.exit_events = exit_own_events
        
        if check_loop_exit_events != {}:
            jsonTransfer.check_loop_exit_events = check_loop_exit_events

    all_loop_event_names = set()
    for loop_event in all_loop_events:
        all_loop_event_names.add(Utils.get_eventtype_UID(loop_event.event_name))
        
    return branching_events, all_loop_event_names

# Creates UPPAAL functions for setting what event each event should be based on
def create_basedOn_functions(jsonTransfers: List[JSONTransfer], name_amount_dict: Dict[str, int], eventnames_dict: Dict[str, str], declaration: Declaration):
    name_basedOnEvents = {}
    for jsonTransfer in jsonTransfers:
        basedOnEvents = {}

        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)

        for current_event in jsonTransfer.own_events:
            for event in all_events:
                if event.target == current_event.source:
                    if eventnames_dict[current_event.event_name] in basedOnEvents:
                        basedOnEvents[eventnames_dict[current_event.event_name]].append(eventnames_dict[event.event_name])
                    else:
                        basedOnEvents[eventnames_dict[current_event.event_name]] = [eventnames_dict[event.event_name]]
    
        name_basedOnEvents[jsonTransfer.name] = basedOnEvents


    for name in name_amount_dict:
        declaration.add_function_call(generate_function_update_log_name, name,name_basedOnEvents[name])


def createModel(jsonTransfers: List[JSONTransfer], globalJsonTransfer: JSONTransfer, model_settings: ModelSettings):
    # We first create the nessesary variable names to be used in UPPAAL.
    eventnames_dict, amount_names, advance_channels, update_channels, reset_channels = calculate_relevant_mappings(jsonTransfers)
    name_amount_dict = model_settings.role_amount

    # Get all exit events for enriching JSONs
    all_events = globalJsonTransfer.own_events.copy()
    all_events.extend(globalJsonTransfer.other_events)

    analyzer = GraphAnalyser(all_events)
    analysis_results = (analyzer.analyse_graph(globalJsonTransfer.initial))
    exit_paths = analysis_results["exit_paths"]
    loop_events = analysis_results["loop_events"]
    global_branching_events = analysis_results["branching_events"]
    start_looping_events = []
    for start_loop_event in loop_events:
        start_looping_events.append(start_loop_event)

    start_exit_path_events = list(exit_paths.keys())

    all_exit_events = set()
    for exit_event in exit_paths:
        all_exit_events.update(exit_paths[exit_event])

    # Set total amount of events
    branching_events, all_loop_event_names = enrich_json(start_exit_path_events, jsonTransfers, eventnames_dict)

    # set flag if any are using global events as bounds
    using_global_event_bound = False
    for key_role in model_settings.delay_type:
        if model_settings.delay_type[key_role] == DelayType.EVENTS_EMITTED:
            using_global_event_bound = True
            break

    declaration = Declaration()

    declaration.add_variable(f"const bool standardSetting = {str(model_settings.standard_setting).lower()};")
    declaration.add_variable(f"const int logSize = {model_settings.log_size};")
    declaration.add_variable("typedef int [0, logSize - 1] logSize_t;")

    declaration.add_variable("""typedef struct {
    int eventID;
    int emitterID;
    int orderCount;
    int basedOnOrderCount;
    int tiedTo;
    bool ignored;
} logEntryType;""")
    declaration.add_variable("int eventOrderCounter = 1;")
    declaration.add_variable("logEntryType tempLogEntry;")
    declaration.add_variable("logEntryType propagationLog[logSize];")
    declaration.add_variable("logEntryType globalLog[logSize];")
    declaration.add_variable("int globalLogIndex = 0;")
    declaration.add_variable("logEntryType trueGlobalLog[logSize];")
    declaration.add_variable("int trueDiscardedEvents[logSize];")
    declaration.add_variable("int trueDiscardedDueToCompetionEvents[logSize];")
    declaration.add_variable("int trueCurrentIndex = -1;")
    declaration.add_variable("int currentEventResetID = -1;")

    if model_settings.time_json_transfer != None:
        declaration.add_variable(f"clock globalTime;")

    number_of_names = []
    log_id_start_entries = {}
    log_id_start_sumizer = "0"
    for name in name_amount_dict:
        log_id_start_entries[name] = log_id_start_sumizer
        current_variable = f"NUMBER_OF_{name}"
        declaration.add_variable(f"const int {current_variable} = {name_amount_dict[name]};")
        declaration.add_variable(f"typedef int[0,{current_variable}-1] {amount_names[name]};")
        number_of_names.append(current_variable)
        log_id_start_sumizer += f" + {current_variable}"

    for jsonTransfer in jsonTransfers:
        jsonTransfer.log_id_start = log_id_start_entries[jsonTransfer.name]  

    amount_of_logs_string = "const int amountOfLogs = "
    for number_of_name in number_of_names:
        if number_of_names.index(number_of_name) != len(number_of_names) - 1:
            amount_of_logs_string += number_of_name + " + "
        else:
            amount_of_logs_string += number_of_name + ";"
    declaration.add_variable(amount_of_logs_string)

    declaration.add_variable("int currentLogToPropagate;")
    declaration.add_variable("int amountOfPropagation = 0;") 

    # For branch tracking we create a list which ties each event to the branches before it
    tiedto_dict = analyzer.find_tiedto(global_branching_events)
    max_branches_before = 1
    for set_of_events in tiedto_dict.values():
        if len(set_of_events) > max_branches_before:
            max_branches_before = len(set_of_events)

    eventsTiedTo = "const int eventsTiedTo[amountOfUniqueEvents][maxAmountOfTied] = {"
    counter = 0
    eventname_to_UID_dict = {}
    for event_key in eventnames_dict:
        declaration.add_variable(f"const int {eventnames_dict[event_key]} = {counter};")
        eventname_to_UID_dict[eventnames_dict[event_key]] = counter
        counter += 1

        tiedTo = "{"
        tiedTolength = len(tiedto_dict[event_key])
        for tiedto_event in tiedto_dict[event_key]:
            tiedTo += "" + Utils.get_eventtype_UID(tiedto_event.event_name) + ", "                        
        
        tiedTo += "-1, " * (max_branches_before - tiedTolength)
        eventsTiedTo += tiedTo[:-2] + "}, "

    eventsTiedTo = eventsTiedTo[:-2] + "};"

    declaration.add_variable(f"const int amountOfUniqueEvents = {counter};")
    declaration.add_variable(f"const int maxAmountOfTied = {max_branches_before};")
    declaration.add_variable(eventsTiedTo)

    # Variables for exiting loops
    if exit_paths != {}:
        current_bool_map = []
        loop_exit_path_maps = []

        for event_name_temp in eventnames_dict:
            # Get int by eventname_to_UID_dict[eventnames_dict[event_name_temp]]
            if event_name_temp in start_looping_events:
                current_bool_map.append(False)
            else:
                current_bool_map.append(True)

            if event_name_temp in start_exit_path_events:
                current_event = None
                for event in all_events:
                    if event.event_name == event_name_temp:
                        current_event = event
                        break
                loop_exit_path_map = []
                for event_name_temp_two in eventnames_dict:
                    current_event_two = None
                    for event in all_events:
                        if event.event_name == event_name_temp_two:
                            current_event_two = event
                            break
                    if event_name_temp == event_name_temp_two:
                        loop_exit_path_map.append(1)

                    elif current_event_two in loop_events[current_event] and current_event_two in exit_paths[current_event]:
                        loop_exit_path_map.append(1)

                    elif current_event_two in loop_events[current_event]:
                        loop_exit_path_map.append(0)
                    else:
                        loop_exit_path_map.append(-1)
                loop_exit_path_maps.append(loop_exit_path_map)

            else:
                loop_exit_path_maps.append(([-1] * counter))

        declaration.add_variable(f"const int loopBound = {model_settings.loop_bound};") # Need for function
        declaration.add_variable(f"const int allExitEventMaps[amountOfUniqueEvents][amountOfUniqueEvents] = {Utils.python_list_to_uppaal_list(str(loop_exit_path_maps))};")
        declaration.add_variable(f"int exitEventMap[amountOfUniqueEvents] = {Utils.python_list_to_uppaal_list(str(current_bool_map).lower())};")


    add_branching_functionality(declaration, branching_events, eventname_to_UID_dict)

    # Creating a list to use for letting the log know where we are
    global_pointer, global_flow_list = create_flow_list(globalJsonTransfer, eventname_to_UID_dict)
    declaration.add_variable(f"int globalCurrentLocation = {global_pointer};")
    declaration.add_variable(f"const int globalEventLocationMap[amountOfUniqueEvents][2] = {Utils.python_list_to_uppaal_list(global_flow_list)};")

    for jsonTransfer in jsonTransfers:
        initial_pointer, flow_list = create_flow_list(jsonTransfer, eventname_to_UID_dict)
        jsonTransfer.initial_pointer = initial_pointer
        jsonTransfer.flow_list = flow_list

    # looping list
    is_in_loop_list = [False] * len(eventname_to_UID_dict)
    for event_key in eventname_to_UID_dict:
        if event_key in all_loop_event_names:
            is_in_loop_list[eventname_to_UID_dict[event_key]] = True
    declaration.add_variable(f"const int isInLoop[amountOfUniqueEvents] = {Utils.python_list_to_uppaal_list(is_in_loop_list).lower()};")

    # Channels
    declaration.add_channel(Channel(urgent=True,broadcast=True, name="propagate_log"))
    declaration.add_channel(Channel(broadcast=True, name="chan_overflow"))

    for name in name_amount_dict:
        currentAmount = amount_names[name]
        declaration.add_channel(Channel(urgent=False, type=currentAmount, name=update_channels[name]))
        declaration.add_channel(Channel(urgent=False, type=currentAmount, name=reset_channels[name]))
        list_of_advance_channels = advance_channels[name]
        for advance_channel in list_of_advance_channels:
            declaration.add_channel(Channel(urgent=False, broadcast=True, type=currentAmount, name=advance_channel))


    if using_global_event_bound:
        declaration.add_variable("int forcedPropagationCounter = 0;")
        # Calculate global amount of logs
        global_amount_of_logs = 0
        for key in name_amount_dict:
            global_amount_of_logs += name_amount_dict[key]
        
        forced_to_propagte_str = "bool forcedToPropagate[amountOfLogs] = {"
        for _ in range(global_amount_of_logs):
            forced_to_propagte_str += "false, " 
        forced_to_propagte_str = forced_to_propagte_str[:-2] + "};"
        declaration.add_variable(forced_to_propagte_str)
        declaration.add_variable("bool anyForcedToPropagate = false;")
        declaration.add_channel(Channel(urgent=False, broadcast=True, name="abandon_propagation"))
        declaration.add_channel(Channel(urgent=False, broadcast=True, name="attempt_propagation"))
        declaration.add_channel(Channel(urgent=False, broadcast=True, name="force_propagate"))

    # Functions
    add_functions(declaration, using_global_event_bound, exit_paths != {})
    create_basedOn_functions(jsonTransfers, name_amount_dict, eventnames_dict, declaration)

    # Adding templates comprised of roles and logs for each jsonTransfer we create one of each.
    roles = []
    logs = []
    all_start_loop_events = set()

    for jsonTransfer in jsonTransfers:
        if model_settings.delay_type[jsonTransfer.name] != DelayType.NOTHING:
                declaration.add_variable(f"int maxUpdatesSincePropagation_{jsonTransfer.name} = {model_settings.delay_amount[jsonTransfer.name]};")
        else:
            # If using a nothing delay we simply set to 0 with since functionality is the same but simplfies log construction.
            # Need to keep DelayType.NOTHING as flag for log construction
            declaration.add_variable(f"int maxUpdatesSincePropagation_{jsonTransfer.name} = 0;")

        role = None
        if model_settings.time_json_transfer == None:
            role = Role(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.loop_bound, [])
        else:
            role = Role(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.loop_bound, model_settings.time_json_transfer.event_time_data)
        roles.append(role)

        # Adding loopcounter to global decleration
        current_evetname_loopcounter = role.get_evetname_loopcounter()
        for eventname in current_evetname_loopcounter:
            current_loopcounter_string = (f"int {current_evetname_loopcounter[eventname]}[{name_amount_dict[jsonTransfer.name]}] = {{")
            for i in range (name_amount_dict[jsonTransfer.name]):
                current_loopcounter_string += "0, "
            declaration.add_variable(current_loopcounter_string[:-2] + "};")
        all_start_loop_events.update(jsonTransfer.loop_events)

        log = None
        if model_settings.time_json_transfer == None:
            log = Log(amount_names[jsonTransfer.name] + " id", jsonTransfer,current_evetname_loopcounter, model_settings.log_size, model_settings.delay_type[jsonTransfer.name], using_global_event_bound)
        else:
            log_time_data_role = next((log_time_data for log_time_data in model_settings.time_json_transfer.log_time_data if log_time_data.role_name == jsonTransfer.name), None)
            log = Log(amount_names[jsonTransfer.name] + " id", jsonTransfer,current_evetname_loopcounter, model_settings.log_size,model_settings.delay_type[jsonTransfer.name], using_global_event_bound, log_time_data_role)
        logs.append(log)

    #Adding start loop event to global decleration
    all_start_loop_events = [Utils.get_eventtype_UID(event_name_UID) for event_name_UID in all_start_loop_events]
    loop_events_string = "int loopCountMap[amountOfUniqueEvents] = {"
    for event_name_ID in eventname_to_UID_dict:
        if event_name_ID in all_start_loop_events:
            loop_events_string += "0 ,"
        else:
            loop_events_string += "-1 ,"
    declaration.add_variable(loop_events_string[:-2] + "};")

    return Model(declaration, roles, logs)