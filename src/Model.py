from JSONParser import parse_JSON_file
from DataObjects.Declaration import Declaration
from DataObjects.JSONTransfer import JSONTransfer
from DataObjects.Channel import Channel
from typing import List, Dict
from collections import defaultdict
from Utils import Utils
from Functions import *
from Log import Log
from Role import Role
from GraphAnalyser import analyze_graph
from operator import attrgetter
from itertools import groupby
import subprocess
import os



currentModel = ""

# attempts to write the contens to a file.
def save_xml_to_file(xml_data: str, file_name: str, file_path: str):
    full_file_path = f"{file_path}/{file_name}.xml"
    
    try:
        with open(full_file_path, 'w', encoding='utf-8') as file:
            file.write(xml_data)
        print(f"XML file saved successfully at {full_file_path}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}") #TODO handle error!!

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


def createModel(jsonTransfers: List[JSONTransfer], name_amount_dict: Dict[str, int], loop_bound: int = 2, standard_setting: bool = False):
    # We first create the nessesary variable names to be used in UPPAAL.
    eventnames_dict = {}
    amount_names = {}
    advance_channels = {}
    update_channels = {}
    reset_channels = {}

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

    for jsonTransfer in jsonTransfers:
        jsonTransfer.total_amount_of_events = len(eventnames_dict)

    final_xml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.6//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd'>
<nta>"""

    set_of_preceding_events = defaultdict(set)
    max_amount_of_preceding_events = 1
    branching_events = None
    loop_events = None

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

        for key_event in preceding_events:
            name_of_event = Utils.get_eventtype_UID(key_event.event_name)
            for event in preceding_events[key_event]:
                set_of_preceding_events[name_of_event].add(Utils.get_eventtype_UID(event.event_name))
            
            if len(set_of_preceding_events[name_of_event]) > max_amount_of_preceding_events:
                max_amount_of_preceding_events = len(set_of_preceding_events[name_of_event])

    declaration = Declaration()

    declaration.add_variable(f"const bool standardSetting = {str(standard_setting).lower()};")

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

    declaration.add_variable("""typedef struct {
    int eventID;
    int emitterID;
    int orderCount;
    int basedOnOrderCount;
    int tiedTo;
    bool ignored;
} logEntryType;""")
    

    declaration.add_variable("int maxUpdatesSincePropagation = 1;")

    declaration.add_variable(f"const int maxAmountOfTied = {max_amount_of_preceding_events};")
    declaration.add_variable(eventsTiedTo)

    log_size = 20
    declaration.add_variable(f"const int logSize = {log_size};") #TODO this size has to depend on the size of model


    declaration.add_variable("int eventOrderCounter = 1;")
    declaration.add_variable("logEntryType tempLogEntry;")
    declaration.add_variable("logEntryType propagationLog[logSize];")
    declaration.add_variable("logEntryType globalLog[logSize];")
    declaration.add_variable("logEntryType trueGlobalLog[logSize];")
    declaration.add_variable("int trueDiscardedEvents[logSize];")
    declaration.add_variable("int trueDiscardedDueToCompetionEvents[logSize];")
    declaration.add_variable("int trueCurrentIndex = -1;")
    declaration.add_variable("int currentEventResetID = -1;")

    # Channels
    declaration.add_channel(Channel(urgent=True,broadcast=True, name="propagate_log"))

    for name in name_amount_dict:
        currentAmount = amount_names[name]
        declaration.add_channel(Channel(urgent=True, type=currentAmount, name=update_channels[name]))
        declaration.add_channel(Channel(urgent=True, type=currentAmount, name=reset_channels[name]))
        list_of_advance_channels = advance_channels[name]
        for advance_channel in list_of_advance_channels:
            declaration.add_channel(Channel(urgent=True, broadcast=True, type=currentAmount, name=advance_channel))

    # Functions
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
    declaration.add_function_call(generate_function_hadnle_standard_event)
    declaration.add_function_call(generate_function_handle_own_event)
    declaration.add_function_call(generate_function_update_true_global_log)
    declaration.add_function_call(generate_function_update_global_log)
    declaration.add_function_call(generate_function_update_log)
    #declaration.add_function_call(generate_function_handle_other_event)

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
    

    roles = []
    logs = []

    for jsonTransfer in jsonTransfers:
        role = Role(jsonTransfer.name, amount_names[jsonTransfer.name] + " id", jsonTransfer, loop_bound)
        roles.append(role)

        # Adding loopcounter to global decleration
        current_evetname_loopcounter = role.get_evetname_loopcounter()
        for eventname in current_evetname_loopcounter:
            declaration.add_variable(f"int {current_evetname_loopcounter[eventname]} = 0;")

        log = Log(jsonTransfer.name, amount_names[jsonTransfer.name] + " id", jsonTransfer,current_evetname_loopcounter, log_size)
        logs.append(log)

    final_xml += declaration.to_xml()

    for role in roles:
        final_xml += role.to_xml()

    for log in logs:
        final_xml += log.to_xml()
        
    

    system_instansiator_string = ""
    for name in name_amount_dict:
        system_instansiator_string += f"{name}, {name}_log, "
    system_instansiator_string = system_instansiator_string[:-2]

    # For each role put in name and log name
    final_xml += f"""<system>// Place template instantiations here.
// List one or more processes to be composed into a system.
system {system_instansiator_string};
</system>"""
    final_xml += "</nta>"

    return final_xml

    
    #print(final_xml)

def parseJsonFiles(paths_to_jsons: List[str]):
    jsonTransfers = []
    for path in paths_to_jsons:
        jsonTransfers.append(parse_JSON_file(path))

    return jsonTransfers

def wareHousedemo():
    jsonTransfers = []
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\Warehouse\\Door.json"))
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\Warehouse\\Forklift.json"))
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\Warehouse\\Transport.json"))

    name_amount_dict = {}
    for jsonTransfer in jsonTransfers:
        if (jsonTransfer.name == "Forklift"):
            name_amount_dict[jsonTransfer.name] = 2
        else:
            name_amount_dict[jsonTransfer.name] = 1

    loop_bound = 2
    currentModel = createModel(jsonTransfers, name_amount_dict, loop_bound)
    save_xml_to_file(currentModel, "warehouse_example6", "C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\Warehouse")

def plantRobotDemo():
    jsonTransfers = [] 
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\RobotPump\\Robot.json"))
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\RobotPump\\Pump.json"))

    name_amount_dict = {}
    for jsonTransfer in jsonTransfers:
        if (jsonTransfer.name == "Robot"):
            name_amount_dict[jsonTransfer.name] = 2
        else:
            name_amount_dict[jsonTransfer.name] = 1

    currentModel = createModel(jsonTransfers, name_amount_dict, standard_setting=True)
    save_xml_to_file(currentModel, "example_file", "C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\RobotPump")

def verifyta_example():
    plantRobotDemo()
    verifyta_path = "C:\\Program Files\\uppaal-5.0.0-win64\\bin\\verifyta"
    model_path = "C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\RobotPump\\example_file.xml"
    query_string = "C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\SwarmProtocolVerification\\tests\\integration\\RobotPump\\query_file.txt"
    # Define the command as a list of strings
    command = [verifyta_path,model_path , query_string]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Check if it was successful
    if result.returncode == 0:
        print("Success:", result.stdout)  # Print the standard output
    else:
        print("Error:", result.stderr)    # Print the standard error


if __name__ == "__main__":
    # Should just load all json files in a given folder.
    #verifyta_example()
    plantRobotDemo()
    #wareHousedemo()