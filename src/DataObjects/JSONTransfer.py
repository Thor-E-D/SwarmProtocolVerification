"""\
Holds all information nessesary for constructing templates.
Holds all information from projections of roles and
additional information used in the creation of both role templates and log templates.

"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

# 

@dataclass
class EventData:
    event_name: str
    source: str
    target: str

    def __hash__(self):
        return hash((self.event_name, self.source, self.target))
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.event_name == other
        if not isinstance(other, EventData):
            return False
        return (self.event_name == other.event_name and 
                self.source == other.source and 
                self.target == other.target)

@dataclass
class JSONTransfer:
    name: str
    initial: str
    subscriptions: List[str]
    own_events: List[EventData] = field(default_factory=list)
    other_events: List[EventData] = field(default_factory=list)

    # Channels names to ensure no discreptancy in names
    do_update_channel_name: Optional[str] = None
    reset_channel_name: Optional[str] = None
    advance_channel_names: Optional[Dict[str, str]] = None

    # Additional information need locally in templates
    log_id_start: Optional[str] = None
    total_amount_of_events: Optional[int] = None
    initial_pointer: Optional[int] = 0
    flow_list: Optional[List[List[int]]] = None
    loop_events: Optional[List[str]] = None
