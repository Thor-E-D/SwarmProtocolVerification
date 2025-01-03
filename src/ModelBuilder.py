"""\
Creates and holds all information for a log.
Log is constructed differently depeding on given settings,
such as if time is included and what kind of delay in propagation is used.

"""
from typing import List, Dict
from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from DataObjects.Declaration import Declaration
from DataObjects.JSONTransfer import JSONTransfer
from DataObjects.Channel import Channel
from DataObjects.ModelSettings import ModelSettings, DelayType
from DataObjects.Model import Model
from JSONParser import parse_projection_JSON_file
from Utils import Utils
from Functions import *
from Log import Log
from Role import Role
from GraphAnalyser import analyze_graph

def add_branching_functionality(declaration: Declaration, branching_events, eventname_to_UID_dict):
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

def calculate_relevant_mappings(jsonTransfers: List[JSONTransfer], name_amount_dict: Dict[str, int]):
    eventnames_dict = {} # Maps eventname/logtypes to Unique names 
    amount_names = {} # Maps role name to typedef name. 
    advance_channels = {} # Maps role name to advance channel.
    update_channels = {} # Maps role name to update channel.
    reset_channels = {} # Maps role name to reset channel

    log_id_start = 0

    for jsonTransfer in jsonTransfers:
        current_advance_channel_names = []
        current_advance_channel_dict = {}
        for subscription in jsonTransfer.subscriptions:
            advance_channel_name = (f"advance_{jsonTransfer.name}_{subscription}")
            current_advance_channel_names.append(advance_channel_name)
            current_advance_channel_dict[subscription] = advance_channel_name
            eventnames_dict[subscription] = (Utils.get_eventtype_UID(subscription))
        
        jsonTransfer.log_id_start = log_id_start
        log_id_start += name_amount_dict[jsonTransfer.name]

        jsonTransfer.advance_channel_names = current_advance_channel_dict
        advance_channels[jsonTransfer.name] = current_advance_channel_names
        jsonTransfer.do_update_channel_name = f"do_log_update_{jsonTransfer.name}"
        update_channels[jsonTransfer.name] = (f"do_log_update_{jsonTransfer.name}")
        jsonTransfer.reset_channel_name = f"reset_{jsonTransfer.name}"
        reset_channels[jsonTransfer.name] = (f"reset_{jsonTransfer.name}")

        amount_names[jsonTransfer.name] = f"{jsonTransfer.name}_t"

    return eventnames_dict, amount_names, advance_channels, update_channels, reset_channels

def add_functions(declaration: Declaration):
    # Ordering is important as some functions depend on others.
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
def create_flow_list(jsonTransfer: JSONTransfer, eventname_to_UID_dict) -> tuple[int, List[List[int]]]:
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

def enrich_json(jsonTransfers, eventnames_dict):
    for jsonTransfer in jsonTransfers:
        jsonTransfer.total_amount_of_events = len(eventnames_dict)

    set_of_preceding_events = defaultdict(set)
    max_amount_of_preceding_events = 1
    branching_events = None
    all_loop_events = set()

    for jsonTransfer in jsonTransfers:
        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)

        analysis_results = (analyze_graph(all_events, jsonTransfer.initial))
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

        for key_event in preceding_events:
            name_of_event = Utils.get_eventtype_UID(key_event.event_name)
            for event in preceding_events[key_event]:
                set_of_preceding_events[name_of_event].add(Utils.get_eventtype_UID(event.event_name))
            
            if len(set_of_preceding_events[name_of_event]) > max_amount_of_preceding_events:
                max_amount_of_preceding_events = len(set_of_preceding_events[name_of_event])

    all_loop_event_names = set()
    for loop_event in all_loop_events:
        all_loop_event_names.add(Utils.get_eventtype_UID(loop_event.event_name))
    return set_of_preceding_events,max_amount_of_preceding_events,branching_events,all_loop_event_names

# Creates UPPAAL functions for setting what event each event should be based on
def create_basedOn_functions(jsonTransfers, name_amount_dict, eventnames_dict, declaration):
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
    eventnames_dict, amount_names, advance_channels, update_channels, reset_channels = calculate_relevant_mappings(jsonTransfers, model_settings.role_amount)
    name_amount_dict = model_settings.role_amount

    # Set total amount of events
    set_of_preceding_events, max_amount_of_preceding_events, branching_events, all_loop_event_names = enrich_json(jsonTransfers, eventnames_dict)


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
    declaration.add_variable("logEntryType trueGlobalLog[logSize];")
    declaration.add_variable("int trueDiscardedEvents[logSize];")
    declaration.add_variable("int trueDiscardedDueToCompetionEvents[logSize];")
    declaration.add_variable("int trueCurrentIndex = -1;")
    declaration.add_variable("int currentEventResetID = -1;")

    if model_settings.time_json_transfer != None:
        declaration.add_variable(f"clock globalTime;")

    number_of_names = []
    for name in name_amount_dict:
        declaration.add_variable(f"const int NUMBER_OF_{name} = {name_amount_dict[name]};")
        declaration.add_variable(f"typedef int[0,NUMBER_OF_{name}-1] {amount_names[name]};")
        number_of_names.append(f"NUMBER_OF_{name}")

    amount_of_logs_string = "int amountOfLogs = "
    for number_of_name in number_of_names:
        if number_of_names.index(number_of_name) != len(number_of_names) - 1:
            amount_of_logs_string += number_of_name + " + "
        else:
            amount_of_logs_string += number_of_name + ";"
    declaration.add_variable(amount_of_logs_string)

    declaration.add_variable("int currentLogToPropagate;")
    declaration.add_variable("int amountOfPropagation = 0;")    


    # For branch tracking we create a list which ties each event to the branches before it
    eventsTiedTo = "const int eventsTiedTo[amountOfUniqueEvents][maxAmountOfTied] = {"
    counter = 0
    eventname_to_UID_dict = {}
    for event_key in eventnames_dict:
        declaration.add_variable(f"const int {eventnames_dict[event_key]} = {counter};")
        eventname_to_UID_dict[eventnames_dict[event_key]] = counter
        counter += 1

        tiedTo = "{"
        tiedTolength = 0
        if eventnames_dict[event_key] in set_of_preceding_events:
                tiedTolength = len(set_of_preceding_events[eventnames_dict[event_key]])
                for event_name in set_of_preceding_events[eventnames_dict[event_key]]:
                    tiedTo += "" + event_name + ", "
                        
        
        tiedTo += "-1, " * (max_amount_of_preceding_events - tiedTolength)
        eventsTiedTo += tiedTo[:-2] + "}, "

    eventsTiedTo = eventsTiedTo[:-2] + "};"
    
    declaration.add_variable(f"const int amountOfUniqueEvents = {counter};")

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

    declaration.add_variable(f"const int maxAmountOfTied = {max_amount_of_preceding_events};")
    declaration.add_variable(eventsTiedTo)

    # Channels
    declaration.add_channel(Channel(urgent=True,broadcast=True, name="propagate_log"))

    for name in name_amount_dict:
        currentAmount = amount_names[name]
        declaration.add_channel(Channel(urgent=False, type=currentAmount, name=update_channels[name]))
        declaration.add_channel(Channel(urgent=False, type=currentAmount, name=reset_channels[name]))
        list_of_advance_channels = advance_channels[name]
        for advance_channel in list_of_advance_channels:
            declaration.add_channel(Channel(urgent=False, broadcast=True, type=currentAmount, name=advance_channel))

    # Functions
    add_functions(declaration)
    create_basedOn_functions(jsonTransfers, name_amount_dict, eventnames_dict, declaration)

    # Adding templates comprised of roles and logs for each jsonTransfer we create one of each.
    roles = []
    logs = []

    for jsonTransfer in jsonTransfers:
        if model_settings.delay_type[jsonTransfer.name] != DelayType.NOTHING:
                declaration.add_variable(f"int maxUpdatesSincePropagation_{jsonTransfer.name} = {model_settings.delay_amount[jsonTransfer.name]};")

        role = None
        if model_settings.time_json_transfer == None:
            role = Role(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.loop_bound, [])
        else:
            role = Role(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.loop_bound, model_settings.time_json_transfer.event_time_data)
        roles.append(role)

        # Adding loopcounter to global decleration
        current_evetname_loopcounter = role.get_evetname_loopcounter()
        for eventname in current_evetname_loopcounter:
            declaration.add_variable(f"int {current_evetname_loopcounter[eventname]} = 0;")

        log = None
        if model_settings.time_json_transfer == None:
            log = Log(amount_names[jsonTransfer.name] + " id", jsonTransfer,current_evetname_loopcounter, model_settings.log_size, model_settings.delay_type[jsonTransfer.name])
        else:
            log_time_data_role = next((log_time_data for log_time_data in model_settings.time_json_transfer.log_time_data if log_time_data.role_name == jsonTransfer.name), None)
            log = Log(amount_names[jsonTransfer.name] + " id", jsonTransfer,current_evetname_loopcounter, model_settings.log_size,model_settings.delay_type[jsonTransfer.name], log_time_data_role)
        logs.append(log)

    return Model(declaration, roles, logs)