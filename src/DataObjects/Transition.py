"""\
The representation of a transition.
guards, synchronisation and assignments are all represented with strings.
Nails are points along the transitions.

"""

from dataclasses import dataclass, field
from typing import Optional, List

import xml.etree.ElementTree as ET

from Utils import Utils
from UppaalPart import UppaalPart
from .Location import Location

@dataclass
class Transition(UppaalPart):
    id: int
    source: Location
    target: Location
    guard: Optional[str] = None
    synchronisation: Optional[str] = None
    assignment: Optional[str] = None
    nails: List[tuple] = field(default_factory=list)
    
    def __eq__(self, other):
        if not isinstance(other, Transition):
            return False
        return self.id == other.id

    def to_xml(self) -> str:
        transition_elem = ET.Element("transition", attrib={"id": "id" + str(self.id)})
        
        ET.SubElement(transition_elem, "source", attrib={"ref": "id" +  str(self.source.id)})
        ET.SubElement(transition_elem, "target", attrib={"ref": "id" +  str(self.target.id)})

        x, y = Utils.find_midpoint(self.source, self.target)
        
        if (self.nails is not None and self.nails != []):
            x, y = 0,0
            for nail in self.nails:
                x += nail[0]
                y += nail[1]
            x //= len(self.nails)
            y //= len(self.nails)

        if self.guard:
            guard_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "guard", "x": f"{x}", "y": f"{y}"})
            guard_elem.text = self.guard

        if self.synchronisation:
            sync_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "synchronisation", "x": f"{x}", "y": f"{y - 15}"})
            sync_elem.text = self.synchronisation

        if self.assignment:
            assign_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "assignment", "x": f"{x}", "y": f"{y + -30}"})
            assign_elem.text = self.assignment

        for nail in self.nails:
            ET.SubElement(transition_elem, "nail", {"x": str(nail[0]), "y": str(nail[1])})
        
        return ET.tostring(transition_elem, encoding="unicode", method="xml")