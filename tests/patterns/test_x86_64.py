"""Test cases for methods and classes defined in patterns/x86_64.py file."""

import itertools
import re

import pytest

from stacklimit.patterns import x86_64

constants = [
    "$0x0",
    "$0x3f",
    "$0xffffffbf",
    "$0xffffffffffffffbf",
]

function_calls = [
    ("400734:       e8 b0 fe ff ff          call   4005e9 <function_e>",),
    ("400734:       e8 b0 fe ff ff          callq  4005e9 <function_e>",),
]


# Return a list of the tuples (line, size) with line:
# > 4004c3:   55                      push(|l)  $const
# and size depending on which kind of constant $const was used in the line.
# Only constants are tested. Registers are already tested in test_x86.py.
stack_push_op = [
    "4004c3:   55                      {}   {}".format(instruction, constant)
    for instruction in ["push", "pushq"]
    for constant in constants
]

stack_push_op_negative = [
    "4004aa:   48 83 ec 10             sub    $0x10,%rsp",
    "4004c3:   55                      pushk  %esp",
    "4004c3:   55                      pushlk %esp",
]


@pytest.mark.parametrize("line", stack_push_op)
def test_x86_64_stack_push_op(line):
    """Test x86_64.StackPushOp."""
    assert re.match(x86_64.StackPushOp, line)


@pytest.mark.parametrize("line", stack_push_op_negative)
def test_x86_64_stack_push_op_with_negative_line(line):
    """Test x86_64.StackPushOp with lines without matches."""
    assert re.match(x86_64.StackPushOp, line) == None


@pytest.mark.parametrize("line", function_calls)
def test_x86_get_stack_call_size(line):
    """Test x86.get_stack_call_size()."""
    assert x86_64.get_stack_call_size(line) == 8


# Skipped: got empty parameter set ['line', 'size'], function test_x86_64_get_stack_push_size at /home/mlu/dev/stacklimit/tests/patterns/test_x86_64.py:49pytest(./tests/patterns/test_x86_64.py::test_x86_64_get_stack_push_size[line0-size0])
@pytest.mark.parametrize("line", stack_push_op)
def test_x86_64_get_stack_push_size(line):
    """Test x86_64.get_stack_push_size()."""
    assert x86_64.get_stack_push_size(line) == 8
