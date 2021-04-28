#!/bin/python3
"""Patterns for the x86_64 architecture."""

import re

from .base import Pattern
from .x86 import x86


class x86_64(x86):
    """Contain the x86 64bit instruction set."""

    arch = ["x86_64"]

    #   4004c3:   55                      push   %esp
    #   4004c3:   55                      pushq  %rbp
    StackPushOp = Pattern._operation("push(q|)( |\t)+")

    @staticmethod
    def get_stack_push_size(line):
        """Implement Pattern.get_stack_push_size."""
        size = x86._get_stack_push_size(line)

        # Check if a constant was pushed on the stack
        if size == 0:
            size = 8

        return size
