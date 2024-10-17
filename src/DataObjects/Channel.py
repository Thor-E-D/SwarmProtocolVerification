from dataclasses import dataclass
from typing import Optional

@dataclass
class Channel:
    name: str
    urgent: bool = False
    broadcast: bool = False
    type: Optional[str] = None

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
