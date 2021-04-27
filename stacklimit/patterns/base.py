#!/bin/python3
"""The base class to implement patterns for a specific architecture."""

from abc import ABC, abstractmethod


class Pattern(ABC):
    """Contain instruction sets for different kind of calls.

    Attributes:
        arch (list[str]):         the supported architectures
        os_functions (list[str]): OS functions, e.g. for initialization and termination
        FileFormat (str):         regex of the file format line
        Section (str):            regex of sections
        Function (str):           regex of functions
        FunctionCall (str):       regex of function calls
        FunctionPointer (str):    regex of function pointers
        StackDynamicOp (str):     regex of dynamic operations
        StackPushOp (str):        regex of stack push operations
        StackSubOp (str):         regex of substraction operators on the stack pointer
    """

    arch = ["arm", "aarch64", "x86", "x86_64"]
    os_functions = [
        "register_tm_clones",
        "deregister_tm_clones",
        "frame_dummy",
        "call_weak_fn",
        "abort@plt",
        ".plt",
        "_init",
        "_start",
        "_fini",
        "__libc_csu_init",
        "__libc_csu_fini",
        "__init_array_start",
        "__init_array_end",
        "__do_global_dtors_aux",
        "__do_global_dtors_aux_fini_array_entry",
        "__frame_dummy_init_array_entry",
        "__libc_start_main@plt",
        "__gmon_start__@plt",
    ]

    # dir/binary:     file format elf64-x86-64
    FileFormat = "^.*:( |\t)*file format "

    # Disassembly of section .text:
    Section = "^Disassembly of section .*:"

    # 000000000040076d <main>:
    Function = "^[0-9a-f]* \<.*\>:$"

    FunctionCall = None
    FunctionPointer = None
    StackDynamicOp = None
    StackPushOp = None
    StackSubOp = None

    @staticmethod
    def _operation(*args):
        """Generate a string from operations with a variable number of registers.

        > instruction [reg1[, reg2[, reg3 [...]]]]
        > instruction [reg1[,reg2[,reg3[...]]]]

        Args:
            args (list[str]):
                The instruction with a variable number of registers. The first element
                is the instruction. The following elements are the registers.

        Returns:
            str: the operation
        """
        op = ".*( |\t)+{}".format(args[0])

        if len(args) > 1:
            op = "{}( |\t)+{}".format(op, args[1])

        for arg in args[2:]:
            op = "{},( |\t|)+{}".format(op, arg)

        return op

    @staticmethod
    def get_function(line):
        """Filter the start address and the name of the function.

        Args:
            line (str): the text line of the function

        Returns:
            (int, str): the start address and the name of the function
        """
        line_array = line.split(" ")
        address = int(line_array[0], 16)
        name = " ".join(line_array[1:])[1:-2]

        return address, name

    @staticmethod
    def get_section(line):
        """Filter the name of the section.

        Args:
            line (str): the text line of the section

        Returns:
            str: the name of the section
        """
        line_array = line.split(" ")
        name = line_array[-1][0:-1]

        return name

    @staticmethod
    @abstractmethod
    def get_function_call(line):
        """Filter the address and the name of the function which is called.

        Args:
            line (str): the text line of the function call operation

        Returns:
            (int, str): the address and the name of the function which is called
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_stack_push_size(line):
        """Calculate the size difference of the stack after the stack push operation.

        This function will return how much the stack will grow after the stack push
        operation.

        Args:
            line (str): the text line of the stack push operation

        Returns:
            int: the size the stack will grow
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_stack_sub_size(line):
        """Filter the size the stack sub operation will manipulate the stack.

        Args:
            line (str): the text line of the stack sub operation

        Returns:
            int: the size the stack will be manipulated
        """
        raise NotImplementedError
