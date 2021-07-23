#!/bin/bash

# Validate the stacklimit tool with "gcc -fstack-usage" with the architecture
# of the host machine

TESTS="tests/component/bubble_sort"
OUTPUT="recursion"
STACKLIMIT="stacklimit/main.py"

for test in ${TESTS}; do
    filenames="${test} ${test}.su"

    for filename in ${filenames}; do
        if [ -e "${filename}" ]; then
            echo "error: ${filename} already exists."
            exit 1
        fi
    done
done

for test in ${TESTS}; do
    # Filenames
    source="${test}.c"
    binary="${test}"
    stack_usage="${test}.su"

    # Compile the recursive test
    gcc -o ${binary} -fstack-usage -O0 ${source}

    # Calculate the stack size with stacklimit
    stack_size_stacklimit="$(${STACKLIMIT} --summary ${binary} | head -n 1)"

    # Calculate the stack size with "gcc -fstack-usage"
    ./${binary}

    let "stack_size_gcc=$(cut --fields=2 ${stack_usage} | tr '\n' ' '| sed -r 's/ / + /g') + 0"

    # Print the results
    echo "* ${test}:"
    echo "  stacklimit: ${stack_size_stacklimit} bytes"
    echo "  gcc:        ${stack_size_gcc} bytes"

    # Clean up
    rm -f "${binary}" "${stack_usage}"
done
