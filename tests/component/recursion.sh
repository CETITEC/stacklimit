#!/bin/bash

# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Validate the stacklimit tool with "gcc -fstack-usage" with the architecture
# of the host machine

SIZE="50 100 500 1000"
OUTPUT="recursion"
STACKLIMIT="stacklimit/main.py"
GENERATOR="tests/component/generate-recursion.sh"

for size in ${SIZE}; do
    filenames="${OUTPUT}_${size}.c ${OUTPUT}_${size} ${OUTPUT}_${size}.su"

    for filename in ${filenames}; do
        if [ -e "${filename}" ]; then
            echo "error: ${filename} already exists."
            exit 1
        fi
    done
done

for size in ${SIZE}; do
    # Filenames
    source="${OUTPUT}_${size}.c"
    binary="${OUTPUT}_${size}"
    stack_usage="${OUTPUT}_${size}.su"

    # Generate and compile the recursive test
    ${GENERATOR} ${size} ${source}
    gcc -o ${binary} -fstack-usage -O0 ${source}

    # Calculate the stack size with stacklimit
    stack_size_stacklimit="$(${STACKLIMIT} --summary ${binary} | head -n 1)"

    # Calculate the stack size with "gcc -fstack-usage"
    ./${binary}

    let "stack_size_gcc=$(cut --fields=2 ${stack_usage} | tr '\n' ' '| sed -r 's/ / + /g') + 0"

    # Print the results
    echo "* ${size} recursions:"
    echo "  stacklimit: ${stack_size_stacklimit} bytes"
    echo "  gcc:        ${stack_size_gcc} bytes"

    # Clean up
    rm -f "${source}" "${binary}" "${stack_usage}"
done
