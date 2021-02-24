#!/bin/bash

DIR="$(dirname "$PWD/$0")"
STACKLIMIT="$DIR/../stacklimit.py"
TEST_X86="$DIR/dep-x86"
TEST_X86_64="$DIR/dep-x86_64"
TEST_ARM="$DIR/dep-arm"
TEST_AARCH64="$DIR/dep-aarch64"

#SIZE_X86=0
SIZE_X86_64=336
SIZE_ARM=0
SIZE_AARCH64=0

#echo -n "test x86...      "
#result=$($STACKLIMIT -s -W $TEST_X86 2> /dev/null)
#if [[ $? -eq 10 && $result -eq $SIZE_X86 ]]; then
#    echo "OK"
#else
#    echo "FAILED"
#fi

echo -n "test x86_64...   "
result=$($STACKLIMIT -s -W $TEST_X86_64 2> /dev/null)
if [[ $? -eq 10 && $result -eq $SIZE_X86_64 ]]; then
    echo "OK"
else
    echo "FAILED"
fi

echo -n "test arm...      "
result=$($STACKLIMIT -s -W $TEST_ARM 2> /dev/null)
if [[ $? -eq 10 && $result -eq $SIZE_ARM ]]; then
    echo "OK"
else
    echo "FAILED"
fi

echo -n "test aarch64...  "
result=$($STACKLIMIT -s -W $TEST_AARCH64 2> /dev/null)
if [[ $? -eq 10 && $result -eq $SIZE_AARCH64 ]]; then
    echo "OK"
else
    echo "FAILED"
fi