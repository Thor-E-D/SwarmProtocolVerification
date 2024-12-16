from dataclasses import dataclass
from typing import Optional
import xml.etree.ElementTree as ET
from UppaalPart import UppaalPart
from enum import Enum

# Define an Enum
class LocationType(Enum):
    URGENT = 1
    COMMITTED = 2
    NEITHER = 3


@dataclass
class Location(UppaalPart):
    id: int
    x: Optional[int] = 0
    y: Optional[int] = 0
    name: Optional[str] = None
    locationType: LocationType = LocationType.NEITHER
    invariant: Optional[str] = None

    def __hash__(self):
        return hash(self.id)

    def to_xml(self) -> str:
        location_elem = ET.Element("location", attrib={"id": "id" + str(self.id), "x": f"{self.x}", "y": f"{self.y}"})

        if self.name:
            name_elem = ET.SubElement(location_elem, "name", attrib={"x": f"{self.x + 2}", "y": f"{self.y + 2}"})
            name_elem.text = self.name

        if self.locationType == LocationType.URGENT:
            ET.SubElement(location_elem, "urgent")
        elif self.locationType == LocationType.COMMITTED:
            ET.SubElement(location_elem, "committed")
        elif self.invariant != None:
            name_elem = ET.SubElement(location_elem, "label", attrib={"kind": "invariant", "x": f"{self.x + 5}", "y": f"{self.y - 28}"})
            name_elem.text = self.invariant

        return ET.tostring(location_elem, encoding="unicode", method="xml")
