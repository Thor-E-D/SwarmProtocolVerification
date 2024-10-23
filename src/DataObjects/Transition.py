from dataclasses import dataclass, field
from typing import Optional
from .Location import Location
from Utils import Utils
import xml.etree.ElementTree as ET

@dataclass
class Transition:
    id: int
    source: Location
    target: Location
    guard: Optional[str] = None
    synchronisation: Optional[str] = None
    assignment: Optional[str] = None

    def to_xml(self) -> str:
        transition_elem = ET.Element("transition", attrib={"id": "id" + str(self.id)})
        
        ET.SubElement(transition_elem, "source", attrib={"ref": "id" +  str(self.source.id)})
        ET.SubElement(transition_elem, "target", attrib={"ref": "id" +  str(self.target.id)})

        x, y = Utils.find_midpoint(self.source, self.target)

        if self.guard:
            guard_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "guard", "x": f"{x}", "y": f"{y}"})
            guard_elem.text = self.guard

        if self.synchronisation:
            sync_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "synchronisation", "x": f"{x}", "y": f"{y}"})
            sync_elem.text = self.synchronisation

        if self.assignment:
            assign_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "assignment", "x": f"{x}", "y": f"{y}"})
            assign_elem.text = self.assignment
        
        return ET.tostring(transition_elem, encoding="unicode", method="xml")