from dataclasses import dataclass, field
from typing import Callable, List, Tuple
from .Channel import Channel  # Import the Channel class from channel.py

# Define the Declaration class with function call handling
@dataclass
class Declaration:
    global_variables: List[str] = field(default_factory=list)
    channels: List[Channel] = field(default_factory=list)
    functions: List[Tuple[Callable, List]] = field(default_factory=list)

    def add_variable(self, var: str):
        """Add a global variable declaration."""
        self.global_variables.append(var)

    def add_channel(self, chan: Channel):
        """Add a channel declaration."""
        self.channels.append(chan)

    def add_function_call(self, func: Callable, *args):
        """Add a function and its arguments to be called later."""
        self.functions.append((func, list(args)))

    def to_xml(self) -> str:
        """Generate the full code for the declaration including variables, channels, and functions."""
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
