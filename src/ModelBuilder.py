"""\
Creates all global variables and functions.
Along with the required number of role and log templates.

Most central logic is captured within this class

"""
from typing import List, Dict, Set
from itertools import groupby
from operator import attrgetter

from DataObjects.Declaration import Declaration
from DataObjects.JSONTransfer import JSONTransfer, EventData
from DataObjects.Channel import Channel
from DataObjects.ModelSettings import ModelSettings, DelayType
from DataObjects.Model import Model
from DataObjects.TimeJSONTransfer import EventTimeData
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
    backtrack_channels = {} # Maps role name to reset channel

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
        jsonTransfer.backtrack_channel_name = f"backtrack_{jsonTransfer.name}"
        backtrack_channels[jsonTransfer.name] = (f"backtrack_{jsonTransfer.name}")

        amount_names[jsonTransfer.name] = f"{jsonTransfer.name}_t"

    return eventnames_dict, amount_names, advance_channels, update_channels, backtrack_channels

def add_functions(declaration: Declaration, using_global_event_bound: bool):
    # Ordering is important as some functions depend on others.
    if using_global_event_bound:
        declaration.add_function_call(generate_function_calculate_any_forced_to_propagte)
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
    declaration.add_function_call(generate_function_find_tiedto)
    declaration.add_function_call(generate_function_set_propagation_log)
    declaration.add_function_call(generate_function_is_In_branching_conflict)
    declaration.add_function_call(generate_function_consolidate_logs)
    declaration.add_function_call(generate_function_check_and_fix_branch_competetion)
    declaration.add_function_call(generate_function_handle_branching_event)
    declaration.add_function_call(generate_function_handle_event)
    declaration.add_function_call(generate_function_update_true_global_log)
    declaration.add_function_call(generate_function_update_global_log)
    declaration.add_function_call(generate_function_update_log)
    declaration.add_function_call(generate_function_update_log_entry)

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

def enrich_json(jsonTransfers: List[JSONTransfer], eventnames_dict: Dict[str,str], global_non_exit_paths: Set[EventData]):
    for jsonTransfer in jsonTransfers:
        jsonTransfer.total_amount_of_events = len(eventnames_dict)

    branching_events = None

    for jsonTransfer in jsonTransfers:
        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)

        analyzer = GraphAnalyser(all_events)
        analysis_results = (analyzer.analyse_graph(jsonTransfer.initial))
        branching_events = analysis_results["branching_events"]

        non_exit_paths = global_non_exit_paths

        jsonTransfer.non_exit_events = non_exit_paths  
        
    return branching_events

def createModel(jsonTransfers: List[JSONTransfer], globalJsonTransfer: JSONTransfer, model_settings: ModelSettings):
    # We first create the nessesary variable names to be used in UPPAAL.
    eventnames_dict, amount_names, advance_channels, update_channels, backtrack_channels = calculate_relevant_mappings(jsonTransfers)
    name_amount_dict = model_settings.role_amount

    # Get all exit events for enriching JSONs
    all_events = globalJsonTransfer.own_events.copy()
    all_events.extend(globalJsonTransfer.other_events)

    # If some events are timed but others arent it is assumed they are instant so max = 0 and min = 0
    if model_settings.time_json_transfer != None:
        current_time_data_names = []
        for time_data in model_settings.time_json_transfer.event_time_data:
            current_time_data_names.append(time_data.event_name)
        
        for event in all_events:
            if event.event_name not in current_time_data_names:
                etd = EventTimeData(
                    event_name=event.event_name,
                    min_time=0,
                    max_time=0)
                model_settings.time_json_transfer.event_time_data.append(etd)

    analyzer = GraphAnalyser(all_events)
    analysis_results = (analyzer.analyse_graph(globalJsonTransfer.initial))
    non_exit_paths = analysis_results["non_exit_paths"]
    global_branching_events = analysis_results["branching_events"]

    # Set total amount of events
    branching_events = enrich_json(jsonTransfers, eventnames_dict, non_exit_paths)

    # set flag if any are using global events as bounds
    using_global_event_bound = False
    for key_role in model_settings.delay_type:
        if model_settings.delay_type[key_role] == DelayType.EVENTS_EMITTED:
            using_global_event_bound = True
            break

    declaration = Declaration()

    declaration.add_variable(f"const bool branchTrackingEnabled = {str(model_settings.branch_tracking).lower()};")
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
    declaration.add_variable("int currentLogEntryEmitterID = -1;")
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
    total_amount_of_instances = 0
    for name in name_amount_dict:
        total_amount_of_instances += name_amount_dict[name]
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

    # Variables for exiting paths
    if model_settings.path_bound > -1:
        non_exit_path_counter_map = []
        for event_name_temp in eventnames_dict:
            current_event = None
            for event in all_events:
                if event.event_name == event_name_temp:
                    current_event = event
                    break
            
            if current_event in non_exit_paths:
                non_exit_path_counter_map.append(0)
            else:
                non_exit_path_counter_map.append(-1)

        all_counter_map = [non_exit_path_counter_map] * total_amount_of_instances
            
        declaration.add_variable(f"int nonExitCounterMap[amountOfLogs][amountOfUniqueEvents] = {Utils.python_list_to_uppaal_list(str(all_counter_map))};")


    add_branching_functionality(declaration, branching_events, eventname_to_UID_dict)

    # Creating a list to use for letting the log know where we are
    global_pointer, global_flow_list = create_flow_list(globalJsonTransfer, eventname_to_UID_dict)
    declaration.add_variable(f"int globalCurrentLocation = {global_pointer};")
    declaration.add_variable(f"const int globalEventLocationMap[amountOfUniqueEvents][2] = {Utils.python_list_to_uppaal_list(global_flow_list)};")

    for jsonTransfer in jsonTransfers:
        initial_pointer, flow_list = create_flow_list(jsonTransfer, eventname_to_UID_dict)
        jsonTransfer.initial_pointer = initial_pointer
        jsonTransfer.flow_list = flow_list

    # Channels
    declaration.add_channel(Channel(urgent=True,broadcast=True, name="propagate_log"))
    declaration.add_channel(Channel(broadcast=True, name="chan_overflow"))

    for name in name_amount_dict:
        currentAmount = amount_names[name]
        declaration.add_channel(Channel(urgent=False, type=currentAmount, name=update_channels[name]))
        declaration.add_channel(Channel(urgent=False, type=currentAmount, name=backtrack_channels[name]))
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

    # Adding role templates first as we need the loop counters they generated for a global function
    roles = []
    names_roles_dict = {}
    all_eventname_loopcounter = {}

    for jsonTransfer in jsonTransfers:
        role = None
        if model_settings.time_json_transfer == None:
            role = Role(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.path_bound, [])
        else:
            role = Role(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.path_bound, model_settings.time_json_transfer.event_time_data)
        roles.append(role)
        names_roles_dict[jsonTransfer.name] = role

        all_eventname_loopcounter.update(role.get_evetname_loopcounter())

    # Functions
    add_functions(declaration, using_global_event_bound)

    # Adding templates comprised of roles and logs for each jsonTransfer we create one of each.
    logs = []
    all_start_loop_events = set()

    for jsonTransfer in jsonTransfers:
        if model_settings.delay_type[jsonTransfer.name] != DelayType.NOTHING:
                declaration.add_variable(f"int maxUpdatesSincePropagation_{jsonTransfer.name} = {model_settings.delay_amount[jsonTransfer.name]};")
        else:
            # If using a nothing delay we simply set to 0 with since functionality is the same but simplfies log construction.
            # Need to keep DelayType.NOTHING as flag for log construction
            declaration.add_variable(f"int maxUpdatesSincePropagation_{jsonTransfer.name} = 0;")

        log = None
        if model_settings.time_json_transfer == None:
            log = Log(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.log_size, model_settings.delay_type[jsonTransfer.name], using_global_event_bound, eventnames_dict)
        else:
            log_time_data_role = next((log_time_data for log_time_data in model_settings.time_json_transfer.log_time_data if log_time_data.role_name == jsonTransfer.name), None)
            log = Log(amount_names[jsonTransfer.name] + " id", jsonTransfer, model_settings.log_size,model_settings.delay_type[jsonTransfer.name], using_global_event_bound, eventnames_dict, log_time_data_role)
        logs.append(log)

    return Model(declaration, roles, logs)