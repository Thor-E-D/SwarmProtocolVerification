from typing import List, Optional
from dataclasses import dataclass

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