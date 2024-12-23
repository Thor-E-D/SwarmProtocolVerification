from dataclasses import dataclass
import xml.etree.ElementTree as ET
from UppaalPart import UppaalPart
from Log import Log
from Role import Role
from .Declaration import Declaration
from typing import List

@dataclass
class Model(UppaalPart):
    declaration: Declaration
    roles: List[Role]
    logs: List[Log]


    def to_xml(self) -> str:
        final_xml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.6//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd'>
<nta>"""

        final_xml += self.declaration.to_xml()

        for role in self.roles:
            final_xml += role.to_xml()

        for log in self.logs:
            final_xml += log.to_xml()

        system_instansiator_string = ""
        for role in self.roles:
            system_instansiator_string += f"{role.name}, {role.name}_log, "
        system_instansiator_string = system_instansiator_string[:-2]

        # For each role put in name and log name
        final_xml += f"""<system>// Place template instantiations here.
    // List one or more processes to be composed into a system.
    system {system_instansiator_string};
    </system>"""
        final_xml += "</nta>"

        return final_xml


