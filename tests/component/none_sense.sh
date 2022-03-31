#!/bin/bash

# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Validate the stacklimit tool with "gcc -fstack-usage" with the architecture
# of the host machine

OUTPUT="tests/component/none_sense"
STACKLIMIT="stacklimit/main.py"

# Filenames
source="${OUTPUT}.c"
call_stack="${OUTPUT}_call_stacks.txt"
binary="${OUTPUT}"
stack_usage="${OUTPUT}.su"

filenames="${binary} ${stack_usage}"

for filename in ${filenames}; do
    if [ -e "${filename}" ]; then
        echo "error: ${filename} already exists."
        exit 1
    fi
done

# Compile the recursive test
gcc -o ${binary} -fstack-usage -O0 ${source}

# Calculate the stack size with stacklimit
stack_size_stacklimit="$(${STACKLIMIT} --summary ${binary} | head -n 1)"

# Calculate the stack size with "gcc -fstack-usage"
./${binary}

stack_size_gcc=0

# Use the stack usage file as a mapping from function name to stack size of the
# function and replace the function names in the call stack file with the stack
# size
while read -r line ; do
    let "size=$line"
    # echo "${size} = ${line}"

    if [[ ${size} -gt ${stack_size_gcc} ]]; then
        stack_size_gcc=${size}
    fi
done < <(sed -r -e 's#.*:(.*)\s+(.*)\s+static#s/\\b\1\\b/\2/g#' ${stack_usage} \
    | sed -f - ${call_stack} \
    | grep -vE "^#|^$")

# Print the results
echo "* ${OUTPUT}:"
echo "  stacklimit: ${stack_size_stacklimit} bytes"
echo "  gcc:        ${stack_size_gcc} bytes"

# Clean up
rm -f "${binary}" "${stack_usage}"
