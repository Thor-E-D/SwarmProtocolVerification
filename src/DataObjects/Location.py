from dataclasses import dataclass
from typing import Optional
import xml.etree.ElementTree as ET

@dataclass
class Location:
    id: int
    x: Optional[int] = 0
    y: Optional[int] = 0
    name: Optional[str] = None
    urgent: bool = False
    committed: bool = False

    def __hash__(self):
        return hash(self.id)

    def to_xml(self) -> str:
        location_elem = ET.Element("location", attrib={"id": "id" + str(self.id), "x": f"{self.x}", "y": f"{self.y}"})

        if self.name:
            name_elem = ET.SubElement(location_elem, "name", attrib={"x": f"{self.x + 2}", "y": f"{self.y + 2}"})
            name_elem.text = self.name

        if self.urgent:
            ET.SubElement(location_elem, "urgent")
        elif self.committed:
            ET.SubElement(location_elem, "committed")

        return ET.tostring(location_elem, encoding="unicode", method="xml")
