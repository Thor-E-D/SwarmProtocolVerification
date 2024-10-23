from JSONParser import parse_JSON_file
from DataObjects.Declaration import Declaration
from DataObjects.JSONTransfer import JSONTransfer
from DataObjects.Channel import Channel
from typing import List, Dict
from Utils import Utils
from Functions import *
from Log import Log
from Role import Role

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

def createModel(jsonTransfers: List[JSONTransfer], name_amount_dict: Dict[str, int]):
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

    final_xml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.6//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd'>
<nta>"""

    declaration = Declaration()

    # Refactor these so they are instasiated based on the JSON files
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

    # Refactor these so they are instasiated based on the JSON files
    counter = 0
    for event_key in eventnames_dict:
        declaration.add_variable(f"const int {eventnames_dict[event_key]} = {counter};")
        counter += 1

    declaration.add_variable("""typedef struct {
    int eventID;
    int emitterID;
    int orderCount;
    int basedOnOrderCount;
    bool ignored;
} logEntryType;""")
    

    declaration.add_variable("int maxUpdatesSincePropagation = 1;")
    declaration.add_variable("const int logSize = 10;") #TODO this size has to depend on the size of model
    declaration.add_variable("int eventOrderCounter = 1;")
    declaration.add_variable("logEntryType tempLogEntry;")
    declaration.add_variable("logEntryType propagationLog[logSize];")

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
    declaration.add_function_call(generate_function_is_int_in_list)
    declaration.add_function_call(generate_function_add_int_to_list)
    declaration.add_function_call(generate_function_set_next_log_to_propagate)
    declaration.add_function_call(generate_function_get_order_count)
    declaration.add_function_call(generate_function_set_log_entry_for_update)
    declaration.add_function_call(generate_function_set_propagation_log)
    declaration.add_function_call(generate_function_update_log)
    declaration.add_function_call(generate_function_handle_own_event)
    declaration.add_function_call(generate_function_handle_other_event)

    name_basedOnEvents = {}
    for jsonTransfer in jsonTransfers:
        basedOnEvents = {}

        all_events = jsonTransfer.own_events.copy()
        all_events.extend(jsonTransfer.other_events)

        for current_event in jsonTransfer.own_events:
            if current_event.source == jsonTransfer.initial:
                continue
            
            for event in all_events:
                if event.target == current_event.source:
                    if eventnames_dict[current_event.event_name] in basedOnEvents:
                        basedOnEvents[eventnames_dict[current_event.event_name]].append(eventnames_dict[event.event_name])
                    else:
                        basedOnEvents[eventnames_dict[current_event.event_name]] = [eventnames_dict[event.event_name]]
    
        name_basedOnEvents[jsonTransfer.name] = basedOnEvents


    for name in name_amount_dict:
        declaration.add_function_call(generate_function_update_log_name, name,name_basedOnEvents[name])
    

    final_xml += declaration.to_xml()

    system_instansiator_string = ""
    for name in name_amount_dict:
        system_instansiator_string += f"{name}, {name}_log, "
    system_instansiator_string = system_instansiator_string[:-2]

    # Roles and logs
    for jsonTransfer in jsonTransfers:
        log = Log(jsonTransfer.name, amount_names[jsonTransfer.name] + " id", jsonTransfer)
        role = Role(jsonTransfer.name, amount_names[jsonTransfer.name] + " id", jsonTransfer)
        final_xml += log.to_xml()
        final_xml += role.to_xml()


    # For each role put in name and log name
    final_xml += f"""<system>// Place template instantiations here.
// List one or more processes to be composed into a system.
system {system_instansiator_string};
</system>"""
    final_xml += "</nta>"

    return final_xml

    
    #print(final_xml)


if __name__ == "__main__":
    # Should just load all json files in a given folder.
    jsonTransfers = [] 
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\Robot.json"))
    jsonTransfers.append(parse_JSON_file("C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis\\Pump.json"))

    name_amount_dict = {}
    for jsonTransfer in jsonTransfers:
        name_amount_dict[jsonTransfer.name] = 2

    currentModel = createModel(jsonTransfers, name_amount_dict)
    save_xml_to_file(currentModel, "example_file", "C:\\Users\\thore\\OneDrive\\Skrivebord\\MasterThesis")