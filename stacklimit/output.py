# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Collection of output utilities."""


class Color:
    """ANSI color codes."""

    BLUE = "\033[94m"
    CYAN = "\033[96m"
    DARK = "\033[90m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    PURPLE = "\033[95m"
    YELLOW = "\033[93m"
    END = "\033[0m"
    BOLD = "\033[1m"


class MessageType:
    """Definition of the shape of a message.

    Attributes:
        color (str):  the color of the message prefix
        prefix (str): the prefix of the message
    """

    color = None
    prefix = None

    def __init__(self, prefix=None, color=None):
        """Create the object.

        Args:
            prefix (str, optional):  the prefix of the message. Defaults to None.
            color (Color, optional): the color of the message prefix. Defaults to None.
        """
        self.color = color
        self.prefix = prefix


class Message:
    """Line format for different message types."""

    DEBUG = MessageType("Debug: ", Color.YELLOW)
    ERROR = MessageType("Error: ", Color.RED)
    INFO = MessageType()
    WARN = MessageType("Warning: ", Color.PURPLE)
