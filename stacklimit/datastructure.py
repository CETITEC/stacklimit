# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""The data structure for analyzing and calculating the stack size of each function."""

MAX_NAME_LEN = 64


class StackImpact:
    """Status of the stack operation.

    No:         no stack operation recognized or considered
    Clear:      stack operation recognized and considered correctly
    Potential:  potential stack operation recognized, but not considered
    Weak:       stack operation recognized, but cannot be considered correctly

    The states are prioritizes to make them comparable.
    """

    No = 0
    Clear = 1
    Potential = 2
    Weak = 3


class OperationStatistic:
    """Statistic of an operation.

    Attributes:
        executions (int):                    the number of occur
        stack_operation (StackImpact): the status of the stack operation
    """

    executions = 0
    stack_impact = None

    def __init__(self, executions, stack_impact):
        """Create the object.

        Args:
            executions (int):                       the number of occur
            stack_impact (StackImpact): the status of the stack operation
        """
        self.executions = executions
        self.stack_impact = stack_impact


class Visitor:
    """Visit each node of the tree, which represents all recursive function calls.

    Each node represents a function. All children of a node are functions, which are
    called by the function represented by the current node.

    The visitor walks through the whole tree by walking down and up and mark all visited
    nodes to not visit them again.

    Attributes:
        callstack (list[Stack.Table]):
            The function which have to be called to reach the current function
        queue (list[list[Stack.Table]]):
            Contains functions of each function in callstack. The first list contains
            functions which have to be handled after the first function in callstack has
            been done. The second list in the queue includes the functions which have to
            be handled after the second function in the callstack has been done...
    """

    callstack = []
    queue = [[]]

    def __init__(self, entrances=None):
        """Create the object.

        Args:
            entrances (list[Stack.Table], optional):
                The entry functions of the binary like the main function. Defaults to
                None.
        """
        if entrances:
            self.callstack = [entrances[-1]]
            self.queue = [entrances[:-1]]
        else:
            self.callstack = []
            self.queue = [[]]

    def __eq__(self, other):
        """Return self.callstack == other.callstack and self.queue == other.queue."""
        return self.callstack == other.callstack and self.queue == other.queue

    def __ne__(self, other):
        """Return self.callstack != other.callstack or self.queue != other.queue."""
        return not self.__eq__(other)

    def down(self):
        """Walk to a leaf of the current sub-tree.

        Returns:
            Stack.Function: the leaf node
        """
        next_call = self.callstack[-1]
        calls = [child for child in next_call.calls if not child.visited]

        # FIXME: Return None if children are empty
        # if not calls:
        #    return None

        while calls:
            next_call = calls.pop()

            if next_call in self.callstack:
                self.callstack.append(next_call)
                break

            self.callstack.append(next_call)

            # FIXME: Always add this, to make it more consequent and the algorithm would
            # have less side effects to handle...
            if calls:
                self.queue.append(calls)

            calls = [child for child in next_call.calls if not child.visited]

        return self.callstack[-1]

    # FIXME: Only walk up, but not to the side. Current behavior is like this:
    #
    # Before:   0    After:   0
    #          / \           / \
    #       ->1   2         1 ->2
    def up(self):
        """Walk up to the parent node and down to the next unvisited children.

        Returns:
            Stack.Function: the unvisited sibling of the current node if available,
                            otherwise the parent node.
        """
        if self.callstack:
            self.callstack.pop()

        tier = len(self.callstack)

        if tier < len(self.queue):
            if self.queue[tier]:
                self.callstack.append(self.queue[tier].pop())

            # FIXME: If we always empty lists in down(), we always have to delete it
            # here, too
            if not self.queue[tier]:
                del self.queue[tier]
                # FIXME: if we reach that, we are sure that we won't walk down again.
                # Why not keep going upwards until there are unvisited children again?

        if len(self.callstack):
            return self.callstack[-1]

        return None


class Stack:
    """The infrastructure to collect stack information of executables or libraries.

    In the following Executables and libraries are called binaries.
    """

    class Statistic:
        """Statistic about operation codes of a binary.

        Attributes:
            operations (dict[StackImpact]):
                list of all executed instructions with the number of occur
            statistic[StackImpact.No] (int):
                the number of skipped instructions, which don't manipulate the stack
            statistic[StackImpact.Clear] (int):
                the number of instructions which increase the stack with the known
                amount of bytes
            statistic[StackImpact.Potential] (int):
                the number of skipped potential stack instructions
            statistic[StackImpact.Weak] (int):
                the number of instructions which increase the stack, but the stack
                increase can't be calculated
        """

        per_operations = {}
        per_stack_impact = {
            StackImpact.No: 0,
            StackImpact.Clear: 0,
            StackImpact.Potential: 0,
            StackImpact.Weak: 0,
        }

        def add_operation(self, operation, stack_impact):
            """Add an operation to the statistics.

            Args:
                operation (str):                        the instruction
                stack_impact (StackImpact): the status of the stack
                                                        operation
            """
            if operation in self.per_operations:
                self.per_operations[operation].executions += 1
                if stack_impact > self.per_operations[operation].stack_impact:
                    self.per_operations[operation].stack_impact = stack_impact
            else:
                self.per_operations[operation] = OperationStatistic(1, stack_impact)

            self.per_stack_impact[stack_impact] += 1

    class Function:
        """A function of a binary.

        The class includes all essential attributes of a function needed to build a call
        tree and calculates the stack size.

        Attributes:
            address (int):         the start address of the function
            name (str):            the function name
            file (str):            the path of the object file the function is defined
            size (int):            the size the function will let the stack maximal grow
            total (int):           the size the function and the functions, which can be
                                   called be this function, can let the stack maximal
                                   grow
            dynamic (bool):        if the function executes a dynamic stack operation
            imprecise (bool):      if the stack size cannot be calculated exactly
                                   (because of function pointers or call cycles)
            cycle (bool):          if the function can be called recursively
                                   (by a recursive call)
            calls (Stack.Table):   the functions, which can be called by this function
            returns (Stack.Table): the call stack of the Visitor of the function
            visited (bool):        if the function was already visited by the Visitor
            section (str):         the section the function is defined
        """

        address = None
        name = None
        file = ""
        size = None
        total = 0
        dynamic = False
        imprecise = False
        cycle = False
        calls = None
        returns = None
        visited = False
        # lock = False
        section = None

        def __init__(self, address, name=None, section=None, file="", size=0):
            """Create the object.

            Args:
                address (int):           the start address of the function.
                name (str, optional):    the function name. If not set, the address will
                                         be taken as the name. Defaults to None.
                section (str, optional): the section the function is defined.
                                         Defaults to None.
                file (str, optional):    the path of the object file the function is
                                         defined. Defaults to "".
                size (int, optional):    the size the function will let the stack
                                         maximal grow. Defaults to 0.
            """
            self.address = address
            if name is None:
                name = str(address)
            if len(name) > MAX_NAME_LEN:
                name = name[: MAX_NAME_LEN - 3] + "..."
            self.name = name
            self.section = section
            self.file = file
            self.size = size
            self.calls = Stack.Table([])
            self.returns = Stack.Table([])

        def __lt__(self, other):
            """Return self.address < other.address."""
            if self.file == other.file:
                return self.address < other.address
            return self.file < other.file

        def __gt__(self, other):
            """Return self.address > other.address."""
            if self.file == other.file:
                return self.address > other.address
            return self.file > other.file

        def __eq__(self, other):
            """Return self.address == other.address."""
            if self.file == other.file:
                return self.address == other.address
            return self.file == other.file

        def __le__(self, other):
            """Return self.address <= other.address."""
            if self.file == other.file:
                return self.address <= other.address
            return self.file <= other.file

        def __ge__(self, other):
            """Return self.address >= other.address."""
            if self.file == other.file:
                return self.address >= other.address
            return self.file >= other.file

        def __ne__(self, other):
            """Return self.address != other.address."""
            return not self.__eq__(other)

        def __repr__(self):
            """Return self.name."""
            if len(self.file):
                return "{}: {}".format(self.file, self.name)
            return self.name

    class Table:
        """The function database of a binary.

        Attributes:
            table (list(Stack.Function)): the list of the binary functions
            statistic:                    the operation code statistic
        """

        table = None
        statistic = None

        def __init__(self, table):
            """Create the object.

            Args:
                table (list(Stack.Function)): the list of the binary functions
            """
            self.table = table
            self.statistic = Stack.Statistic()

        def __contains__(self, item):
            """Return if the Table contains the function."""
            return self.find(item.address)

        def __delitem__(self, key):
            """Delete the item."""
            index = self.table.index(key)
            del self.table[index]

        def __getitem__(self, item):
            """Return the item."""
            return self.table.__getitem__(item)

        def __iter__(self):
            """Return the iterator."""
            return self.table.__iter__()

        def __len__(self):
            """Return the number of functions."""
            return len(self.table)

        def __repr__(self):
            """Return repr(self.table)."""
            return str(self.table)

        def __setitem__(self, key, value):
            """Set the item of with the key."""
            return self.table.__setitem__(key, value)

        def append(self, function):
            """Append a function.

            Args:
                function (Stack.Function): the function

            Returns:
                Stack.function: the function which was appended
            """
            self.table.append(function)
            return function

        # FIXME: This doesn't work for arm, because there are multiple system functions which has the address 0x0
        # Maybe we have to use the file name too?
        def find(self, address):
            """Search the function.

            Args:
                address (int): the function start address

            Returns:
                Stack.Function: the function
            """
            for function in self.table:
                if address == function.address:
                    return function

            return None

        def sort(self):
            """Sort the functions by Stack.Function.total with the largest value first."""
            self.table.sort(key=lambda node: node.total, reverse=True)

        def limit(self):
            """Return the largest Stack.Function.total value.

            Returns:
                int: the largest Stack.Function.total value
            """
            limit = 0

            for function in self.table:
                limit = max(limit, function.total)

            return limit
