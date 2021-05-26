stacklimit
==========

Determines the maximum stack size of a binary program using the ELF format.

The logic is very simple. This tool just parse the assembler code and notes all
subtraction operations on the stack. Additionally it builds an function call
graph based on the knowledge of the assembler code which function is calling the
respective subfunction. After that the tool calculates the stack size for each
function including the stack size of the subfunction with the biggest stack
size.


*Note*: You can disable the color mode to parse the output for scripts. There
are also exit codes for each Warning and Error type.


Features
--------

* Function call tree
* Detection of recursive function calls (cycles)
* Detection of dynamic stack operations
* Detection of function pointers


Supported Architectures
-----------------------

* `arm`
* `aarch64`
* `x86`
* `x86_64`


Requirements
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
