#!/bin/bash

# SPDX-FileCopyrightText: 2022 CETITEC GmbH <https://www.cetitec.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

# This component test shall test if the result calculated by stacklimit will
# increase with the same multiple than the called nested functions.


if [[ $# -ne 2 ]]; then
    echo "usage: $0 RECURSIONS FILENAME"
    exit 1
fi

RECURSIONS=$1
OUTPUT=$2

if [ -e ${OUTPUT} ]; then
    echo "error: ${OUTPUT} already exists."
    exit 1
fi

if [ ${RECURSIONS} -lt 1 ]; then
    echo "error: RECURSIONS must be bigger than 0."
    exit 1
fi

echo "#include <stdint.h>

int64_t __attribute__ ((noinline)) recursive1() {
    return 0;
}" >> ${OUTPUT}

for ((i=2; i <= ${RECURSIONS}; i++)); do
    let next=$i-1
    echo "
int64_t __attribute__ ((noinline)) recursive$i() {
    return recursive${next}();
}" >> ${OUTPUT}
done

echo "
int64_t main(int argc, int** argv) {
    return recursive${RECURSIONS}();
}" >> ${OUTPUT}
