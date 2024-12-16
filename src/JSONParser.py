import json
from pathlib import Path
from DataObjects.JSONTransfer import JSONTransfer, EventData
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class LogTimeData:
    role_name: str
    min_time: Optional[int] = None
    max_time: Optional[int] = None

    def __eq__(self, other):
        if isinstance(other, LogTimeData):
            return self.role_name == other.role_name
        elif isinstance(other, str):
            return self.role_name == other
        return False

@dataclass
class EventTimeData:
    event_name: str
    min_time: Optional[int] = None
    max_time: Optional[int] = None

    def __eq__(self, other):
        if isinstance(other, EventTimeData):
            return self.event_name == other.event_name
        elif isinstance(other, str):  # Allow comparison directly with a string (event_name)
            return self.event_name == other
        return False

@dataclass
class TimeJSONTransfer:
    log_time_data: Optional[List[LogTimeData]] = None
    event_time_data: Optional[List[EventTimeData]] = None


def parse_JSON_file(json_file: str) -> JSONTransfer:
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    initial_state = data['initial']
    subscriptions = data['subscriptions']
    
    own_event_names = []
    own_events = []
    other_events = []
    
    for transition in data['transitions']:
        source = transition.get('source')
        target = transition.get('target')
        label = transition.get('label', {})
        tag = label.get('tag')
        
        if tag == 'Execute':
            log_types = label.get('logType', [])
            for log_type in log_types:
                own_event_names.append(log_type)
        
        elif tag == 'Input':
            event_type = label.get('eventType')
            if any(event_type == event_name for event_name in own_event_names):  # Own event
                own_events.append(EventData(event_name=event_type, source=source, target=target))

            elif not any(event.event_name == event_type for event in own_events):
                other_events.append(EventData(event_name=event_type, source=source, target=target))
    
    return JSONTransfer(
        name=Path(json_file).stem,
        initial=initial_state,
        subscriptions=subscriptions,
        own_events=own_events,
        other_events=other_events
    )


def parse_time_JSON(json_file: str) -> List[TimeJSONTransfer]:
    event_time_data = []
    log_time_data = []
    with open(json_file, 'r') as file:
        data = json.load(file)
        event_time_data = [
            EventTimeData(
                event_name=event_data["logType"],
                min_time=event_data.get("min_time"),
                max_time=event_data.get("max_time")
            )
            for event_data in data.get("events", [])
        ]
        log_time_data = [
            LogTimeData(
                role_name=event_data["role_name"],
                min_time=event_data.get("min_time"),
                max_time=event_data.get("max_time")
            )
            for event_data in data.get("logs", [])
        ]

    time_json_transger = TimeJSONTransfer(log_time_data=log_time_data, event_time_data=event_time_data)
    return time_json_transger
    