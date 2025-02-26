"""\
The representation of a channel.
Can express the same as a channel in UPPAAL.

"""

from dataclasses import dataclass
from typing import Optional

from UppaalPart import UppaalPart

@dataclass
class Channel(UppaalPart):
    name: str
    urgent: bool = False
    broadcast: bool = False
    type: Optional[str] = None # Array channel size

    def to_xml(self) -> str:
        declaration = ""
        if self.urgent:
            declaration += "urgent "
        if self.broadcast:
            declaration += "broadcast "

        declaration += f"chan {self.name}"

        # If it's an array channel
        if self.type:
            declaration += f"[{self.type}]"

        declaration += ";"

        return declaration
