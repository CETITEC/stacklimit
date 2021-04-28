#!/bin/python3
"""Patterns for the x86 architecture."""

from .base import Pattern


class x86(Pattern):
    """Contain the x86 instruction set."""

    arch = ["x86"]

    # Stack pointer
    sp = "(e|r|l|)sp"

    # 1 byte registers
    reg1byte = (
        # fmt: off
          "(" + "(a|b|c|d)(h|l)"
        + "|" + "(bp|si|di|sp)l"
        + "|" + "r(8|9|10|11|12|13|14|15)b"
        + ")"
        # fmt: on
    )

    # 2 bytes registers
    reg2bytes = (
        # fmt: off
          "(" + "(a|b|c|d)x"
        + "|" + "bp|si|di|sp"
        + "|" + "r(8|9|10|11|12|13|14|15)w"
        + ")"
        # fmt: on
    )

    # 4 bytes registers
    reg4bytes = (
        # fmt: off
          "(" + "e(a|b|c|d)x"
        + "|" + "e(bp|si|di|sp)"
        + "|" + "r(8|9|10|11|12|13|14|15)d"
        + ")"
        # fmt: on
    )

    # 8 bytes registers
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
    StackDynamicOp = Pattern._operation("sub", "\%.*", "\%{}$".format(sp))

    #   4004c3:   55                      push   %esp
    #   4004c3:   55                      push   %rsp
    StackPushOp = Pattern._operation("push(l|)( |\t)+")

    #   4004aa:   48 83 ec 10             sub    $0x10,%rsp
    StackSubOp = Pattern._operation("sub", "\$0x[0-9a-f]*", "\%{}$".format(sp))

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
    def get_stack_push_size(line):
        """Implement Pattern.get_stack_push_size."""
        return 4

    @staticmethod
    def get_stack_sub_size(line):
        """Implement Pattern.get_stack_sub_size."""
        temp = line.split(" ")[-1]
        return temp.split(",")[0][1:]
