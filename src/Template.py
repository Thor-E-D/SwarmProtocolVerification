from abc import ABC
from DataObjects.Declaration import Declaration
from DataObjects.Transition import Transition
from DataObjects.Location import Location
from typing import List

class Template(ABC):
    def __init__(self, name: str, parameter: str, declaration: Declaration, locations: List[Location],startLocation: Location, transitions: List[Transition]):
        self.name = name
        self.parameter = parameter
        self.declaration = declaration
        self.locations = locations
        self.startLocation = startLocation
        self.transitions = transitions
    
    # Implemented method that converts the object to XML
    def to_xml(self) -> str:
        # Start of the XML template
        xml_output = f'<template>\n'
        xml_output += f'\t<name>{self.name}</name>\n'
        xml_output += f'\t<parameter>{self.parameter}</parameter>\n'
        xml_output += self.declaration.to_xml() + "\n"

        for loc in self.locations:
            xml_output += loc.to_xml() + "\n"

        xml_output += f'\t<init ref=\"id{self.startLocation.id}\"/>\n'

        for trans in self.transitions:
            xml_output += trans.to_xml()  + "\n"
        
        xml_output += '</template>'
        return xml_output
