import json
from typing import Set, List

from DataObjects.JSONTransfer import JSONTransfer, EventData
from JSONParser import build_graph_internal, parse_protocol_JSON_file, parse_projection_JSON_file
from Utils import Utils

class QueryGenerator:
    protocol_data: JSONTransfer
    projection_data: List[JSONTransfer]

    def __init__(self, protocol_file_path: str, projection_json_files: Set[str]):

        try:
            json_transfers = []
            global_json_transfer = None
            if len(projection_json_files) == 0:
                global_json_transfer, json_transfers = parse_protocol_JSON_file(protocol_file_path)
            else:
                global_json_transfer, auto_json_transfers = parse_protocol_JSON_file(protocol_file_path)

                name_list = []
                for auto_json_transfer in auto_json_transfers:
                    name_list.append(auto_json_transfer.name)

                for projection_json_file in projection_json_files:
                    current_json_transfer = parse_projection_JSON_file(projection_json_file)
                    if current_json_transfer.name in name_list:
                        name_list.remove(current_json_transfer.name)
                        json_transfers.append(current_json_transfer)

                if len(name_list) != 0:
                    for auto_json_transfer in auto_json_transfers:
                        if auto_json_transfer.name in name_list:
                            json_transfers.append(auto_json_transfer)
        except Exception as e:
            raise e
        
        self.protocol_data = global_json_transfer
        self.projection_data = json_transfers

    def generate_end_state_query(self) -> str:
        graph_data = {}
        for projection_transfer in self.projection_data:
            graph_data[projection_transfer.name] = projection_transfer.own_events

        graph = build_graph_internal(graph_data)

        # Find edges with outdegree 0
        locations = set()
        locations_pure = set()
        for edge in graph.edges:
            current_target = edge.target
            found_end = True
            for edge_inner in graph.edges:
                if current_target == edge_inner.source:
                    found_end = False
                    break
            if found_end:
                locations_pure.add(current_target)
                if current_target[0].isdigit():
                    locations.add("l" + current_target)
                else:
                    locations.add(current_target)

        index = 'i'
        map_role_index = {}

        for role in graph.get_role_names():
            map_role_index[role] = index
            index = chr(ord(index) + 1)

        deadlock_query = "A[] "
        for role in map_role_index:
            deadlock_query += f"forall({map_role_index[role]}: {role}_t) "

        deadlock_query += "(deadlock and globalLog[logSize - 1].orderCount == 0) imply "

        role_end_state_dict = {}
        for role in map_role_index:
            role_end_state_dict[role] = set()

        for jsonTransfer in self.projection_data:
            all_events = jsonTransfer.own_events.copy()
            all_events.extend(jsonTransfer.other_events)
            for event in all_events:
                loc_is_end = None
                if event.target in locations_pure:
                    loc_is_end = event.target
                elif event.source in locations_pure:
                    loc_is_end = event.source

                if loc_is_end != None and current_target[0].isdigit():
                    role_end_state_dict[jsonTransfer.name].add("l" +event.target)
                elif loc_is_end != None:
                    role_end_state_dict[jsonTransfer.name].add(event.target)

        for role in map_role_index:
            current_index = map_role_index[role]
            current_role_addition = "("
            for location in role_end_state_dict[role]:
                current_role_addition += f"{role}({current_index}).{location} or "
            current_role_addition = current_role_addition[:-4] + ")"
            deadlock_query += current_role_addition + " and "

        return deadlock_query[:-5]
    
    def generate_overflow_query(self) -> str:
        role = self.projection_data[0].name
        return (f"A[] not {role}_log(0).overflow")
    
    def generate_sizebound_query(self) -> str:
        return "sup: globalLogIndex"
    
    def generate_timebound_queries(self) -> str:
        role_queries_dict = {}
        for projection_json_transfer in self.projection_data:
            role_queries_dict[projection_json_transfer.name] = []
            all_events = projection_json_transfer.own_events.copy()
            all_events.extend(projection_json_transfer.other_events)

            locations = set()
            for event in all_events:
                locations.add(event.source)
                locations.add(event.target)
            
            for location in sorted(locations):
                # bounds{R(0).l4}: globalTime
                current_query = f"bounds{{{projection_json_transfer.name}(0).{location}}}: globalTime"
                role_queries_dict[projection_json_transfer.name].append(current_query)
        
        return role_queries_dict
    
def generate_log_query(log: List[str], valid_only: bool) -> str:
    log_to_use = "globalLog"
    if valid_only:
        log_to_use = "trueGlobalLog"

    counter = 0
    result_query = "E<> "
    for logEntry in log:
        result_query += f"{log_to_use}[{counter}].eventID == {Utils.get_eventtype_UID(logEntry)}"
        counter += 1
        if counter == len(log):
            result_query += f" and {log_to_use}[{counter-1}].orderCount != 0"
        else:
            result_query += " and "
    
    return result_query
            
