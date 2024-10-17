from dataclasses import dataclass, field
from typing import Optional
import xml.etree.ElementTree as ET

@dataclass
class Transition:
    id: int
    source: int
    target: int
    guard: Optional[str] = None
    synchronisation: Optional[str] = None
    assignment: Optional[str] = None

    def to_xml(self) -> str:
        transition_elem = ET.Element("transition", attrib={"id": "id" + str(self.id)})
        
        ET.SubElement(transition_elem, "source", attrib={"ref": "id" +  str(self.source)})
        ET.SubElement(transition_elem, "target", attrib={"ref": "id" +  str(self.target)})

        if self.guard:
            guard_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "guard", "x": "-544", "y": "178"})
            guard_elem.text = self.guard

        if self.synchronisation:
            sync_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "synchronisation", "x": "-544", "y": "212"})
            sync_elem.text = self.synchronisation

        if self.assignment:
            assign_elem = ET.SubElement(transition_elem, "label", attrib={"kind": "assignment", "x": "-535", "y": "161"})
            assign_elem.text = self.assignment
        
        return ET.tostring(transition_elem, encoding="unicode", method="xml")