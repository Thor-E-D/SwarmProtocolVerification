"""\
The settings nessesary to create a full model in UPPAAL
Every variable can be changed by the user through the CLI

"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from .TimeJSONTransfer import TimeJSONTransfer

# The different ways to delay propagation
class DelayType(Enum):
    NOTHING = 1
    EVENTS_EMITTED = 2
    EVENTS_SELF_EMITTED = 3

@dataclass
class ModelSettings:
    role_amount: Dict[str, int] # name of role to amount
    delay_type: Dict[str, DelayType] # name of role to delayType
    path_bound: int = 2
    branch_tracking: bool = True
    log_size: int = 20
    delay_amount: Optional[Dict[str, int]] = None
    time_json_transfer: Optional[TimeJSONTransfer] = None
    subsets: Optional[str] = None #TODO make this xD