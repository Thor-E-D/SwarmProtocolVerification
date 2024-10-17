from dataclasses import dataclass
from typing import Optional
import xml.etree.ElementTree as ET

@dataclass
class Location:
    id: int
    name: Optional[str] = None
    urgent: bool = False
    committed: bool = False

    def to_xml(self) -> str:
        location_elem = ET.Element("location", attrib={"id": "id" + str(self.id), "x": "0", "y": "0"})

        if self.name:
            name_elem = ET.SubElement(location_elem, "name", attrib={"x": "0", "y": "0"})
            name_elem.text = self.name

        if self.urgent:
            ET.SubElement(location_elem, "urgent")
        elif self.committed:
            ET.SubElement(location_elem, "committed")

        return ET.tostring(location_elem, encoding="unicode", method="xml")
