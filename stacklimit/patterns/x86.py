#!/bin/python3
"""Patterns for the x86 architecture."""

from .base import Pattern


class x86(Pattern):
    """Contain the x86 instruction set."""

    arch = ["x86"]

    #   400734:       e8 b0 fe ff ff          callq  4005e9 <function_e>
    FunctionCall = Pattern._operation("callq", "[0-9a-f]+ \<.*\>$")

    #   400804:   ff d0                   callq  *%rax
    FunctionPointer = Pattern._operation("callq", ".*%.*$")

    #   XXXXXX:   YY YY YY YY             add     0xff,%rsp
    #   XXXXXX:   YY YY YY YY             sub     0xef,%rsp
    StackDynamicOp = Pattern._operation("sub", "\%.*", "\%(e|r)sp$")

    #   4004c3:   55                      push   %esp
    #   4004c3:   55                      push   %rsp
    StackPushOp = Pattern._operation("push(l|)( |\t)+")

    #   4004aa:   48 83 ec 10             sub    $0x10,%rsp
    StackSubOp = Pattern._operation("sub", "\$0x[0-9a-f]*", "\%(e|r)sp$")

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
