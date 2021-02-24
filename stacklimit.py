#!/bin/python3
"""
Determines the maximum stack size of a binary program using the ELF format.

@author Mortiz Lüdecke (CETITEC)
"""

import argparse
from cmath import log
from os import listdir, environ
from os.path import isfile
import re
import subprocess

PATH = [path + '/' for path in ['.'] + environ["PATH"].split(':')]
MAX_NAME_LEN=64


def get_arch(arch):
    if not arch:
        return None

    arch = arch.lower().replace('-', '_')

    for supported_arch in Pattern.arch:
        if arch == supported_arch:
            return arch

        # To match also '80386' as x86 architecture
        if supported_arch[0] == 'x':
            temp = supported_arch[1:]
            if temp in arch and temp[-1] == arch[-1]:
                return supported_arch

    return None


# instruction [reg1[, reg2[, reg3 [...]]]]
def _operation(*args):
    op = '.*( |\t)+{}'.format(args[0])

    if len(args) > 1:
        op = '{}( |\t)+{}'.format(op, args[1])

    for arg in args[2:]:
        op = '{},( |\t)+{}'.format(op, arg)

    return op


class Color:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    DARK = '\033[90m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'


class MessageType:
    color = None
    prefix = None

    def __init__(self, prefix=None, color=None):
        self.color = color
        self.prefix = prefix


class Message:
    DEBUG = MessageType('Debug: ', Color.YELLOW)
    ERROR = MessageType('Error: ', Color.RED)
    INFO = MessageType()
    WARN = MessageType('Warning: ', Color.PURPLE)


class Pattern:
    arch = ['arm', 'aarch64',
            'x86', 'x86_64']
    os_functions = [
        'register_tm_clones',
        'deregister_tm_clones',
        'frame_dummy',
        'call_weak_fn',
        'abort@plt',
        '.plt',
        '_init',
        '_start',
        '_fini',
        '__libc_csu_init',
        '__libc_csu_fini',
        '__init_array_start',
        '__init_array_end',
        '__do_global_dtors_aux',
        '__do_global_dtors_aux_fini_array_entry',
        '__frame_dummy_init_array_entry',
        '__libc_start_main@plt',
        '__gmon_start__@plt']

    # dir/binary:     file format elf64-x86-64
    FileFormat = '^.*:( |\t)*file format '

    # Disassembly of section .text:
    Section = '^Disassembly of section .*:'

    # 000000000040076d <main>:
    Function = '^[0-9a-f]* \<.*\>:$'

    FunctionCall = None
    FunctionPointer = None
    StackDynamicOp = None
    StackPushOp = None
    StackSubOp = None

    @staticmethod
    def get_function(line):
        line_array = line.split(' ')
        address = int(line_array[0], 16)
        name = ' '.join(line_array[1:])[1:-2]

        return address, name

    @staticmethod
    def get_section(line):
        line_array = line.split(' ')
        name = line_array[-1][0:-1]

        return name


# ARM and Thumb instruction set
class arm(Pattern):
    arch = ['arm']

    #   1069c:   ebffff80        bl      104a4 <func_alpha>
    # TODO: Test cbz and cbnz
    FunctionCall = '(' + _operation('(b[a-z]{2}|blx|bl|b)(.n|)', '[0-9]+') \
                 + '|' + _operation('(cbz|cbnz)',                '[a-z]([a-z]|[0-9]+)', '[0-9]+') \
                 + ')'

    #   1031c:   e12fff13    bx  r3
    #   10344:   012fff1e    bxeq    lr
    #   10918:   e12fff33    blx r3
    FunctionPointer = '(' + _operation('(bx[a-z]{2}|bxj|blx|bx)', '[a-z]([a-z]|[0-9]+)') \
                    + '|' + _operation('bne(.w|w|s|)',            '(0x[0-9a-f]+|[0-9]+)') \
                    + ')'

    # TODO: Test stm*
    # TODO: push{cond}
    StackPushOp = '(' + _operation('push(|[a-z]{2})') \
                + '|' + _operation('stm(ia|ib|da|db)(.w|w|s|)', 'sp') \
                + ')'

    #   ad5e0a:   b0f8        sub   sp,  #480
    #   ad7620:   b093        sub   sp,  #76
    #   a31760:   e24dd01c    sub   sp,  sp, #28
    #   a31760:   e24dd01c    add   sp,  sp, #-28
    #   ad6e4e:   f5ad7d21    sub.w sp,  sp, #644
    #      4bc:   a9bc7bfd    stp   x29, x30, [sp,#-64]!
    #      894:   a9af7bfd    stp   x29, x30, [sp,#-272]!
    #     4610:   f81d0ffe    str        x30, [sp, #-48]!
    StackSubOp = '(' + _operation('stp', 'x[0-9]+', '[a-z]([a-z]|[0-9]+)', '\[sp, \#-(0x[0-9a-f]+|[0-9]+)\]') \
               + '|' + _operation('str(.w|w|s|)',   '[a-z]([a-z]|[0-9]+)', '\[sp, \#-(0x[0-9a-f]+|[0-9]+)\]') \
               + '|' + _operation('sub(.w|w|s|)',   'sp',                  'sp',            '\#(0x[0-9a-f]|[0-9]+)') \
               + '|' + _operation('add(.w|w|s|)',   'sp',                  'sp',            '\#-(0x[0-9a-f]|[0-9]+)') \
               + ')'

    @staticmethod
    def get_function_call(line):
        name = line.split('<')[1]
        name = name.split('>')[0]

        line = line.split(' <')[0]
        line = line.replace('\t', ' ')
        line = line.replace('  ', ' ')
        line_array = line.split(' ')
        address = int(line_array[-1], 16)

        return address, name

    @staticmethod
    def get_stack_push_count(line):
        # TODO: push {r0,r4-r7}
        temp = line.split('{')[-1]
        temp = temp.split('}')[0]
        return temp.count(',') + 1

    @staticmethod
    def get_stack_push_size(line):
        return 4 * arm.get_stack_push_count(line)

    @staticmethod
    def get_stack_sub_size(line):
        temp = line.split('#')[-1]
        temp = temp.split('\n')[0]
        temp = temp.split('\t')[0]
        temp = temp.split(' ')[0]
        if temp[0] == '-':
            temp = temp[1:]
        return temp


class aarch64(arm):
    arch = ['aarch64']

    @staticmethod
    def get_stack_push_size(line):
        return 8 * arm.get_stack_push_count(line)

    @staticmethod
    def get_stack_sub_size(line):
        temp = line.split('#')[-1]
        temp = temp.split(']')[0]
        if temp[0] == '-':
            temp = temp[1:]
        return temp


class x86(Pattern):
    arch = ['x86']

    #   400734:       e8 b0 fe ff ff          callq  4005e9 <function_e>
    FunctionCall = '^( )*[0-9a-f]*:( |\t|[0-9a-f])+callq  [0-9a-f]+ \<.*\>$'

    #   400804:   ff d0                   callq  *%rax
    FunctionPointer = '^( )*[0-9a-f]*:( |\t|[0-9a-f])+callq  .*%.*$'

    #   XXXXXX:   YY YY YY YY             add     0xff,%rsp
    #   XXXXXX:   YY YY YY YY             sub     0xef,%rsp
    StackDynamicOp = '.*( |\t)+sub( |\t)+\%.*,\%(e|r)sp$'

    #   4004c3:   55                      push   %esp
    #   4004c3:   55                      push   %rsp
    StackPushOp = '.*( |\t)+push(l|)( |\t)+'

    #   4004aa:   48 83 ec 10             sub    $0x10,%rsp
    StackSubOp = '.*( |\t)+sub( |\t)+\$0x[0-9a-f]*,\%(e|r)sp$'

    @staticmethod
    def get_function_call(line):
        line = line.replace('\t', ' ')
        line = line.replace('  ', ' ')
        line_array = line.split(' ')
        address = int(line_array[-2], 16)
        name = line_array[-1][1:-1]

        return address, name

    @staticmethod
    def get_stack_push_size(line):
        return 4

    @staticmethod
    def get_stack_sub_size(line):
        temp = line.split(' ')[-1]
        return temp.split(',')[0][1:]


class x86_64(x86):
    arch = ['x86_64']

    #   4004c3:   55                      push   %esp
    #   4004c3:   55                      pushq  %rbp
    StackPushOp = '.*( |\t)+push(q|)( |\t)+'

    @staticmethod
    def get_stack_push_size(line):
        return 8


class Visitor:
    callstack = []
    queue = []

    def __init__(self, entrances):
        if entrances:
            self.callstack = [entrances[-1]]
            self.queue = [entrances[:-1]]

    def down(self):
        next_call = self.callstack[-1]
        calls = [child for child in next_call.calls if not child.visited]

        while calls:
            next_call = calls.pop()

            if next_call in self.callstack:
                self.callstack.append(next_call)
                break

            self.callstack.append(next_call)

            if calls:
                self.queue.append(calls)

            calls = [child for child in next_call.calls if not child.visited]

        return self.callstack[-1]

    def up(self):
        if self.callstack:
            self.callstack.pop()

        tier = len(self.callstack)

        if tier < len(self.queue):
            if self.queue[tier]:
                self.callstack.append(self.queue[tier].pop())

            if not self.queue[tier]:
                del(self.queue[tier])

        if len(self.callstack):
            return self.callstack[-1]

        return None


class Stack:
    class Function:
        address = None
        name = None
        file = None
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

        def __init__(self, address=None, name=None, section=None, file=None, size=0):
            self.address = address
            if len(name) > MAX_NAME_LEN:
                name = name[:MAX_NAME_LEN - 3] + '...'
            self.name = name
            self.section = section
            self.file = file
            self.size = size
            self.calls = Stack.Table([])
            self.returns = Stack.Table([])

        def __lt__(self, other):
            return self.address < other.address

        def __gt__(self, other):
            return self.address > other.address

        def __eq__(self, other):
            if other is None:
                return False
            return self.address == other.address

        def __le__(self, other):
            return self.address <= other.address

        def __ge__(self, other):
            return self.address >= other.address

        def __ne__(self, other):
            return self.address != other.address

        def __repr__(self):
            return self.name

    class Table:
        table = None

        def __init__(self, table):
            self.table = table

        def __contains__(self, item):
            return self.find(item.address)

        def __delitem__(self, key):
            index = self.table.index(key)
            del(self.table[index])

        def __getitem__(self, item):
            return self.table.__getitem__(item)

        def __iter__(self):
            return self.table.__iter__()

        def __len__(self):
            return len(self.table)

        def __missing__(self, key):
            return self.table.__missing__(key)

        def __repr__(self):
            return str(self.table)

        def __setitem__(self, key, value):
            return self.table.__setitem__(key, value)

        def append(self, function):
            self.table.append(function)
            return function

        # FIXME: This doesn't work for arm, because there are multiple system functions which has the address 0x0
        def find(self, address):
            for function in self.table:
                if address == function.address:
                    return function

            return None

        def sort(self):
            self.table.sort(key=lambda node: node.total, reverse=True)

        def limit(self):
            limit = 0

            for function in self.table:
                limit = max(limit, function.total)

            return limit


class Stacklimit:
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

    def __init__(self, debug=False, warn=True, quiet=False, color=False, multiple_warn=True, regard_os_functions=True,
                 arch=None, objdump=None, binary=None):
        self.debug = debug
        self.color = color
        self.quiet = quiet
        self.warn = warn
        self.warn_cycle = warn
        self.warn_fp = warn
        self.warn_dynamic = warn
        self.multiple_warn = multiple_warn
        self.regard_os_functions = regard_os_functions
        self.stacktable = Stack.Table([Stack.Function(address=0, name='Function Pointer')])

        self.readelf_path = self._get_tool_path('readelf')
        self._init_arch(arch, binary)
        self._init_objdump(binary, objdump)

    def _init_arch(self, arch, binary):
        if not arch:
            self._print(Message.DEBUG, 'Determinate platform from binary...')
            arch = self._get_arch(binary)

            if not arch:
                self._print(Message.ERROR, 'Couldn\'t determinate platform.\n'
                                           'Use \'' + self._bold('-a') + '\' or \'' + self._bold('--arch') + '\''
                                           'to define the platform.')
                raise ValueError()

        if arch not in Pattern.arch:
            self._print(Message.ERROR, 'Unsupported platform \'' + arch + '\'.\n'
                                       'Supported platforms are: ', end='')
            for arch in Pattern.arch[:-2]:
                self._print(Message.INFO, arch, end=', ', prefix='')
            self._print(Message.INFO, Pattern.arch[-2] + ' and ' + Pattern.arch[-1] + '.\n', prefix='')
            raise ValueError()

        self._print(Message.DEBUG, 'Using architecture ' + self._bold(arch))
        self.arch = arch

    def _init_objdump(self, binary, objdump=None):
        self._print(Message.DEBUG, 'Determinate objdump support for architecture ' + self._bold(self.arch) + '...')

        if objdump:
            self.objdump_path = self._get_tool_path(objdump)
            supported = self._has_objdump_support(binary)
        else:
            supported = self._find_objdump(binary)

        if not supported:
            self._print(Message.ERROR,
                        'Your objdump doesn\'t support the architecture ' + self._bold(self.arch) + '.')
            if not objdump:
                self._print(Message.ERROR, 'Use \'' + self._bold('-o') + '\' or \'' + self._bold('--objdump') + '\''
                                           'to specify the objdump binary.', prefix='')
            raise ValueError()

        self._print(Message.DEBUG, 'Using \'' + self._bold(self.objdump_path) + '\'')

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
        objdumps = [dir + file for dir in PATH for file in listdir(dir) if file.endswith('objdump')]

        self._print(Message.DEBUG, 'Search compatible objdump...')

        for objdump in objdumps:
            cmd = [objdump, '--version']
            output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                                      ).communicate()[0].decode('utf-8')

            if output == '':
                self._print(Message.DEBUG, 'Couldn\'t get version from \'' + self._bold(objdump) + '\'.')
                continue

            origin = output.split(' ')[0]
            # Add support for llvm-objdump
            if origin == 'GNU' and self._has_objdump_support(binary, objdump):
                self.objdump_path = objdump
                return True

            self._print(Message.DEBUG, '\'' + self._bold(objdump) + '\' doesn\'t support arch.')

        return False

    def _get_arch(self, binary):
        arch = self._get_arch_with_readelf(binary)
        if not arch:
            # Since the initramfs is not really an ELF file we have to use objdump
            arch = self._get_arch_with_objdump(binary)

        if not arch:
            self._print(Message.DEBUG, 'Maybe the binary is not an ELF file.')

        return arch

    def _get_arch_with_objdump(self, binary):
        if not binary:
            return None

        if not self._find_objdump(binary):
            return None

        cmd = [self.objdump_path, '-a', binary]
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode('utf-8')

        if output == '':
            self._print(Message.DEBUG, 'Couldn\'t read binary with objdump.')
            return None

        output_array = output.split('file format ')

        if len(output_array) < 2:
            self._print(Message.DEBUG, 'Couldn\'t find \'' + self._bold('file format') + '\' in output of objdump. '
                                       'Maybe the syntax has changed.')
            return None

        output = output_array[1]
        output = output.split('\n')[0]

        return get_arch(output)

    def _get_arch_with_readelf(self, binary):
        if not binary:
            return None

        cmd = [self.readelf_path, '-h', binary]
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode('utf-8')

        if output == '':
            self._print(Message.DEBUG, 'Couldn\'t read binary with readelf.')
            return None

        output_array = output.split('Machine:')

        if len(output_array) < 2:
            self._print(Message.DEBUG, 'Couldn\'t find \'' + self._bold('Machine') + '\' in output of readelf. '
                                       'Maybe the syntax has changed.')
            return None

        output = output_array[1]
        output = output.split('\n')[0]
        output = output.split(' ')[-1]

        return get_arch(output)

    def _get_tool_path(self, tool):
        for dir in [''] + PATH:
            path = dir + tool
            if isfile(path):
                return path

        self._print(Message.ERROR, 'Couldn\'t find \'' + self._bold(tool) + '\'')
        raise ValueError()

    def _has_objdump_support(self, binary, objdump=None):
        if not binary:
            return False

        if not objdump:
            objdump = self.objdump_path

        cmd = [objdump, '-d', '--stop-address=0', binary]
        returncode = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return returncode == 0

    def _print(self, kind, *objects, sep=' ', end='\n', prefix=True):
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
                print(text, end='')
            print(*objects, sep=sep, end=end)

    def _print_call_branch(self, function, path=[]):
        indent = 3 * (len(path) - 1)
        alight = function in path

        self._print_call_node(function, indent, alight)

        if not alight:
            for calls in function.calls:
                self._print_call_branch(calls, path + [function])

    def _print_call_node(self, function, indent=0, alight=False):
        arrow = '-> ' if function.returns else ''
        prefix = ''
        suffix = ''

        if function.address == 0:
            address = self._bold('Unknown')
            name = 'Function Pointer'
            if self.color:
                name = Color.RED + name + Color.END
        else:
            address = self._bold(hex(function.address))
            name = self._func(function.name)

        total = self._bold(str(function.total))
        size = str(function.size)
        size = self._dark('(' + size + ')')

        if function.imprecise:
            total = '>' + total

        info = address + ' ' + name + ' ' + total
        if not alight and not function.dynamic and function.address != 0:
            info += ' ' + size

        if function.cycle and alight:
            suffix += ' CIRCLE'
        if function.dynamic:
            suffix += ' DYNAMIC'
        if self.color and suffix != '':
            suffix = Color.RED + suffix + Color.END

        if self.color and (suffix != '' or function.cycle):
            arrow = Color.RED + arrow + Color.END

        if indent > 0:
            prefix = '{:{}}'.format('', indent)

        prefix += arrow

        self._print(Message.INFO, '{}{}{}'.format(prefix, info, suffix))

    def _print_cycle_warn(self, callstack):
        current = callstack[-1]
        start = callstack.index(current)

        if self.multiple_warn:
            self._print(Message.WARN, 'Found cycle in call graph entering with \'' + self._func(current.name) + '\'')
        else:
            self._print(Message.WARN, 'Found cycles in call graph')

        if self.debug and self.warn_cycle:
            path_string = [self._func(call.name) for call in callstack]
            if self.color:
                path_string[start] = Color.RED + current.name + Color.END
                path_string[-1] = Color.RED + current.name + Color.END

            self._print(Message.DEBUG, '  ', end='')

            for calls in path_string:
                self._print(Message.DEBUG, calls, end=' -> ', prefix=False)

            self._print(Message.DEBUG, '...', prefix=False)

    def _regard_function(self, function):
        if function.address == 0:
            return False

        if self.regard_os_functions:
            return True

        return function.section == '.text' and function.name not in Pattern.os_functions

    def _handle_dynamic(self, callstack):
        current = callstack[-1]

        if not current.dynamic:
            return

        for node in callstack[:-1]:
            node.imprecise = True

        if self.warn_dynamic:
            self.warn_dynamic = self.multiple_warn
            if self.multiple_warn:
                self._print(Message.WARN, 'Dynamic stack operation in function \'' + self._func(current.name) + '\'')
            else:
                self._print(Message.WARN, 'Found dynamic stack operations')

    def _handle_function_pointer(self, callstack):
        current = callstack[-1]

        if not [child for child in current.calls if child.address == 0]:
            return

        for node in callstack[:-1]:
            node.imprecise = True
        if self.warn_fp:
            self.warn_fp = self.multiple_warn
            if self.multiple_warn:
                self._print(Message.WARN, 'Function \'' + self._func(current.name) + '\' calls a function pointer')
            else:
                self._print(Message.WARN, 'Found function pointers')

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
        '''
        :callstack: the function which have to called to reach the current function
        :queue: contains functions of each function in callstack. The first array contains functions which have to
                handle after the first function in callstack has been done. The second array in the queue includes the
                functions which have to handle after the second function in the callstack has been done...
        '''

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
        current = None
        file = None

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

        objdump_cmd = [self.objdump_path, '-d', binary]
        objdump = subprocess.Popen(objdump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        section = None

        for line in objdump.stdout:
            line = line.decode('utf-8')[:-1]

            if re.match(pattern.FileFormat, line):
                line_array = line.split(' ')
                path = line_array[0][:-1]
                file = path.split('/')[-1]

            if re.match(pattern.Section, line):
                section = pattern.get_section(line)
                self._print(Message.DEBUG)
                self._print(Message.DEBUG, 'Disassembly of section {}:'.format(section))

            elif re.match(pattern.Function, line):
                (address, name) = pattern.get_function(line)
                current = self.stacktable.find(address)

                if current:
                    current.file = file
                    current.section = section
                else:
                    current = self.stacktable.append(Stack.Function(address=address, name=name, section=section, file=file))

                current.visited = True
                self._print(Message.DEBUG, '{}:'.format(name))

            elif pattern.StackPushOp and re.match(pattern.StackPushOp, line):
                self._print(Message.DEBUG, '  StackPushOp    ', line)
                size = pattern.get_stack_push_size(line)
                current.size += size

            # Note: We ignore all 'add' operations. We're only interested in 'sub'.
            elif pattern.StackSubOp and re.match(pattern.StackSubOp, line):
                self._print(Message.DEBUG, '  StackSubOp     ', line)
                temp = pattern.get_stack_sub_size(line)
                if temp[:2] == '0x':
                    size = int(temp, 16)
                else:
                    size = int(temp)

                # TODO: Rewrite this
                if size > 0xf000000000000000:
                    continue

                if size > 0xf0000000:
                    size = -size
                    size += 0x80000000
                    size += 0x80000000

                if size > 0x10000000:
                    continue

                current.size += size

            elif pattern.StackDynamicOp and re.match(pattern.StackDynamicOp, line):
                current.dynamic = True

            elif pattern.FunctionCall and re.match(pattern.FunctionCall, line):
                self._print(Message.DEBUG, '  FunctionCall   ', line)

                (address, name) = pattern.get_function_call(line)
                function = self.stacktable.find(address)

                if not function:
                    function = self.stacktable.append(Stack.Function(address=address, name=name))

                if not current.calls.find(address):
                    current.calls.append(function)
                    function.returns.append(current)

            elif pattern.FunctionPointer and re.match(pattern.FunctionPointer, line):
                self._print(Message.DEBUG, '  FunctionPointer', line)

                function_pointer = self.stacktable.find(0)
                current.calls.append(function_pointer)
                function_pointer.returns.append(current)

        for function in [function for function in self.stacktable if not function.visited and function.address != 0]:
            address = self._bold(hex(function.address))
            name = self._func(function.returns[0].name)
            self._print(Message.DEBUG, 'Ignore inner FunctionCall in {} to {} ({})'.format(name,
                                                                                           address,
                                                                                           function.name))
            del(self.stacktable[function])
            for caller in function.returns:
                del(caller.calls[function])

        for function in self.stacktable:
            function.visited = False

    def get_stack_limit(self):
        return self.stacktable.limit()

    def print_stack_table(self, show_header=False, show_section=False):
        # Should never happen
        if not self.stacktable:
            return

        address_len = 0xfffff if show_header else 1
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

        if show_header:
            section = 'section '
            if not show_section:
                section = ''
                section_len = 0

            self._print(Message.INFO, '{:>{}} {:<{}}  {:<{}}{:<{}}  {:>{}} {:>{}}'.format('address',  address_len,
                                                                                          'function', name_len,
                                                                                          section,    section_len,
                                                                                          'file',     file_len,
                                                                                          'fsize',    size_len,
                                                                                          'tsize',    total_len))

        self.stacktable.sort()

        for function in self.stacktable:
            if self._regard_function(function):
                address = self._bold('{:#0{width}x}'.format(function.address, width=address_len))
                name = self._func('{:{width}}'.format(function.name, width=name_len))
                section = ''
                file = function.file if function.file else ''
                file = self._dark('{:{width}}'.format(file, width=file_len))
                size = '{:{width}}'.format(function.size, width=size_len)
                # Workaround for text with color
                total = self._bold(str(function.total))
                imprecise = '>' if function.imprecise else ' '
                total_prefix_len = total_len - int(log(function.total + 1, 10).real) - 1
                total = '{:>{width}}{}'.format(imprecise, total, width=total_prefix_len)

                if show_section:
                    section = function.section if function.section else ''
                    section = self._dark('{:{width}}'.format(section, width=section_len))
                    section = section + ' '

                self._print(Message.INFO, '{} {}  {}{}  {} {}'.format(address, name, section, file, size, total))

    def print_call_tree(self):
        for top in self.stacktable:
            if not top.returns and self._regard_function(top):
                self._print_call_branch(top)


def main():
    parser = argparse.ArgumentParser(prog='stacklimit',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Determine the maximum stack size of C.',
                                     epilog='Note: This script cannot handle recursive functions and function'
                                            'pointers!\n'
                                             'Exit status:    0  OK\n'
                                             '                1  input error\n'
                                             '                2  program error\n'
                                             '               10  see warnings\n'
                                             '              130  user abort the program')
    # TODO: Handle multiple binaries: nargs='+'
    parser.add_argument('binary', type=argparse.FileType('r'),
                        help='the binary')
    parser.add_argument('-a', '--arch',
                        help='the architecture of the target platform')
    parser.add_argument('-c', '--no-color', action='store_true',
                        help='suppress color')
    parser.add_argument('-o', '--objdump',
                        help='path to or name of the objdump')
    parser.add_argument('-r', '--regard-all', action='store_true',
                        help='regard initialization and termination code')
    parser.add_argument('-s', '--summary', action='store_true',
                        help='only print the maximum stack size')
    parser.add_argument('--show-header', action='store_true',
                        help='show header line')
    parser.add_argument('--show-section', action='store_true',
                        help='show section column')
    parser.add_argument('-t', '--tree', action='store_true',
                        help='show function call tree')
    parser.add_argument('-w', '--no-duplicated-warnings', action='store_true',
                        help='suppress duplicated warnings')
    parser.add_argument('-W', '--no-warnings', action='store_true',
                        help='suppress warnings')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='show debug messages')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='only print warnings and errors')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')

    args = parser.parse_args()

    warn = not args.no_warnings
    mult_warn = not args.no_duplicated_warnings
    color = not args.no_color

    try:
        sl = Stacklimit(args.debug, warn, args.quiet, color, mult_warn, args.regard_all,
                        args.arch, args.objdump, args.binary.name)
    except ValueError:
        exit(1)

    try:
        # TODO: Handle multiple binaries
        sl.parse(args.binary.name)
        precise = sl.calculate_stack()
        limit = sl.get_stack_limit()

        if args.summary:
            print(limit)
        elif args.tree:
            sl.print_call_tree()
        else:
            sl.print_stack_table(args.show_header, args.show_section)
    except KeyboardInterrupt:
        exit(130)

    if not limit:
        exit(2)
    if not precise:
        exit(10)


if __name__ == '__main__':
    main()
