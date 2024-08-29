import argparse
import textwrap
from dataclasses import dataclass
from typing import Any, Type


@dataclass
class ArgInfo:
    """Information for a command-line argument."""

    help: str
    type: Type | None = None
    default: Any = None
    action: str | None = None
    nargs: str | None = None
    dest: str | None = None
    required: bool = False


class ArgumentsBase:
    @classmethod
    def as_dict(cls) -> dict[str, ArgInfo]:
        return {name: value for name, value in cls.__dict__.items() if isinstance(value, ArgInfo)}


class CustomHelpFormatter(argparse.HelpFormatter):
    """
    Format a help message for argparse. It allows for customizing the column width of the arguments
    and help text. You would use this class by passing it as the formatter_class argument to the
    ArgumentParser constructor, like the below example.

        parser = argparse.ArgumentParser(description=__doc__, formatter_class=lambda prog: CustomHelpFormatter(prog, max_help_position=24, width=100))

    But to make your life easier, just use the ArgParser class below, which uses this formatter by
    default and allows you to specify the column widths as arguments.
    """

    def __init__(self, prog: str, max_help_position: int = 24, width: int = 120) -> None:
        super().__init__(prog, max_help_position=max_help_position, width=width)
        self.custom_max_help_position = max_help_position

    def _split_lines(self, text: str, width: int) -> list[str]:
        return textwrap.wrap(text, width)

    def _format_action(self, action: argparse.Action) -> str:
        parts = super()._format_action(action)
        if action.help:
            help_position = parts.find(action.help)
            space_to_insert = max(self.custom_max_help_position - help_position, 0)
            parts = parts[:help_position] + (" " * space_to_insert) + parts[help_position:]
        return parts


class ArgParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser that uses the CustomHelpFormatter by default and makes it easier to
    specify the column widths. After importing it, just use this instead of argparse.ArgumentParser,
    like the example below.

        parser = ArgParser(description=__doc__, arg_width=24, max_width=120)

    The arg_width and max_width arguments are optional and default to 24 and 120, respectively. They
    map to max_help_position and width in CustomHelpFormatter.
    """

    def __init__(self, *args, **kwargs):
        self.arg_width = kwargs.pop("arg_width", 24)
        self.max_width = kwargs.pop("max_width", 120)
        super().__init__(
            *args,
            **kwargs,
            formatter_class=lambda prog: CustomHelpFormatter(
                prog,
                max_help_position=self.arg_width,
                width=self.max_width,
            ),
        )

    def add_argument_from_info(self, name: str, arg_info: ArgInfo) -> None:
        """Add an argument to the parser based on ArgInfo."""
        kwargs: dict[str, Any] = {"help": arg_info.help}

        if arg_info.action in ["store_true", "store_false"]:
            kwargs["action"] = arg_info.action
        else:
            if arg_info.type is not None:
                kwargs["type"] = arg_info.type
            if arg_info.default is not None:
                kwargs["default"] = arg_info.default
            if arg_info.action:
                kwargs["action"] = arg_info.action
            if arg_info.nargs:
                kwargs["nargs"] = arg_info.nargs

        if arg_info.dest:
            kwargs["dest"] = arg_info.dest
        if arg_info.required:
            kwargs["required"] = arg_info.required

        if name == "file":
            self.add_argument(name, **kwargs)
        elif name in {"creation", "modification"}:
            self.add_argument(f"-{name[0]}", f"--{name}", **kwargs)
        else:
            self.add_argument(f"--{name.replace('_', '-')}", **kwargs)

    def add_args_from_class(self, arg_class: Type[ArgumentsBase]) -> None:
        """Automatically add arguments to the parser based on a class of ArgInfo instances."""
        for field_name, arg_info in arg_class.as_dict().items():
            self.add_argument_from_info(field_name, arg_info)
