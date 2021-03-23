#!/bin/python3
"""Patterns for the aarch64 architecture."""

from .arm import arm
from .base import Pattern


class aarch64(arm):
    """Contain the aarch64 instruction sets."""

    arch = ["aarch64"]

    @staticmethod
    def get_stack_push_size(line):
        """Implement Pattern.get_stack_push_size."""
        return 8 * arm.get_stack_push_count(line)

    @staticmethod
    def get_stack_sub_size(line):
        """Implement Pattern.get_stack_sub_size."""
        temp = line.split("#")[-1]
        temp = temp.split("]")[0]
        if temp[0] == "-":
            temp = temp[1:]
        return temp
