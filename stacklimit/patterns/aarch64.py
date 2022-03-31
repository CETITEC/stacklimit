# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Patterns for the ARM 64bit (aka AArch64) architecture."""

from .arm import arm
from .base import Pattern


class aarch64(arm):
    """Extend the arm class with the ARM A64 instruction set.

    This extends the arm class with 64bit related properties.

    Note: The instructions LDM, STM, PUSH and POP doesn't exist in A64. Therefore the
    instructions LDP and STP are used to load and store a pair of registers.
    """

    arch = ["aarch64"]

    @staticmethod
    def get_stack_push_size(line):
        """Implement Pattern.get_stack_push_size."""
        raise RuntimeError("The instruction PUSH doesn't exist in A64!")

    @staticmethod
    def get_stack_sub_size(line):
        """Implement Pattern.get_stack_sub_size."""
        temp = line.split("#")[-1]
        temp = temp.split("]")[0]
        if temp[0] == "-":
            temp = temp[1:]
        return temp
