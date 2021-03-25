"""Test cases for methods and classes defined in stacklimit.py file."""

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
def test_init_of_message_type(prefix, color):
    message = MessageType(prefix, color)
    assert message.prefix == prefix
    assert message.color == color
