"""Test cases for methods and classes defined in output.py file."""

import itertools

import pytest

from stacklimit.output import Color, MessageType


@pytest.mark.parametrize(
    "prefix, color",
    itertools.chain(
        itertools.product(
            [None, "prefix", "test", ""],
            [None, Color.YELLOW, Color.RED, Color.BOLD],
        )
    ),
)
def test_message_type__init__(prefix, color):
    """Test MessageType.__init__()."""
    message = MessageType(prefix, color)
    assert message.prefix == prefix
    assert message.color == color
