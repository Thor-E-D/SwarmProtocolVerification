from typing import Dict, Optional
from dataclasses import dataclass
from .TimeJSONTransfer import TimeJSONTransfer
from enum import Enum

# Define an Enum
class DelayType(Enum):
    NOTHING = 1
    EVENTS_EMITTED = 2
    EVENTS_SELF_EMITTED = 3

@dataclass
class ModelSettings:
    delay_type: Dict[str, DelayType] # name of model to delayType
    loop_bound: int = 2
    standard_setting: bool = False
    log_size: int = 20
    delay_amount: Optional[Dict[str, int]] = None
    time_json_transfer: Optional[TimeJSONTransfer] = None
    subsets: Optional[str] = None #TODO make this xD

