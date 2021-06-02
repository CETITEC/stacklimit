"""Test cases for methods and classes defined in patterns/x86.py file."""

import itertools
import re

import pytest

from stacklimit.patterns import x86

constants = [
    "$0x0",
    "$0x3f",
    "$0xffffffbf",
    "$0xffffffffffffffbf",
]

# Stack pointers
stack_pointers = ["esp", "rsp", "lsp"]

# General purpose 1 byte (integer) registers
reg1byte = [
    "".join(reg)
    for reg in itertools.chain(
        list(itertools.product("%", "abcd", "hl")),
        list(itertools.product("%", ["bp", "si", "di", "sp"], "l")),
        list(itertools.product("%", "r", [str(n) for n in range(8, 16)], "b")),
    )
]

# General purpose 2 byte (integer) registers
reg2bytes = [
    "".join(reg)
    for reg in itertools.chain(
        list(itertools.product("%", "abcd", "x")),
        list(itertools.product("%", ["bp", "si", "di", "sp"])),
        list(itertools.product("%", "r", [str(n) for n in range(8, 16)], "w")),
    )
]

# General purpose 4 byte (integer) registers
reg4bytes = [
    "".join(reg)
    for reg in itertools.chain(
        list(itertools.product("%", "e", "abcd", "x")),
        list(itertools.product("%", "e", ["bp", "si", "di", "sp"])),
        list(itertools.product("%", "r", [str(n) for n in range(8, 16)], "d")),
    )
]

# General purpose 8 byte (integer) registers
reg8bytes = [
    "".join(reg)
    for reg in itertools.chain(
        list(itertools.product("%", "r", "abcd", "x")),
        list(itertools.product("%", "r", ["bp", "si", "di", "sp"])),
        list(itertools.product("%", "r", [str(n) for n in range(8, 16)])),
    )
]

register_sizes = [
    (constants, 4),
    (reg1byte, 1),
    (reg2bytes, 2),
    (reg4bytes, 4),
    (reg8bytes, 8),
]


function_calls = [
    (
        "400734:       e8 b0 fe ff ff          callq  4005e9 <function_e>",
        0x4005E9,
        "function_e",
    ),
]

function_calls_negative = [
    "400804:   ff d0                   callq  *%rax",
]

stack_dynamic_op = [
    "4004aa:   48 83 ec 10             sub    %rax,%{}".format(stack_pointer)
    for stack_pointer in stack_pointers
]

stack_dynamic_op_negative = [
    "4004aa:   48 83 ec 10             sub    %rax,%rax",
]

function_pointer = [
    "400804:   ff d0                   callq  *%rax",
]

function_pointer_negative = [
    "400734:       e8 b0 fe ff ff          callq  4005e9 <function_e>",
]

# Return a list of the tuples (line, size) with line:
# > 4004c3:   55                      push(|l)  %reg
# and size depending on which kind of register %reg was used in the line.
# The registers are defined in
# * constants
# * reg1bytes
# * reg2bytes
# * reg4bytes
# * reg8bytes
stack_push_op = [
    n
    for registers, size in register_sizes
    for n in itertools.product(
        [
            "4004c3:   55                      {}   {}".format(instruction, register)
            for instruction in ["push", "pushl"]
            for register in registers
        ],
        [size],
    )
]

stack_push_op_negative = [
    "4004aa:   48 83 ec 10             sub    $0x10,%rsp",
    "4004c3:   55                      pushk  %esp",
    "4004c3:   55                      pushlk %esp",
]

stack_sub_op = [
    ("4004aa:   48 83 ec 10             sub    {},%rsp".format(constant), constant[1:])
    for constant in constants
]

stack_sub_op_negative = [
    "400734:   YY YY YY YY             sub     0xef,%rsp",
    "400764:   YY YY YY YY             add     0xff,%rsp",
]


@pytest.mark.parametrize("line, address, name", function_calls)
def test_x86_function_call(line, address, name):
    """Test x86.FunctionCall."""
    assert re.match(x86.FunctionCall, line)


@pytest.mark.parametrize("line", function_calls_negative)
def test_x86_function_call_with_negative_line(line):
    """Test x86.FunctionCall with lines without matches."""
    assert re.match(x86.FunctionCall, line) == None


@pytest.mark.parametrize("line", function_pointer)
def test_x86_function_pointer(line):
    """Test x86.FunctionPointer."""
    assert re.match(x86.FunctionPointer, line)


@pytest.mark.parametrize("line", function_pointer_negative)
def test_x86_function_pointer_with_negative_line(line):
    """Test x86.FunctionPointer with lines without matches."""
    assert re.match(x86.FunctionPointer, line) == None


@pytest.mark.parametrize("line", stack_dynamic_op)
def test_x86_stack_dynamic_op(line):
    """Test x86.StackDynamicOp."""
    assert re.match(x86.StackDynamicOp, line)


@pytest.mark.parametrize("line", stack_dynamic_op_negative)
def test_x86_stack_dynamic_op_with_negative_line(line):
    """Test x86.StackDynamicOp with lines without matches."""
    assert re.match(x86.StackDynamicOp, line) == None


@pytest.mark.parametrize("line, size", stack_push_op)
def test_x86_stack_push_op(line, size):
    """Test x86.StackPushOp."""
    assert re.match(x86.StackPushOp, line)


@pytest.mark.parametrize("line", stack_push_op_negative)
def test_x86_stack_push_op_with_negative_line(line):
    """Test x86.StackPushOp with lines without matches."""
    assert re.match(x86.StackPushOp, line) == None


@pytest.mark.parametrize("line, size", stack_sub_op)
def test_x86_stack_sub_op(line, size):
    """Test x86.StackSubOp."""
    assert re.match(x86.StackSubOp, line)


@pytest.mark.parametrize("line", stack_sub_op_negative)
def test_x86_stack_sub_op_with_negative_line(line):
    """Test x86.StackSubOp with lines without matches."""
    assert re.match(x86.StackSubOp, line) == None


@pytest.mark.parametrize("line, address, name", function_calls)
def test_x86_get_function_call(line, address, name):
    """Test x86.get_function_call()."""
    assert x86.get_function_call(line) == (address, name)


@pytest.mark.parametrize("line, size", stack_push_op)
def test_x86_get_stack_push_size(line, size):
    """Test x86.get_stack_push_size()."""
    assert x86.get_stack_push_size(line) == size


@pytest.mark.parametrize("line, size", stack_sub_op)
def test_x86_get_stack_sub_size(line, size):
    """Test x86.get_stack_sub_size()."""
    assert x86.get_stack_sub_size(line) == size
