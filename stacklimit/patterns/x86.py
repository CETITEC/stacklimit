#!/bin/python3
"""Patterns for the x86 32bit and 64bit architecture."""

import re

from .base import Pattern


class x86(Pattern):
    """Contain the x86 instruction set.

    Both 32 bit and 64 bit registers and instruction sets are covered.

    Instructions which depends on the architecture and cannot be determine on the
    register name or operation are splitted into x86 (this class) and x86_64.
    """

    arch = ["x86"]

    # Stack pointer
    sp = "(e|r|l|)sp"

    # General purpose 1 byte (integer) registers
    reg1byte = (
        # fmt: off
          "(" + "(a|b|c|d)(h|l)"
        + "|" + "(bp|si|di|sp)l"
        + "|" + "r(8|9|10|11|12|13|14|15)b"
        + ")"
        # fmt: on
    )

    # General purpose 2 byte (integer) registers
    reg2bytes = (
        # fmt: off
          "(" + "(a|b|c|d)x"
        + "|" + "bp|si|di|sp"
        + "|" + "r(8|9|10|11|12|13|14|15)w"
        + ")"
        # fmt: on
    )

    # General purpose 4 byte (integer) registers
    reg4bytes = (
        # fmt: off
          "(" + "e(a|b|c|d)x"
        + "|" + "e(bp|si|di|sp)"
        + "|" + "r(8|9|10|11|12|13|14|15)d"
        + ")"
        # fmt: on
    )

    # General purpose 8 byte (integer) registers
    reg8bytes = (
        # fmt: off
          "(" + "r(a|b|c|d)x"
        + "|" + "r(bp|si|di|sp)"
        + "|" + "r(8|9|10|11|12|13|14|15)"
        + ")"
        # fmt: on
    )

    #   400734:       e8 b0 fe ff ff          callq  4005e9 <function_e>
    FunctionCall = Pattern._operation("callq", "[0-9a-f]+ \<.*\>$")

    #   400804:   ff d0                   callq  *%rax
    FunctionPointer = Pattern._operation("callq", ".*%.*$")

    #   XXXXXX:   YY YY YY YY             add     0xff,%rsp
    #   XXXXXX:   YY YY YY YY             sub     0xef,%rsp
    # TODO:
    # * Only track stack decrements. This includes
    #   > add "-x",%rsp
    # * add(b|l|)
    # * sub(b|l|)
    # * mov...
    # * ...
    StackDynamicOp = Pattern._operation("sub", "\%.*", "\%{}$".format(sp))

    #   4004c3:   55                      push   %esp
    #   4004c3:   55                      push   %rsp
    # TODO:
    # * pusha   push all general-purpose registers
    # * pushad  push all general-purpose registers
    # * pushf   push EFLAGS register onto the stack
    # * pushfd  push EFLAGS register onto the stack
    # * pushfq  push EFLAGS register onto the stack
    StackPushOp = Pattern._operation("push(l|)( |\t)+")

    #   4004aa:   48 83 ec 10             sub    $0x10,%rsp
    # TODO:
    # * Only track stack decrements. This includes
    #   > add "-x",%rsp
    # * add(b|l|)
    # * sub(b|l|)
    # * mov...
    # * ...
    StackSubOp = Pattern._operation("sub", "\$0x[0-9a-f]*", "\%{}$".format(sp))

    # Some operations are already covered by tracking the counter part like
    # * pop and push
    # * add and sub
    # * add reg and add -reg
    # or are recovered by using another opeartion like mov
    PotentialStackOp = (
        # fmt: off
          "(" + Pattern._operation("enter")
        + "|" + Pattern._operation("fdecstp")  # ignore counter part fincstp
        + "|" + Pattern._operation("push.*")
        + "|" + Pattern._operation("^(pop)", "\%{}$".format(sp))  # Only track push and not pop
        + ")"
        # fmt: on
    )

    @staticmethod
    def get_function_call(line):
        """Implement Pattern.get_function_call."""
        line = line.replace("\t", " ")
        line = line.replace("  ", " ")
        line_array = line.split(" ")
        address = int(line_array[-2], 16)
        name = line_array[-1][1:-1]

        return address, name

    @staticmethod
    def _get_stack_push_size(line):
        """Calculate how many bytes the stack will grow depending on the register."""
        if re.match(".*( |\t)+%{}$".format(x86.reg8bytes), line):
            return 8
        elif re.match(".*( |\t)+%{}$".format(x86.reg4bytes), line):
            return 4
        elif re.match(".*( |\t)+%{}$".format(x86.reg2bytes), line):
            return 2
        elif re.match(".*( |\t)+%{}$".format(x86.reg1byte), line):
            return 1
        else:  # constant
            return 0

    @staticmethod
    def get_stack_push_size(line):
        """Implement Pattern.get_stack_push_size."""
        size = x86._get_stack_push_size(line)

        # Check if a constant was pushed on the stack
        if size == 0:
            size = 4

        return size

    @staticmethod
    def get_stack_sub_size(line):
        """Implement Pattern.get_stack_sub_size."""
        temp = line.split(" ")[-1]
        return temp.split(",")[0][1:]
