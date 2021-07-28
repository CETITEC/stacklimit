#!/bin/python3
"""The entrance point when executing the tool from a shell."""

import argparse

from stacklimit import Stacklimit


def print_documentation():
    """Print the tool documentation."""
    # All printed lines are < 83 characters long.
    print(
        "STACK INSTRUCTION STATES\n"
        "        States how the instruction was detected and treated as a stack operation:\n"
        "        • clear:\n"
        "            stack instruction recognized and considered correctly\n"
        "\n"
        "            Note that only specific stack instructions will be counted, like those\n"
        "            operations which decrease the stack. Operations which increase it are\n"
        "            ignored.\n"
        "\n"
        '            (see also "potential stack operations")\n'
        "\n"
        "        • potential (pot.):\n"
        "            potential stack instruction recognized, but not considered\n"
        "\n"
        "            Some instructions might listed here which are already covered by\n"
        "            tracking the counter part like\n"
        "            • pop and push\n"
        "            • add and sub\n"
        "            • add x... and add -x...\n"
        "            or are recovered by using another opeartion like mov.\n"
        "\n"
        "        • weak:\n"
        "            stack instructions recognized, but cannot be considered correctly\n"
        "\n"
        "        • none (empty):\n"
        "            no stack instruction detected or expected\n"
        "\n"
        "DEBUG MESSAGE FORMATTING OF THE OBJDUMP PARSER\n"
        "                  +- state if the instruction was detected as a stack operation:\n"
        "                  |\n"
        "                  |     +- the sort of the detected stack operation\n"
        "                  |     |\n"
        "                  |     |                  +- how much the stack will grow\n"
        "                  |     |                  |\n"
        "                  |     |                  |    +- output of objdump\n"
        "                  |     |                  |    |\n"
        "        Debug:   clear StackSubOp       +  8B  4d0:	48 83 ec 08          	sub    $0x8,%rsp\n"
        "\n"
        "STACK TABLE\n"
        '        ">" indicates that the stack size can be bigger than calculated.\n'
        "\n"
        "        E.g. through dynamic stack operations or calling a function though a function\n"
        "        pointer which couldn't be resolved.\n"
        "\n"
        "         +- the start address of the function\n"
        "         |\n"
        "         |       +- the function name\n"
        "         |       |\n"
        "         |       |         +- the file the function is defined\n"
        "         |       |         |\n"
        "         |       |         |              +- bytes the function itself manipulates\n"
        "         |       |         |              |  the stack size\n"
        "         |       |         |              |\n"
        "         |       |         |              |     +- bytes the function with all\n"
        "         |       |         |              |     |  sub-functions manipulates the\n"
        "         |       |         |              |     |  stack size\n"
        "         |       |         |              |     |\n"
        "        address function  file           fsize tsize\n"
        "        0x008f9 main      dep-x86_64_O0     80  >480\n"
        "\n"
        "OPERATION STATISTIC\n"
        "         +- the instruction\n"
        "         |\n"
        "         |      +- number of calls\n"
        "         |      |\n"
        "         |      |    +- percentage of calls in relation to all function calls\n"
        "         |      |    |\n"
        "         |      |    |     +- state if the instruction was detected as a stack\n"
        "         |      |    |     |  operation\n"
        "         |      |    |     |\n"
        "        total  390  100%   |\n"
        "        call    30    8%  weak\n"
        "\n"
        "STACK IMPACTS STATISTIC\n"
        "         +- state how the instruction was detected and treated as a stack operation\n"
        "         |\n"
        "         |                              +- number of calls\n"
        "         |                              |\n"
        "         |                              |    +- percentage of calls in relation to\n"
        "         |                              |    |  all function calls\n"
        "         |                              |    |\n"
        "        total                          390  100%\n"
        "        clear                           66   17%\n"
        "        weak (unknown stack impact)      6    2%\n"
        "        skipped                        318   82%\n"
        "          potential stack instructions   0    0%\n"
        "          unexpected stack impact      318   82%\n"
    )


class DocumentationAction(argparse.Action):
    """The action class for printing the documentation."""

    def __init__(self, option_strings, dest=None, default=None, help=None):
        """Create the object."""
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        """Execute the action."""
        print_documentation()
        parser.exit()


def main():
    """Entry point for the command prompt."""
    parser = argparse.ArgumentParser(
        prog="stacklimit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Determine the maximum stack size of C.",
        epilog="Note: This script cannot handle recursive functions and function"
        " pointers!\n"
        "\n"
        "Exit status:    0  OK\n"
        "                1  input error\n"
        "                2  program error\n"
        "               10  see warnings\n"
        "              130  user abort the program",
    )
    parser.add_argument(
        "-D",
        "--documentation",
        action=DocumentationAction,
        help="print the tool documentation",
    )
    # TODO: Handle multiple binaries: nargs='+'
    parser.add_argument("binary", type=argparse.FileType("r"), help="the binary")
    parser.add_argument("-a", "--arch", help="the architecture of the target platform")
    parser.add_argument("-c", "--no-color", action="store_true", help="suppress color")
    parser.add_argument("-o", "--objdump", help="path to or name of the objdump")
    parser.add_argument(
        "-r",
        "--regard-all",
        action="store_true",
        help="regard initialization and termination code",
    )
    parser.add_argument(
        "-s", "--summary", action="store_true", help="only print the maximum stack size"
    )
    parser.add_argument("--show-header", action="store_true", help="show header line")
    parser.add_argument(
        "--show-section", action="store_true", help="show section column"
    )
    parser.add_argument(
        "--show-operation-statistic",
        action="store_true",
        help="show operation statistic",
    )
    parser.add_argument(
        "-t", "--tree", action="store_true", help="show function call tree"
    )
    parser.add_argument(
        "-w",
        "--no-duplicated-warnings",
        action="store_true",
        help="suppress duplicated warnings",
    )
    parser.add_argument(
        "-W", "--no-warnings", action="store_true", help="suppress warnings"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="show debug messages"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="only print warnings and errors"
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1")

    args = parser.parse_args()

    warn = not args.no_warnings
    multiple_warn = not args.no_duplicated_warnings
    color = not args.no_color

    try:
        stacklimit = Stacklimit(
            args.debug,
            warn,
            args.quiet,
            color,
            multiple_warn,
            args.regard_all,
            args.arch,
            args.objdump,
            args.binary.name,
        )
    except ValueError:
        exit(1)

    try:
        # TODO: Handle multiple binaries
        stacklimit.parse(args.binary.name)
        precise = stacklimit.calculate_stack()
        limit = stacklimit.get_stack_limit()

        if args.summary:
            print(limit)
        else:
            if args.tree:
                stacklimit.print_call_tree()
            else:
                stacklimit.print_stack_table(args.show_header, args.show_section)
            print()
            stacklimit.print_statistic(args.show_header, args.show_operation_statistic)
    except KeyboardInterrupt:
        exit(130)

    if not limit:
        exit(2)
    if not precise:
        exit(10)


if __name__ == "__main__":
    main()
