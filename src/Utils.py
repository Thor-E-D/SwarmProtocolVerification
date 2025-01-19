"""\
Holds static utility functions used across the project

"""

from DataObjects.Location import Location
from typing import List, Any

class Utils:
    _count = 0
    _loopcount = 0

    @staticmethod
    def get_next_id() -> int:
        Utils._count += 1
        return Utils._count
    
    @staticmethod
    def get_next_loopcount() -> str:
        Utils._loopcount += 1
        return f"loop_counter{Utils._loopcount}"
    
    @staticmethod
    def get_eventtype_UID(name: str) -> str:
        return name + "_ID"
    
    @staticmethod
    def find_midpoint(l1: Location, l2: Location) -> tuple:
        x1 = l1.x
        y1 = l1.y
        x2 = l2.x
        y2 = l2.y
        
        midpoint_x = (x1 + x2) // 2
        midpoint_y = (y1 + y2) // 2
        
        return (midpoint_x, midpoint_y)
    
    @staticmethod
    def python_list_to_uppaal_list(l1: List[Any]) -> str:
        return str(l1).replace("[", "{").replace("]","}")
    
    @staticmethod
    def remove_last_two_chars(s: str) -> str:
        return s[:-2] if len(s) >= 2 else s

