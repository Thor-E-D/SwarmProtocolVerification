"""\
The representation of a Declaration.
Split into three as variables, functions and channels.
Functions are kept as callable functions until needed.
Variables are simply represented as strings.

"""

from dataclasses import dataclass, field
from typing import Callable, List, Tuple

from .Channel import Channel
from UppaalPart import UppaalPart

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
        code = "<declaration>\n"

        if self.global_variables:
            code += "\n".join(self.global_variables) + "\n"

        for chan in self.channels:
            code += chan.to_xml() + "\n"

        for func, args in self.functions:
            code += func(*args) + "\n"

        code += "</declaration>"

        return code
