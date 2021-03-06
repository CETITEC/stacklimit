# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Determine the maximum stack size of a binary program using the ELF format."""


import re
import subprocess
from cmath import log
from os import environ, listdir
from os.path import isfile

from datastructure import Stack, StackImpact, Visitor
from output import Color, Message
from patterns import Pattern, aarch64, arm, x86, x86_64

PATH = [path + "/" for path in ["."] + environ["PATH"].split(":")]


def get_arch(arch):
    """Determine the architecture.

    Note: 80386 is recognized as x86

    Args:
        arch (str): the string to determine the architecture

    Returns:
        str: the architecture defined in Pattern.arch
    """
    if not arch:
        return None

    arch = arch.lower().replace("-", "_")

    for supported_arch in Pattern.arch:
        if arch == supported_arch:
            return arch

        # Match "80386" as x86
        if supported_arch[0] == "x":
            temp = supported_arch[1:]
            if temp in arch and temp[-1] == arch[-1]:
                return supported_arch

    return None


class Statistic:
    """Helper class to iterate easily through.

    Attributes:
        title (str):           the description of the count
        count (int):           the number of occurrences
        percent (int):         the percentage of count related to number of instructions
        data (data, optional): the additional data
    """

    title = None
    count = 0
    percent = 0
    data = None

    def __init__(self, title, count, percent, data=None):
        """Create the object.

        Args:
            title (str):   the description of the count
            count (int):   the number of occurrences
            percent (int): the percentage of count related to number of instructions
            data (data):   the additional data
        """
        self.title = title
        self.count = count
        self.percent = percent
        self.data = data


class Stacklimit:
    """Infrastructure to calculate the maximal stack size.

    Attributes:
        arch (str):                 the architecture the code was compiled for
        color (bool):               show messages in color
        debug (bool):               show debug messages
        quiet (bool):               Suppress informative messages
        warn (bool):                show warnings
        multiple_warn (bool):       show same warnings multiple times
        warn_cycle (bool):          show warnings for recursive function calls
        warn_fp (bool):             show warnings for function pointers
        warn_dynamic (bool):        show warnings for dynamic stack operations
        regard_os_functions (bool): consider OS functions defined
        readelf_path (str):         the path to the readelf binary
        objdump_path (str):         the path to the objdump binary
        stacktable (Stack.Table):   the function database to calculate the stack size
    """

    arch = None
    color = None
    debug = None
    quiet = None
    warn = None
    multiple_warn = None

    warn_cycle = True
    warn_fp = True
    warn_dynamic = True

    regard_os_functions = None

    readelf_path = None
    # TODO: Add support for llvm-objdump
    objdump_path = None

    stacktable = None

    def __init__(
        self,
        debug=False,
        warn=True,
        quiet=False,
        color=False,
        multiple_warn=True,
        regard_os_functions=True,
        arch=None,
        objdump=None,
        binary=None,
    ):
        """Create the object.

        Args:
            debug (bool, optional):
                Show debug messages. Defaults to False.
            warn (bool, optional):
                Show warnings. Defaults to True.
            quiet (bool, optional):
                Suppress informative messages. Error, debug and warn messages are not
                affected by this option. Defaults to False.
            color (bool, optional):
                Show messages in color. Defaults to False.
            multiple_warn (bool, optional):
                Show same warnings multiple times. If this is False the same warning
                will only displayed once and suppressed in the future. Defaults to True.
            regard_os_functions (bool, optional):
                Consider OS functions defined in Pattern.os_functions. Defaults to True.
            arch (str, optional if binary is set):
                the architecture the code was compiled for. This defines with which
                instruction set the binary will be parsed. If not defined it will be
                detected automatically through the binary bypassed through the parameter
                binary. Defaults to None.
            objdump (str, optional):
                the path to the objdump binary. If not set, the program will try to find
                it itself. Defaults to None.
            binary (str, optional if arch is set):
                the path to the binary to determine the architecture

        Raises:
            ValueError: arch parameter wasn't set and the platform couldn't be determined
            ValueError: arch parameter was set with an unknown value
            ValueError: objdump couldn't be found
            ValueError: readelf couldn't be found
        """
        self.debug = debug
        self.color = color
        self.quiet = quiet
        self.warn = warn
        self.warn_cycle = warn
        self.warn_fp = warn
        self.warn_dynamic = warn
        self.multiple_warn = multiple_warn
        self.regard_os_functions = regard_os_functions
        self.stacktable = Stack.Table(
            [Stack.Function(address=0, name="Function Pointer")]
        )

        self.readelf_path = self._get_tool_path("readelf")
        self._init_arch(arch, binary)
        self._init_objdump(binary, objdump)

    def _init_arch(self, arch, binary):
        if not arch:
            self._print(Message.DEBUG, "Determinate platform from binary...")
            arch = self._get_arch(binary)

            if not arch:
                self._print(
                    Message.ERROR,
                    "Couldn't determinate platform.\n"
                    "Use '" + self._bold("-a") + "' or '" + self._bold("--arch") + "'"
                    "to define the platform.",
                )
                raise ValueError()

        if arch not in Pattern.arch:
            self._print(
                Message.ERROR,
                "Unsupported platform '" + arch + "'.\n" "Supported platforms are: ",
                end="",
            )
            for arch in Pattern.arch[:-2]:
                self._print(Message.INFO, arch, end=", ", prefix="")
            self._print(
                Message.INFO,
                Pattern.arch[-2] + " and " + Pattern.arch[-1] + ".\n",
                prefix="",
            )
            raise ValueError()

        self._print(Message.DEBUG, "Using architecture " + self._bold(arch))
        self.arch = arch

    def _init_objdump(self, binary, objdump=None):
        self._print(
            Message.DEBUG,
            "Determinate objdump support for architecture "
            + self._bold(self.arch)
            + "...",
        )

        if objdump:
            self.objdump_path = self._get_tool_path(objdump)
            supported = self._has_objdump_support(binary)
        else:
            supported = self._find_objdump(binary)

        if not supported:
            self._print(
                Message.ERROR,
                "Your objdump doesn't support the architecture "
                + self._bold(self.arch)
                + ".",
            )
            if not objdump:
                self._print(
                    Message.ERROR,
                    "Use '"
                    + self._bold("-o")
                    + "' or '"
                    + self._bold("--objdump")
                    + "'"
                    "to specify the objdump binary.",
                    prefix="",
                )
            raise ValueError()

        self._print(Message.DEBUG, "Using '" + self._bold(self.objdump_path) + "'")

    def _attribute_note(self, msg):
        if self.color:
            return Color.YELLOW + msg + Color.END
        else:
            return msg

    def _attribute_ok(self, msg):
        if self.color:
            return Color.GREEN + msg + Color.END
        else:
            return msg

    def _attribute_warn(self, msg):
        if self.color:
            return Color.RED + msg + Color.END
        else:
            return msg

    def _bold(self, msg):
        if self.color:
            return Color.BOLD + msg + Color.END
        else:
            return msg

    def _dark(self, msg):
        if self.color:
            return Color.DARK + msg + Color.END
        else:
            return msg

    def _func(self, msg):
        if self.color:
            return Color.CYAN + msg + Color.END
        else:
            return msg

    def _find_objdump(self, binary):
        objdumps = []
        for dir in PATH:
            try:
                for file in listdir(dir):
                    if file.endswith("objdump"):
                        objdumps.append(dir + file)
            except FileNotFoundError:
                pass

        self._print(Message.DEBUG, "Search compatible objdump...")

        for objdump in objdumps:
            cmd = [objdump, "--version"]
            output = (
                subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                .communicate()[0]
                .decode("utf-8")
            )

            if output == "":
                self._print(
                    Message.DEBUG,
                    "Couldn't get version from '" + self._bold(objdump) + "'.",
                )
                continue

            origin = output.split(" ")[0]
            # Add support for llvm-objdump
            if origin == "GNU" and self._has_objdump_support(binary, objdump):
                self.objdump_path = objdump
                return True

            self._print(
                Message.DEBUG, "'" + self._bold(objdump) + "' doesn't support arch."
            )

        return False

    def _get_arch(self, binary):
        arch = self._get_arch_with_readelf(binary)
        if not arch:
            # Since the initramfs is not really an ELF file we have to use objdump
            arch = self._get_arch_with_objdump(binary)

        if not arch:
            self._print(Message.DEBUG, "Maybe the binary is not an ELF file.")

        return arch

    def _get_arch_with_objdump(self, binary):
        if not binary:
            return None

        if not self._find_objdump(binary):
            return None

        cmd = [self.objdump_path, "-a", binary]
        output = (
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            .communicate()[0]
            .decode("utf-8")
        )

        if output == "":
            self._print(Message.DEBUG, "Couldn't read binary with objdump.")
            return None

        output_array = output.split("file format ")

        if len(output_array) < 2:
            self._print(
                Message.DEBUG,
                "Couldn't find '"
                + self._bold("file format")
                + "' in output of objdump. "
                "Maybe the syntax has changed.",
            )
            return None

        output = output_array[1]
        output = output.split("\n")[0]

        return get_arch(output)

    def _get_arch_with_readelf(self, binary):
        if not binary:
            return None

        cmd = [self.readelf_path, "-h", binary]
        output = (
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            .communicate()[0]
            .decode("utf-8")
        )

        if output == "":
            self._print(Message.DEBUG, "Couldn't read binary with readelf.")
            return None

        output_array = output.split("Machine:")

        if len(output_array) < 2:
            self._print(
                Message.DEBUG,
                "Couldn't find '" + self._bold("Machine") + "' in output of readelf. "
                "Maybe the syntax has changed.",
            )
            return None

        output = output_array[1]
        output = output.split("\n")[0]
        output = output.split(" ")[-1]

        return get_arch(output)

    def _get_tool_path(self, tool):
        for dir in [""] + PATH:
            path = dir + tool
            if isfile(path):
                return path

        self._print(Message.ERROR, "Couldn't find '" + self._bold(tool) + "'")
        raise ValueError()

    def _has_objdump_support(self, binary, objdump=None):
        if not binary:
            return False

        if not objdump:
            objdump = self.objdump_path

        cmd = [objdump, "-d", "--stop-address=0", binary]
        returncode = subprocess.call(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        return returncode == 0

    def _print(self, kind, *objects, sep=" ", end="\n", prefix=True):
        if kind is Message.DEBUG:
            condition = self.debug
        elif kind is Message.ERROR:
            condition = True
        elif kind is Message.WARN:
            condition = self.warn
        else:
            condition = not self.quiet

        if condition:
            if prefix and kind.prefix:
                if self.color and kind.color:
                    text = kind.color + kind.prefix + Color.END
                else:
                    text = kind.prefix
                print(text, end="")
            print(*objects, sep=sep, end=end)

    def _print_call_branch(self, function, path=[]):
        indent = 3 * (len(path) - 1)
        alight = function in path

        self._print_call_node(function, indent, alight)

        if not alight:
            for calls in function.calls:
                self._print_call_branch(calls, path + [function])

    def _print_call_node(self, function, indent=0, alight=False):
        arrow = "-> " if function.returns else ""
        prefix = ""
        suffix = ""

        if function.address == 0:
            address = self._bold("Unknown")
            name = "Function Pointer"
            if self.color:
                name = Color.RED + name + Color.END
        else:
            address = self._bold(hex(function.address))
            name = self._func(function.name)

        total = self._bold(str(function.total))
        size = str(function.size)
        size = self._dark("(" + size + ")")

        if function.imprecise:
            total = ">" + total

        info = address + " " + name + " " + total
        if not alight and not function.dynamic and function.address != 0:
            info += " " + size

        if function.cycle and alight:
            suffix += " CIRCLE"
        if function.dynamic:
            suffix += " DYNAMIC"
        if self.color and suffix != "":
            suffix = Color.RED + suffix + Color.END

        if self.color and (suffix != "" or function.cycle):
            arrow = Color.RED + arrow + Color.END

        if indent > 0:
            prefix = "{:{}}".format("", indent)

        prefix += arrow

        self._print(Message.INFO, "{}{}{}".format(prefix, info, suffix))

    def _print_cycle_warn(self, callstack):
        current = callstack[-1]
        start = callstack.index(current)

        if self.multiple_warn:
            self._print(
                Message.WARN,
                "Found cycle in call graph entering with '"
                + self._func(current.name)
                + "'",
            )
        else:
            self._print(Message.WARN, "Found cycles in call graph")

        if self.debug and self.warn_cycle:
            path_string = [self._func(call.name) for call in callstack]
            if self.color:
                path_string[start] = Color.RED + current.name + Color.END
                path_string[-1] = Color.RED + current.name + Color.END

            self._print(Message.DEBUG, "  ", end="")

            for calls in path_string:
                self._print(Message.DEBUG, calls, end=" -> ", prefix=False)

            self._print(Message.DEBUG, "...", prefix=False)

    def _regard_function(self, function):
        if function.address == 0:
            return False

        if self.regard_os_functions:
            return True

        return function.section == ".text" and function.name not in Pattern.os_functions

    def _stack_impact(self, stack_impact):
        if stack_impact is StackImpact.Clear:
            return self._attribute_ok("clear")
        elif stack_impact is StackImpact.Potential:
            return self._attribute_note("pot. ")
        elif stack_impact is StackImpact.Weak:
            return self._attribute_warn("weak ")
        elif stack_impact is StackImpact.No:
            return "     "
        else:
            raise ValueError("Unknown StackImpact state {}.".format(stack_impact))

    def _track_operation(self, pattern, line, stack_impact, size=None):
        operation = Pattern.get_operation(line)

        if operation is not None:
            self.stacktable.statistic.add_operation(operation, stack_impact)

        stack_impact_text = self._stack_impact(stack_impact)

        size_text = "     "
        if size:
            size_text = self._bold("+{:>{}}B".format(size, 3))

        prefix = "  {} {:<16} {}".format(stack_impact_text, pattern, size_text)
        self._print(Message.DEBUG, prefix, line)

    def _handle_dynamic(self, callstack):
        current = callstack[-1]

        if not current.dynamic:
            return

        for node in callstack[:-1]:
            node.imprecise = True

        if self.warn_dynamic:
            self.warn_dynamic = self.multiple_warn
            if self.multiple_warn:
                self._print(
                    Message.WARN,
                    "Dynamic stack operation in function '"
                    + self._func(current.name)
                    + "'",
                )
            else:
                self._print(Message.WARN, "Found dynamic stack operations")

    def _handle_function_pointer(self, callstack):
        current = callstack[-1]

        if not [child for child in current.calls if child.address == 0]:
            return

        for node in callstack[:-1]:
            node.imprecise = True
        if self.warn_fp:
            self.warn_fp = self.multiple_warn
            if self.multiple_warn:
                self._print(
                    Message.WARN,
                    "Function '"
                    + self._func(current.name)
                    + "' calls a function pointer",
                )
            else:
                self._print(Message.WARN, "Found function pointers")

    def _handle_cycle(self, callstack):
        current = callstack[-1]

        start = callstack.index(current)
        if not callstack or start == len(callstack) - 1:
            return False

        for node in callstack[:start]:
            node.imprecise = True
        for node in callstack[start:-1]:
            node.imprecise = True
            node.cycle = True

        if self.warn_cycle:
            self.warn_cycle = self.multiple_warn
            self._print_cycle_warn(callstack)

        return True

    def _handle_node(self, callstack):
        if not callstack:
            return True

        current = callstack[-1]

        if current.visited:
            return False

        if self._regard_function(current):
            self._handle_dynamic(callstack)
            self._handle_function_pointer(callstack)

        return self._handle_cycle(callstack)

    def calculate_stack(self):
        """Calculate the maximal recursive stack size for each function.

        Returns:
            bool: true if the stack has a limit and false if the stack limit cannot be
                  determined
        """
        entrances = [function for function in self.stacktable if not function.returns]
        visitor = Visitor(entrances)

        while visitor.callstack:
            current = visitor.down()

            if current:
                skip = self._handle_node(visitor.callstack)
                current.visited = True
                if not skip:
                    subcall_size = 0
                    for child in current.calls:
                        subcall_size = max(subcall_size, child.total)
                    current.total = current.size + subcall_size

            visitor.up()

        for entrance in entrances:
            if entrance.imprecise:
                return False

        return True

    def parse(self, binary):
        """Calculate the stack size of each function.

        Only the stack size of the function itself is considered. Stack changes caused by
        function calls within the current function are ignored.

        Args:
            binary (str): the path to the binary file
        """
        if self.arch in aarch64.arch:
            pattern = aarch64
        elif self.arch in arm.arch:
            pattern = arm
        elif self.arch in x86.arch:
            pattern = x86
        elif self.arch in x86_64.arch:
            pattern = x86_64
        else:
            return

        objdump_cmd = [self.objdump_path, "-d", binary]
        objdump = subprocess.Popen(
            objdump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        file = None
        section = None
        current = None

        for line in objdump.stdout:
            line = line.decode("utf-8")[:-1]

            # Set file
            if re.match(pattern.FileFormat, line):
                line_array = line.split(" ")
                path = line_array[0][:-1]
                file = path.split("/")[-1]

                # Skip the following code since this line is not an instruction
                continue

            # Set section
            elif re.match(pattern.Section, line):
                section = pattern.get_section(line)
                self._print(Message.DEBUG)
                self._print(Message.DEBUG, "Disassembly of section {}:".format(section))

                # Skip the following code since this line is not an instruction
                continue

            elif re.match(pattern.Function, line):
                (address, name) = pattern.get_function(line)
                current = self.stacktable.find(address)

                if current:
                    current.file = file
                    current.section = section
                else:
                    current = self.stacktable.append(
                        Stack.Function(
                            address=address, name=name, section=section, file=file
                        )
                    )

                current.visited = True
                self._print(Message.DEBUG, "{}:".format(self._func(name)))

            # Empty line
            elif len(line) == 0:
                continue

            # Analyze the instruction

            if pattern.StackPushOp and re.match(pattern.StackPushOp, line):
                size = pattern.get_stack_push_size(line)
                current.size += size
                self._track_operation("StackPushOp", line, StackImpact.Clear, size)

            # TODO: Only track sub with positive numbers and add with negative numbers
            # Note: We ignore all 'add' operations. We're only interested in 'sub'.
            elif pattern.StackSubOp and re.match(pattern.StackSubOp, line):
                temp = pattern.get_stack_sub_size(line)
                if temp[:2] == "0x":
                    size = int(temp, 16)
                else:
                    size = int(temp)

                # TODO: Rewrite this
                if size > 0xF000000000000000:
                    continue

                if size > 0xF0000000:
                    size = -size
                    size += 0x80000000
                    size += 0x80000000

                if size > 0x10000000:
                    continue

                current.size += size
                self._track_operation("StackSubOp", line, StackImpact.Clear, size)

            elif pattern.StackDynamicOp and re.match(pattern.StackDynamicOp, line):
                current.dynamic = True
                self._track_operation("StackDynamicOp", line, StackImpact.Weak)

            elif pattern.FunctionCall and re.match(pattern.FunctionCall, line):
                (address, name) = pattern.get_function_call(line)
                function = self.stacktable.find(address)

                if not function:
                    function = self.stacktable.append(
                        Stack.Function(address=address, name=name)
                    )

                if not current.calls.find(address):
                    current.calls.append(function)
                    function.returns.append(current)

                size = pattern.get_stack_call_size(line)
                current.size += size
                if size == 0:
                    size = None
                self._track_operation("FunctionCall", line, StackImpact.Clear, size)

            elif pattern.FunctionPointer and re.match(pattern.FunctionPointer, line):
                function_pointer = self.stacktable.find(0)
                current.calls.append(function_pointer)
                function_pointer.returns.append(current)

                self._track_operation("FunctionPointer", line, StackImpact.Weak)

            elif pattern.PotentialStackOp and re.match(pattern.PotentialStackOp, line):
                self._track_operation("PotentialStackOp", line, StackImpact.Potential)
            else:
                self._track_operation("", line, StackImpact.No)

        for function in [
            function
            for function in self.stacktable
            if not function.visited and function.address != 0
        ]:
            address = self._bold(hex(function.address))
            name = self._func(function.returns[0].name)
            self._print(
                Message.DEBUG,
                "Ignore inner FunctionCall in {} to {} ({})".format(
                    name, address, function.name
                ),
            )
            del self.stacktable[function]
            for caller in function.returns:
                del caller.calls[function]

        for function in self.stacktable:
            function.visited = False

        if self.debug:
            print()

    def get_stack_limit(self):
        """Get the maximal stack size.

        Returns:
            int: the maximal stack size
        """
        return self.stacktable.limit()

    def print_stack_table(self, show_header=False, show_section=False):
        """Print all functions and their stack usage.

        Args:
            show_header (bool, optional):
                Show the column headers of the table. Defaults to False.
            show_section (bool, optional):
                Show the section of each function. Defaults to False.
        """
        # Should never happen
        if not self.stacktable:
            return

        address_len = 0xFFFFF if show_header else 1
        name_len = 8 if show_header else 1
        section_len = 7 if show_header else 1
        file_len = 4 if show_header else 1
        size_len = 99999 if show_header else 1
        # This is correct! The length is increment by one later
        total_len = 9999 if show_header else 1

        for function in self.stacktable:
            address_len = max(function.address, address_len)
            name_len = max(len(function.name), name_len)
            if function.file:
                file_len = max(len(function.file), file_len)
            if show_section and function.section:
                section_len = max(len(function.section), section_len)
            size_len = max(function.size, size_len)
            total_len = max(function.total, total_len)

        address_len = int(log(address_len, 16).real + 3)
        size_len = int(log(size_len, 10).real + 1)
        # Increment the length for the imprecise symbol
        total_len = int(log(total_len, 10).real + 1) + 1

        self._print(Message.INFO)

        if show_header:
            section = "section "
            if not show_section:
                section = ""
                section_len = 0

            self._print(
                Message.INFO,
                "{:>{}} {:<{}}  {:<{}}{:<{}}  {:>{}} {:>{}}".format(
                    "address",
                    address_len,
                    "function",
                    name_len,
                    section,
                    section_len,
                    "file",
                    file_len,
                    "fsize",
                    size_len,
                    "tsize",
                    total_len,
                ),
            )

        self.stacktable.sort()

        for function in self.stacktable:
            if self._regard_function(function):
                address = self._bold(
                    "{:#0{width}x}".format(function.address, width=address_len)
                )
                name = self._func("{:{width}}".format(function.name, width=name_len))
                section = ""
                file = function.file if function.file else ""
                file = self._dark("{:{width}}".format(file, width=file_len))
                size = "{:{width}}".format(function.size, width=size_len)
                # Workaround for text with color
                total = self._bold(str(function.total))
                imprecise = ">" if function.imprecise else " "
                total_prefix_len = total_len - int(log(function.total + 1, 10).real) - 1
                total = "{:>{width}}{}".format(imprecise, total, width=total_prefix_len)

                if show_section:
                    section = function.section if function.section else ""
                    section = self._dark(
                        "{:{width}}".format(section, width=section_len)
                    )
                    section = section + " "

                self._print(
                    Message.INFO,
                    "{} {}  {}{}  {} {}".format(
                        address, name, section, file, size, total
                    ),
                )

    def print_statistic_of_operations(self, show_header=False):
        """Print statistic of the parsed instructions.

        Args:
            show_header (bool, optional):
                Show the column headers of the table. Defaults to False.
        """
        operations = self.stacktable.statistic.per_operations

        total = 0
        title_len = 9 if show_header else 1
        count_len = 99999 if show_header else 1

        for operation in operations:
            total += operations[operation].executions
            title_len = max(len(operation), title_len)
            count_len = max(operations[operation].executions, count_len)

        count_len = int(log(count_len, 10).real + 1) + 1
        percent_len = 4

        statistics = [Statistic("total", total, 100, StackImpact.No)]
        for operation in operations:
            executions = operations[operation].executions
            executions_percent = round(100 * float(executions / total))
            stack_impact = operations[operation].stack_impact
            statistics.append(
                Statistic(operation, executions, executions_percent, stack_impact)
            )

        statistics.sort(key=lambda statistic: statistic.count, reverse=True)

        if show_header:
            self._print(
                Message.INFO,
                "{:<{}} {:>{}}  {:>{}}  stack impact".format(
                    "operation",
                    title_len,
                    "count",
                    count_len,
                    "%",
                    percent_len,
                ),
            )

        for statistic in statistics:
            operation = "{:{width}}".format(statistic.title, width=title_len)
            count = "{:{width}}".format(statistic.count, width=count_len)
            percent = self._bold(
                "{:{width}}".format(statistic.percent, width=percent_len)
            )
            stack_impact = self._stack_impact(statistic.data)

            self._print(
                Message.INFO,
                "{} {} {}%  {}".format(operation, count, percent, stack_impact),
            )

    def print_statistic_of_stack_impacts(self, show_header=False):
        """Print stack impact statistic of the parsed instructions.

        Args:
            show_header (bool, optional):
                Show the column headers of the table. Defaults to False.
        """
        total = sum(self.stacktable.statistic.per_stack_impact.values())

        clear = self.stacktable.statistic.per_stack_impact[StackImpact.Clear]
        clear_percent = round(100 * float(clear / total))

        weak = self.stacktable.statistic.per_stack_impact[StackImpact.Weak]
        weak_percent = round(100 * float(weak / total))

        skipped_clear = self.stacktable.statistic.per_stack_impact[StackImpact.No]
        skipped_clear_percent = round(100 * float(skipped_clear / total))

        skipped_potential = self.stacktable.statistic.per_stack_impact[
            StackImpact.Potential
        ]
        skipped_potential_percent = round(100 * float(skipped_potential / total))

        skipped = skipped_clear + skipped_potential
        skipped_percent = skipped_clear_percent + skipped_potential_percent

        title_len = 8
        count_len = 99999 if show_header else 1

        statistics = [
            Statistic("total", total, 100),
            Statistic("clear", clear, clear_percent),
            Statistic("weak (unknown stack impact)", weak, weak_percent),
            Statistic("skipped", skipped, skipped_percent),
            Statistic(
                "  potential stack instructions",
                skipped_potential,
                skipped_potential_percent,
            ),
            Statistic(
                "  unexpected stack impact",
                skipped_clear,
                skipped_clear_percent,
            ),
        ]

        for statistic in statistics:
            title_len = max(len(statistic.title), title_len)
            count_len = max(statistic.count, count_len)

        count_len = int(log(count_len, 10).real + 1)
        percent_len = 4

        if show_header:
            self._print(
                Message.INFO,
                "{:<{}} {:>{}}  {:>{}}".format(
                    "",
                    title_len,
                    "count",
                    count_len,
                    "%",
                    percent_len,
                ),
            )

        for statistic in statistics:
            title = "{:{width}}".format(statistic.title, width=title_len)
            count = "{:{width}}".format(statistic.count, width=count_len)
            percent = self._bold(
                "{:{width}}".format(statistic.percent, width=percent_len)
            )

            self._print(Message.INFO, "{} {} {}%".format(title, count, percent))

    def print_statistic(self, show_header=False, show_operation_statistic=False):
        """Print statistic of the parsed instructions.

        Args:
            show_header (bool, optional):
                Show the column headers of the table. Defaults to False.
            show_operation_statistic (bool, optional):
                show operation statistic
        """
        if show_operation_statistic:
            self.print_statistic_of_operations(show_header)
            self._print(Message.INFO)
        self.print_statistic_of_stack_impacts(show_header)

    def print_call_tree(self):
        """Print the function call tree."""
        for top in self.stacktable:
            if not top.returns and self._regard_function(top):
                self._print_call_branch(top)
