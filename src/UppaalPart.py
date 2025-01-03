"""\
Ensures UppaalParts have a method converting it to an xml representation, 
which is just a string for ease of use

"""

from abc import ABC, abstractmethod

class UppaalPart(ABC):

    @abstractmethod
    def to_xml(self) -> str:
        pass
