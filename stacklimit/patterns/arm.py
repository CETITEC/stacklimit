#!/bin/python3
"""Patterns for the ARM 32bit (aka AArch 32) and 64bit (aka AArch64) architecture."""

from .base import Pattern


class arm(Pattern):
    """Contain the A32, T32 and A64 instruction set of the ARM architecture.

    Both 32 bit and 64 registers are covered. Further the following instruction sets are
    considered:
    * AArch32
      * A32 (previously known as ARM)
      * T32 (previously known as Thumb2)
    * AArch64
      * A64

    Instructions which depends on the architecture and cannot be determine on the
    register name or operation are splitted into arm (this class) and aarch64.
    """

    arch = ["arm"]

    # Stack pointer
    sp = "(w|)sp"

    # General purpose 4 byte (integer) registers
    # Ignore the "zero" register w31, since it won't influence the stack
    reg4bytes = (
        # fmt: off
          "(" + "w((|1|2)(0|1|2|3|4|5|6|7|8|9)|30)"
        + ")"
        # fmt: on
    )

    # General purpose 8 byte (integer) registers
    # Ignore the "zero" register x31, since it won't influence the stack
    reg8bytes = (
        # fmt: off
          "(" + "x((|1|2)(0|1|2|3|4|5|6|7|8|9)|30)"
        + ")"
        # fmt: on
    )

    #   1069c:   ebffff80        bl      104a4 <func_alpha>
    # TODO: Test cbz and cbnz
    FunctionCall = (
        # fmt: off
          "(" + Pattern._operation("(b[a-z]{2}|blx|bl|b)(.n|)", "[0-9]+")
        + "|" + Pattern._operation("(cbz|cbnz)", "[a-z]([a-z]|[0-9]+)", "[0-9]+")
        + ")"
        # fmt: on
    )

    #   1031c:   e12fff13    bx  r3
    #   10344:   012fff1e    bxeq    lr
    #   10918:   e12fff33    blx r3
    FunctionPointer = (
        # fmt: off
          "(" + Pattern._operation("(bx[a-z]{2}|bxj|blx|bx)", "[a-z]([a-z]|[0-9]+)")
        + "|" + Pattern._operation("bne(.w|w|s|)", "(0x[0-9a-f]+|[0-9]+)")
        + ")"
        # fmt: on
    )

    # TODO: Test stm*
    # TODO: push{cond}
    StackPushOp = (
        # fmt: off
          "(" + Pattern._operation("push(|[a-z]{2})")
        + "|" + Pattern._operation("stm(ia|ib|da|db)(.w|w|s|)", sp)
        + ")"
        # fmt: on
    )

    #   ad5e0a:   b0f8        sub   sp,  #480
    #   ad7620:   b093        sub   sp,  #76
    #   a31760:   e24dd01c    sub   sp,  sp, #28
    #   a31760:   e24dd01c    add   sp,  sp, #-28
    #   ad6e4e:   f5ad7d21    sub.w sp,  sp, #644
    #      4bc:   a9bc7bfd    stp   x29, x30, [sp,#-64]!
    #      894:   a9af7bfd    stp   x29, x30, [sp,#-272]!
    #     4610:   f81d0ffe    str        x30, [sp, #-48]!
    StackSubOp = (
        # fmt: off
          "(" + Pattern._operation("stp", "x[0-9]+", "[a-z]([a-z]|[0-9]+)", "\[{}, \#-(0x[0-9a-f]+|[0-9]+)\]".format(sp))
        + "|" + Pattern._operation("str(ex|)(.w|w|s|)", "[a-z]([a-z]|[0-9]+)", "\[{}, \#-(0x[0-9a-f]+|[0-9]+)\]".format(sp))
        + "|" + Pattern._operation("sub(.w|w|s|)", sp, sp, "\#(0x[0-9a-f]|[0-9]+)")
        + "|" + Pattern._operation("add(.w|w|s|)", sp, sp, "\#-(0x[0-9a-f]|[0-9]+)")
        + ")"
        # fmt: on
    )

    @staticmethod
    def get_function_call(line):
        """Implement Pattern.get_function_call."""
        name = line.split("<")[1]
        name = name.split(">")[0]

        line = line.split(" <")[0]
        line = line.replace("\t", " ")
        line = line.replace("  ", " ")
        line_array = line.split(" ")
        address = int(line_array[-1], 16)

        return address, name

    @staticmethod
    def get_stack_push_count(line):
        """Count the registers pushed onto the stack.

        Args:
            line (str): the text line of the stack push operation

        Returns:
            int: the number of the registers
        """
        # TODO: push {r0,r4-r7}
        temp = line.split("{")[-1]
        temp = temp.split("}")[0]
        return temp.count(",") + 1

    @staticmethod
    def get_stack_push_size(line):
        """Implement Pattern.get_stack_push_size."""
        return 4 * arm.get_stack_push_count(line)

    @staticmethod
    def get_stack_sub_size(line):
        """Implement Pattern.get_stack_sub_size."""
        temp = line.split("#")[-1]
        temp = temp.split("\n")[0]
        temp = temp.split("\t")[0]
        temp = temp.split(" ")[0]
        if temp[0] == "-":
            temp = temp[1:]
        return temp
