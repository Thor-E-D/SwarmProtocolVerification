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
    role_amount: Dict[str, int] # name of role to amount
    delay_type: Dict[str, DelayType] # name of role to delayType
    loop_bound: int = 2
    standard_setting: bool = False
    log_size: int = 20
    delay_amount: Optional[Dict[str, int]] = None
    time_json_transfer: Optional[TimeJSONTransfer] = None
    subsets: Optional[str] = None #TODO make this xD


def __str__(self):
        # Format dicts
        delay_type_str = ", ".join(f"{role}: {dtype.name}" for role, dtype in self.delay_type.items())
        delay_amount_str = ", ".join(f"{role}: {amount}" for role, amount in (self.delay_amount or {}).items())
        role_amount_str = ", ".join(f"{role}: {amount}" for role, amount in (self.role_amount or {}).items())
        
        return (
            f"ModelSettings(\n"
            f"  role_amount: {{{role_amount_str}}},\n"
            f"  delay_type: {{{delay_type_str}}},\n"
            f"  loop_bound: {self.loop_bound},\n"
            f"  standard_setting: {self.standard_setting},\n"
            f"  log_size: {self.log_size},\n"
            f"  delay_amount: {{{delay_amount_str}}},\n"
            f"  time_json_transfer: {self.time_json_transfer},\n"
            f"  subsets: {self.subsets}\n"
            f")"
        )