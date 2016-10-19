stacklimit
==========

Determines the maximum stack size of a binary program using the ELF format.

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

* `x86`
* `x86_64`


Requirements
------------

* **objdump**
* **elfread**

