"""Test cases for methods and classes defined in stacklimit.py file."""

import itertools

import pytest

from stacklimit.datastructure import Stack, Visitor


def create_visitor(callstack, queue):
    """Create a visitor easily for the test cases below.

    Args:
        callstack (list[int]):   the callstack with addresses the visitor shall be
                                 initialized with
        queue (list[list[int]]): the queue with lists of addresses the visitor shall be
                                 initialized with
    """
    visitor = Visitor()

    visitor.callstack = [Stack.Function(address) for address in callstack]
    for calls in queue:
        visitor.queue.append([Stack.Function(address) for address in calls])

    return visitor


def test_visitor__init__with_none():
    """Test Visitor.__init__(None)."""
    visitor = Visitor(None)
    assert visitor.callstack == []
    assert visitor.queue == [[]]


def test_visitor__init__with_empty_list():
    """Test Visitor.__init__([])."""
    visitor = Visitor([])
    assert visitor.callstack == []
    assert visitor.queue == [[]]


def test_visitor__init__():
    """Test Visitor.__init__([1, 2, 3])."""
    entrances = [
        Stack.Function(1),
        Stack.Function(2),
        Stack.Function(3),
    ]
    visitor = Visitor(entrances)

    assert len(visitor.callstack) == 1
    assert visitor.callstack[0] in entrances

    assert len(visitor.queue) == 1
    assert len(visitor.queue[0]) == 2
    assert visitor.queue[0][0] in entrances
    assert visitor.queue[0][1] in entrances


@pytest.mark.parametrize(
    "callstack1, queue1, callstack2, queue2, expected",
    [
        # fmt: off
        ([],  [],         [],  [],         True),
        ([0], [[1]],      [0], [[1]],      True),
        ([0], [[1]],      [0], [[0]],      False),
        ([0], [[1]],      [1], [[1]],      False),
        ([0], [[1]],      [1], [[0]],      False),
        ([],  [[1, 2]],   [],  [[1, 2]],   True),
        ([],  [[1]],      [],  [[1, 2]],   False),
        ([],  [[1, 2]],   [],  [[1, 3]],   False),
        ([],  [[1], []],  [],  [[1], []],  True),
        ([],  [[1]],      [],  [[1], []],  False),
        ([],  [[1]],      [],  [[1], [1]], False),
        ([],  [[1], [2]], [],  [[1], [2]], True),
        ([],  [[1], [2]], [],  [[1], [3]], False),
        ([0], [],         [0], [],         True),
        ([0], [],         [0, 1], [],      False),
        # fmt: on
    ],
)
def test_visitor_equal(callstack1, queue1, callstack2, queue2, expected):
    """Test Visitor.__eq__() and  Visitor.__ne__()."""
    visitor1 = create_visitor(callstack1, queue1)
    visitor2 = create_visitor(callstack2, queue2)

    assert visitor1.__eq__(visitor2) == expected
    assert visitor1.__ne__(visitor2) == (not expected)


@pytest.fixture
def functions1():
    r"""Initialize a function set of 3 functions.

    It shall only initialize the call structure, but no logic of the visitor state like
    if the function was already visited.

        0
       / \
      1   2
    """
    functions = [Stack.Function(address) for address in list(range(3))]

    functions[0].calls = [functions[1], functions[2]]

    return functions


@pytest.fixture
def functions2():
    r"""Initialize a function set of 4 functions.

    It shall only initialize the call structure, but no logic of the visitor state like
    if the function was already visited.

         0
       / | \
      1  2  3
    """
    functions = [Stack.Function(address) for address in list(range(4))]

    functions[0].calls = [functions[1], functions[2], functions[3]]

    return functions


@pytest.fixture
def functions3():
    r"""Initialize a function set of 3 functions.

    It shall only initialize the call structure, but no logic of the visitor state like
    if the function was already visited.

      0
      |
      1
      |
      2
    """
    functions = [Stack.Function(address) for address in list(range(3))]

    functions[0].calls = [functions[1]]
    functions[1].calls = [functions[2]]

    return functions


@pytest.fixture
def functions4():
    r"""Initialize a function set of 5 functions.

    It shall only initialize the call structure, but no logic of the visitor state like
    if the function was already visited.

        0
       / \
      1   2
         / \
        3   4
    """
    functions = [Stack.Function(address) for address in list(range(5))]

    functions[0].calls = [functions[1], functions[2]]
    functions[2].calls = [functions[3], functions[4]]

    return functions


@pytest.mark.skip(reason="Fix the current implementation")
def test_visitor_down_with_empty_data():
    """Test Visitor.down() with empty Visitor.callstack and empty Visitor.queue."""
    visitor = Visitor()

    assert visitor.down() == None

    assert visitor.callstack == []
    assert visitor.queue == []


def test_visitor_down_with_two_unvisited_children(functions1):
    r"""Test Visitor.down() with two unvisited children.

    Before:  After:
      ->0        0
       / \      / \
      1   2    1 ->2
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0]]
    visitor.queue = [[]]

    assert visitor.down() == functions1[2]

    assert visitor.callstack == [functions1[0], functions1[2]]
    assert visitor.queue == [[], [functions1[1]]]


def test_visitor_down_with_three_unvisited_children(functions2):
    r"""Test Visitor.down() with three unvisited children.

    Before:    After:
       ->0          0
       / | \      / | \
      1  2  3    1  2->3
    """
    visitor = Visitor()
    visitor.callstack = [functions2[0]]
    visitor.queue = [[]]

    assert visitor.down() == functions2[3]

    assert visitor.callstack == [functions2[0], functions2[3]]
    assert visitor.queue == [[], [functions2[1], functions2[2]]]


def test_visitor_down_with_left_visited_child(functions1):
    r"""Test Visitor.down() with left child visited and right child unvisited.

    Before:  After:
      ->0        0
       / \      / \
      1*  2    1*->2
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0]]
    visitor.queue = [[]]

    functions1[1].visited = True

    assert visitor.down() == functions1[2]

    assert visitor.callstack == [functions1[0], functions1[2]]
    assert visitor.queue == [[]]


def test_visitor_down_with_right_visited_child(functions1):
    r"""Test Visitor.down() with left child unvisited and right child visited.

    Before:  After:
      ->0        0
       / \      / \
      1   2* ->1   2*
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0]]
    visitor.queue = [[]]

    functions1[2].visited = True

    assert visitor.down() == functions1[1]

    assert visitor.callstack == [functions1[0], functions1[1]]
    assert visitor.queue == [[]]


def test_visitor_down_with_visited_children(functions1):
    r"""Test Visitor.down() with visited children.

    Before:    After:
        ->0      ->0
         / \      / \
        1*  2*   1*  2*
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0]]
    visitor.queue = [[]]

    functions1[1].visited = True
    functions1[2].visited = True

    assert visitor.down() == functions1[0]

    assert visitor.callstack == [functions1[0]]
    assert visitor.queue == [[]]


def test_visitor_down_with_unvisited_child_and_grandchild(functions3):
    r"""Test Visitor.down() with an unvisited child and an unvisited grandchild.

    Before:    After:
    ->0          0
      |          |
      1          1
      |          |
      2        ->2
    """
    visitor = Visitor()
    visitor.callstack = [functions3[0]]
    visitor.queue = [[]]

    assert visitor.down() == functions3[2]

    assert visitor.callstack == [functions3[0], functions3[1], functions3[2]]
    assert visitor.queue == [[]]


def test_visitor_down_with_unvisited_parent_and_child(functions3):
    r"""Test Visitor.down() with an unvisited parent and an unvisited child.

    Before:    After:
      0          0
      |          |
    ->1          1
      |          |
      2        ->2
    """
    visitor = Visitor()
    visitor.callstack = [functions3[0], functions3[1]]
    visitor.queue = [[]]

    assert visitor.down() == functions3[2]

    assert visitor.callstack == [functions3[0], functions3[1], functions3[2]]
    assert visitor.queue == [[]]


@pytest.mark.skip(reason="Fix the current implementation")
def test_visitor_down_without_children(functions3):
    r"""Test Visitor.down() without any children.

    Before:    After:
      0          0
      |          |
      1          1
      |          |
    ->2        ->2
    """
    visitor = Visitor()
    visitor.callstack = [functions3[0], functions3[1], functions3[2]]
    visitor.queue = [[]]

    assert visitor.down() == None

    assert visitor.callstack == [functions3[0], functions3[1], functions3[2]]
    assert visitor.queue == [[]]


def test_visitor_down_complex1(functions4):
    r"""Test Visitor.down() with a complex structure.

    Before:    After:
      ->0          0
       / \        / \
      1   2      1   2
         / \        / \
        3   4      3 ->4
    """
    visitor = Visitor()
    visitor.callstack = [functions4[0]]
    visitor.queue = [[]]

    assert visitor.down() == functions4[4]

    assert visitor.callstack == [functions4[0], functions4[2], functions4[4]]
    assert visitor.queue == [[], [functions4[1]], [functions4[3]]]


def test_visitor_down_complex2(functions4):
    r"""Test Visitor.down() with a complex structure.

    Before:    After:
      ->0          0
       / \        / \
      1   2      1   2
         / \        / \
        3   4*   ->3   4*
    """
    visitor = Visitor()
    visitor.callstack = [functions4[0]]
    visitor.queue = [[]]

    functions4[4].visited = True

    assert visitor.down() == functions4[3]

    assert visitor.callstack == [functions4[0], functions4[2], functions4[3]]
    assert visitor.queue == [[], [functions4[1]]]


def test_visitor_up_with_empty_data():
    """Test Visitor.up() with empty Visitor.callstack and empty Visitor.queue."""
    visitor = Visitor()

    assert visitor.up() == None

    assert visitor.callstack == []
    assert visitor.queue == []


def test_visitor_up_with_unvisited_sibling(functions1):
    r"""Test Visitor.up() with an unvisited sibling.

    Before:  After:
        0        0
       / \      / \
    ->1   2    1 ->2
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0], functions1[1]]
    visitor.queue = [[], [functions1[2]]]

    assert visitor.up() == functions1[2]

    assert visitor.callstack == [functions1[0], functions1[2]]
    assert visitor.queue == [[]]


def test_visitor_up_with_visited_sibling1(functions1):
    r"""Test Visitor.up() with a visited sibling, visited by 0.

    Before:  After:
        0      ->0
       / \      / \
    ->1   2*   1   2*
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0], functions1[1]]
    visitor.queue = [[]]

    functions1[2].visited = True

    assert visitor.up() == functions1[0]

    assert visitor.callstack == [functions1[0]]
    assert visitor.queue == [[]]


@pytest.mark.skip(reason="Fix the current implementation")
def test_visitor_up_with_visited_sibling2(functions1):
    r"""Test Visitor.up() with a visited sibling, but not visited directly by 0.

    Before:  After:
        0      ->0
       / \      / \
    ->1   2*   1   2*
    """
    visitor = Visitor()
    visitor.callstack = [functions1[0], functions1[1]]
    visitor.queue = [[], functions1[2]]

    functions1[2].visited = True

    assert visitor.up() == functions1[0]

    assert visitor.callstack == [functions1[0]]
    assert visitor.queue == [[]]


def test_visitor_up_with_unvisited_parent_and_grandparent(functions3):
    r"""Test Visitor.up() with an unvisited parent and an unvisited grandparent.

    Before:    After:
      0          0
      |          |
      1        ->1
      |          |
    ->2          2
    """
    visitor = Visitor()
    visitor.callstack = [functions3[0], functions3[1], functions3[2]]
    visitor.queue = [[], [], []]

    assert visitor.up() == functions3[1]

    assert visitor.callstack == [functions3[0], functions3[1]]
    assert visitor.queue == [[], []]


def test_visitor_up_with_unvisited_parent_and_child(functions3):
    r"""Test Visitor.up() with an unvisited parent and an unvisited child.

    Before:    After:
      0        ->0
      |          |
    ->1          1
      |          |
      2          2
    """
    visitor = Visitor()
    visitor.callstack = [functions3[0], functions3[1]]
    visitor.queue = [[], []]

    assert visitor.up() == functions3[0]

    assert visitor.callstack == [functions3[0]]
    assert visitor.queue == [[]]


def test_visitor_up_without_parent(functions3):
    r"""Test Visitor.up() without a parent.

    Before:    After:
    ->0          0
      |          |
      1          1
      |          |
      2          2
    """
    visitor = Visitor()
    visitor.callstack = [functions3[0]]
    visitor.queue = [[]]

    assert visitor.up() == None

    assert visitor.callstack == []
    assert visitor.queue == []
