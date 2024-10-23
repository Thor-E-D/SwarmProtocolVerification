from DataObjects.Location import Location

class Utils:
    _count = 0

    @staticmethod
    def get_next_id():
        Utils._count += 1
        return Utils._count
    
    @staticmethod
    def get_eventtype_UID(name: str):
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
