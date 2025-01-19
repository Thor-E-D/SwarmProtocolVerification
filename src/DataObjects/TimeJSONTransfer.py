"""\
Python dataclass for the information stored in a json file with time information for
the UPPAAL model. To allow easy transfer.

"""
from abc import ABC
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TimeData(ABC):
    min_time: Optional[int] = None
    max_time: Optional[int] = None

@dataclass
class LogTimeData(TimeData):
    role_name: str = None

    def __eq__(self, other):
        if isinstance(other, LogTimeData):
            return self.role_name == other.role_name
        elif isinstance(other, str):
            return self.role_name == other
        return False

@dataclass
class EventTimeData(TimeData):
    event_name: str = None

    def __eq__(self, other):
        if isinstance(other, EventTimeData):
            return self.event_name == other.event_name
        elif isinstance(other, str):
            return self.event_name == other
        return False

@dataclass
class TimeJSONTransfer:
    log_time_data: Optional[List[LogTimeData]] = None
    event_time_data: Optional[List[EventTimeData]] = None