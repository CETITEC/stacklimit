"""Test cases for methods and classes defined in patterns/base.py file."""

import re

import pytest

from stacklimit.patterns import Pattern

file_formats = [
    "filename:      file format elf64-x86-64",
    "tests/dep-aarch64_O1:     file format elf64-little",
]

file_formats_negative = [
    "filename:      fil format elf64-x86-64",
]

sections = [
    # fmt: off
    ("Disassembly of section main:",                  "main"),
    ("Disassembly of section .plt:",                  ".plt"),
    ("Disassembly of section __libc_start_main@plt:", "__libc_start_main@plt"),
    # fmt: on
]

sections_negative = [
    "Disassembly of section main",
    "Disassembly of main:",
]

functions = [
    # fmt: off
    ("000000000040076d <main>:",                  0x40076d, "main"),
    ("0000000000400370 <.plt>:",                  0x400370, ".plt"),
    ("0000000000400390 <__libc_start_main@plt>:", 0x400390, "__libc_start_main@plt"),
    # fmt: on
]

functions_negative = [
    "000000000040076d <main>",
    "000000000040076d main",
    "000000000040076d",
    "main",
]


@pytest.mark.parametrize("line", file_formats)
def test_pattern_file_format(line):
    """Test Pattern.FileFormat."""
    assert re.match(Pattern.FileFormat, line)


@pytest.mark.parametrize("line", file_formats_negative)
def test_pattern_file_format_with_negative_line(line):
    """Test Pattern.FileFormat with lines without matches."""
    assert re.match(Pattern.FileFormat, line) == None


@pytest.mark.parametrize("line, section", sections)
def test_pattern_section(line, section):
    """Test Pattern.Section."""
    assert re.match(Pattern.Section, line)


@pytest.mark.parametrize("line", sections_negative)
def test_pattern_section_with_negative_line(line):
    """Test Pattern.Section with lines without matches."""
    assert re.match(Pattern.Section, line) == None


@pytest.mark.parametrize("line, address, name", functions)
def test_pattern_function(line, address, name):
    """Test Pattern.Function."""
    assert re.match(Pattern.Function, line)


@pytest.mark.parametrize("line", functions_negative)
def test_pattern_function_with_negative_line(line):
    """Test Pattern.Function with lines without matches."""
    assert re.match(Pattern.Function, line) == None


@pytest.mark.parametrize(
    "args, result",
    [
        # fmt: off
        (["inst"],                         ".*\s+inst"),
        (["inst", "reg1"],                 ".*\s+inst\s+reg1"),
        (["inst", "reg1", "reg2"],         ".*\s+inst\s+reg1,\s*reg2"),
        (["inst", "reg1", "reg2", "reg3"], ".*\s+inst\s+reg1,\s*reg2,\s*reg3"),
        # fmt: on
    ],
)
def test_pattern__operation(args, result):
    """Test Pattern._operation()."""
    assert Pattern._operation(*args) == result


@pytest.mark.parametrize("line, address, name", functions)
def test_pattern_get_function(line, address, name):
    """Test Pattern.get_function()."""
    assert Pattern.get_function(line) == (address, name)


@pytest.mark.parametrize("line, section", sections)
def test_pattern_get_section(line, section):
    """Test Pattern.get_section()."""
    assert Pattern.get_section(line) == section


def test_pattern_get_function_call():
    """Test Pattern.get_function_call()."""
    with pytest.raises(NotImplementedError):
        Pattern.get_function_call(None)


def test_pattern_get_stack_push_size():
    """Test Pattern.get_stack_push_size()."""
    with pytest.raises(NotImplementedError):
        Pattern.get_stack_push_size(None)


def test_pattern_get_stack_sub_size():
    """Test Pattern.get_stack_sub_size()."""
    with pytest.raises(NotImplementedError):
        Pattern.get_stack_sub_size(None)
