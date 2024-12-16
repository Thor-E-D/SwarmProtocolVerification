from abc import ABC, abstractmethod

# Ensures UppaalParts have a method converting it to an xml representation, which is just a string for ease of use

class UppaalPart(ABC):

    @abstractmethod
    def to_xml(self) -> str:
        pass
