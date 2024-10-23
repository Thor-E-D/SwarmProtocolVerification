import json
from pathlib import Path
from DataObjects.JSONTransfer import JSONTransfer, EventData

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
