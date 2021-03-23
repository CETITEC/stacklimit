#!/bin/python3
"""The entrance point when executing the tool from a shell."""

import argparse

from stacklimit import Stacklimit


def main():
    """Entry point for the command prompt."""
    parser = argparse.ArgumentParser(
        prog="stacklimit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Determine the maximum stack size of C.",
        epilog="Note: This script cannot handle recursive functions and function"
        "pointers!\n"
        "Exit status:    0  OK\n"
        "                1  input error\n"
        "                2  program error\n"
        "               10  see warnings\n"
        "              130  user abort the program",
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
    mult_warn = not args.no_duplicated_warnings
    color = not args.no_color

    try:
        sl = Stacklimit(
            args.debug,
            warn,
            args.quiet,
            color,
            mult_warn,
            args.regard_all,
            args.arch,
            args.objdump,
            args.binary.name,
        )
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


if __name__ == "__main__":
    main()
