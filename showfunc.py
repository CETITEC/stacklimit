#!/bin/python3
"""
Print selected lines from objdump

@author Mortiz Lüdecke (CETITEC)
"""

import argparse
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

    # dir/binary:     file format elf64-x86-64
    FileFormat = '^.*:( |\t)*file format '

    # 000000000040076d <main>:
    def Function(name):
       return '^[0-9a-f]* \<' + name + '\>:$'


class ObjdumpParser:
    arch = None
    color = None

    readelf_path = None
    objdump_path = None

    def __init__(self, debug=False, color=False, arch=None, objdump=None, binary=None):
        self.debug = debug
        self.color = color

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
            supported = self._has_objdmup_support(binary)
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
            if origin == 'GNU' and self._has_objdmup_support(binary, objdump):
                self.objdump_path = objdump
                return True

            self._print(Message.DEBUG, '\'' + self._bold(objdump) + '\' doesn\'t support arch.')

        return False

    def _get_arch(self, binary):
        if not binary:
            return None

        cmd = [self.readelf_path, '-h', binary]
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode('utf-8')

        if output == '':
            self._print(Message.DEBUG, 'Couldn\'t read binary with readelf. Maybe the binary is not an ELF file.')
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

    def _has_objdmup_support(self, binary, objdump=None):
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

    def parse(self, binary, functions):
        current = None
        found = False
        printSpace = False

        objdump_cmd = [self.objdump_path, '-d', binary]
        objdump = subprocess.Popen(objdump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for line in objdump.stdout:
            line = line.decode('utf-8')[:-1]

            if not found:
                for function in functions:
                    if re.match(Pattern.Function(function), line):
                        found = True
                        break

                if not found:
                    continue

                if printSpace:
                    print()

            if line == '':
                printSpace = True
                found = False
                continue

            print(line)


def main():
    try:
        parser = argparse.ArgumentParser(prog='stacklimit',
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description='Show only selected assembler functions')
        parser.add_argument('binary', type=argparse.FileType('r'),
                            help='the binary')
        parser.add_argument('functions', nargs='+',
                            help='function names')
        parser.add_argument('-a', '--arch',
                            help='the architecture of the target platform')
        parser.add_argument('-c', '--no-color', action='store_true',
                            help='suppress color')
        parser.add_argument('-o', '--objdump',
                            help='path to or name of the objdump')
        parser.add_argument('-d', '--debug', action='store_true',
                            help='show debug messages')

        args = parser.parse_args()

        try:
            odparser = ObjdumpParser(args.debug, not args.no_color, args.arch, args.objdump, args.binary.name)
        except ValueError:
            exit(1)

        odparser.parse(args.binary.name, args.functions)

    except KeyboardInterrupt:
        exit(130)


if __name__ == '__main__':
    main()
