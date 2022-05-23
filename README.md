stacklimit
==========

A static analyzer, which determines the maximum stack size of an executable or
library using the ELF format.

stacklimit is a standalone python script, which parses the object file of the
provided binary by using objdump. During parsing it stacklimit will create a
call graph with the changed stack size per function. The changed stack size is
determined via operations which can decrease the stack pointer and therefore may
increase the used stack.

After that stacklimit will calculate the total stack size by traveling through
the call graph and summarize the stack size of each function including the
sub-function, which increases the stack the most.

stacklimit was highly influenced by the Perl script [checkstack.pl](https://github.com/torvalds/linux/blob/28596c9722289b2f98fa83a2e4351eb0a031b953/scripts/checkstack.pl) of the [Linux kernel](https://www.kernel.org).


Example
-------

To analyze the compilation of `test/dep.c`, just execute stacklimit with the
path to the binary:
```
$ stacklimit tests/dep-x86_64
Warning: Found cycle in call graph entering with 'rec_xi'
Warning: Found cycle in call graph entering with 'rec_psi'
Warning: Function 'main' calls a function pointer

0x4007a5 main                   dep-x86_64  80 >480
0x40066d func_epsilon           dep-x86_64  96  400
0x4005e9 func_delta             dep-x86_64  80  304
0x40058b func_gamma             dep-x86_64  64  224
0x400556 func_beta              dep-x86_64  48  160
0x40051a func_alpha             dep-x86_64  40  112
0x400787 rec_psi                dep-x86_64  32  >96
0x4004f0 func_alpha2            dep-x86_64  40   72
0x400769 rec_chi                dep-x86_64  32  >64
0x4004ce func_alpha3            dep-x86_64  24   32
0x400718 rec_xi                 dep-x86_64  32  >32
0x40073e rec_phi                dep-x86_64  32  >32
0x4004b1 func_omega             dep-x86_64  16   24
0x4004a6 func_omega2            dep-x86_64   8    8
0x4004bc func_alpha4            dep-x86_64   8    8

total                          392  100%
clear                           67   17%
weak (unknown stack impact)      5    1%
skipped                        320   82%
  potential stack instructions   0    0%
  unexpected stack impact      320   82%
```

For further information execute stacklimit with `--help` or `--documentation`.


Features
--------

* Function call tree
* Detection of recursive function calls (cycles)
* Detection of dynamic stack operations
* Detection of indirect calls (function pointers)


Supported Architectures
-----------------------

* `arm`
* `aarch64`
* `x86`
* `x86_64`


Dependencies
------------

* **objdump** (gcc)
* **readelf**
* **python** >= `3.6`


Build
-----

To build the sources and wheels archives, use [Poetry](https://python-poetry.org):
```
poetry build
```


Development
-----------

To run all checks like the code formatter and all unit tests just execute
```
poetry run pre-commit run --all-files
```

To run those checks automatically when creating a new commit, just configure
`pre-commit` within the project folder with
```
poetry run pre-commit install
```

Tools:
* [Poetry](https://python-poetry.org): build tool
* [black](https://pypi.org/project/black): code formatter
* [isort](https://pypi.org/project/isort): imports sorter
* [pre-commit](https://pypi.org/project/pre-commit): pre-commit hooks for git
* [pydocstyle](https://pypi.org/project/pydocstyle): docstring style checker
* [pytest](https://pypi.org/project/pytest): testing
* [pytest-cov](https://pypi.org/project/pytest-cov): coverage

To install all develop dependencies, use [Poetry](https://python-poetry.org):
```
poetry install
```

Unit tests
----------

For testing the framework pytest is used.

To run all tests, just execute
```
poetry run pytest
```

To print the coverage, too, run
```
poetry run pytest --cov=stacklimit
```

And to generate a coverage report in XML, which can be used further, run
```
poetry run pytest --cov=stacklimit --cov-report=xml tests
```


Component tests
---------------

To run component tests execute
```
poetry run tests/component/misc.sh
poetry run tests/component/none_sense.sh
poetry run tests/component/recursion.sh
```

LICENSE
-------

Copyright (C) 2022 CETITEC GmbH.

Free use of this software is granted under the terms of the GNU General
Public License version 2 (GPLv2).
