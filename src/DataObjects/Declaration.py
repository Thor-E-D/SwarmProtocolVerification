from dataclasses import dataclass, field
from typing import Callable, List, Tuple
from .Channel import Channel
from UppaalPart import UppaalPart

# Define the Declaration class with function call handling
@dataclass
class Declaration(UppaalPart):
    global_variables: List[str] = field(default_factory=list)
    channels: List[Channel] = field(default_factory=list)
    functions: List[Tuple[Callable, List]] = field(default_factory=list)

    def add_variable(self, var: str):
        self.global_variables.append(var)

    def add_channel(self, chan: Channel):
        self.channels.append(chan)

    def add_function_call(self, func: Callable, *args):
        self.functions.append((func, list(args)))

    def to_xml(self) -> str:
        # Start the code block with <declaration> tags
        code = "<declaration>\n"

        # Add global variables
        if self.global_variables:
            code += "\n".join(self.global_variables) + "\n"

        # Add channel declarations
        for chan in self.channels:
            code += chan.to_xml() + "\n"

        # Add function definitions
        for func, args in self.functions:
            code += func(*args) + "\n"

        # Close the <declaration> block
        code += "</declaration>"

        return code
