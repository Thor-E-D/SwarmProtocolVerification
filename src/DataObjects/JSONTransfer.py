from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class EventData:
    event_name: str
    source: str
    target: str

@dataclass
class JSONTransfer:
    name: str
    initial: str
    subscriptions: List[str]
    own_events: List[EventData] = field(default_factory=list)
    other_events: List[EventData] = field(default_factory=list)
    do_update_channel_name: Optional[str] = None
    reset_channel_name: Optional[str] = None
    advance_channel_names: Optional[Dict[str, str]] = None
    log_id_start: Optional[int] = None

    
    def __str__(self):
        own_event_str = "\n".join([f"Own Event - {event.source} -> {event.target}: {event.event_name}" for event in self.own_events])
        other_event_str = "\n".join([f"Other Event - {event.source} -> {event.target}: {event.event_name}" for event in self.other_events])
        
        return (f"Initial State: {self.initial}\n"
                f"Subscriptions: {self.subscriptions}\n\n"
                f"Own Events:\n{own_event_str}\n\n"
                f"Other Events:\n{other_event_str}")
