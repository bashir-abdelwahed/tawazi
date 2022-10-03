import logging
from time import sleep
from typing import Any

import pytest

from tawazi import DAG, ErrorStrategy, ExecNode

T = 0.001
# global comp_str
pytest.comp_str = ""


def a() -> None:
    sleep(T)
    pytest.comp_str += "a"


def b(a: Any) -> None:
    raise NotImplementedError


def c(b: Any) -> None:
    sleep(T)
    pytest.comp_str += "c"


def d(a: Any) -> None:
    sleep(T)
    pytest.comp_str += "d"


list_execnodes = [
    ExecNode(a, a, priority=1, is_sequential=False),
    ExecNode(b, b, [a], priority=2, is_sequential=False),
    ExecNode(c, c, [b], priority=2, is_sequential=False),
    ExecNode(d, d, [a], priority=1, is_sequential=False),
]


def test_strict_error_behavior() -> None:
    pytest.comp_str = ""
    g = DAG(list_execnodes, 1, behaviour=ErrorStrategy.strict, logger=logging.getLogger())
    try:
        g.execute()
    except NotImplementedError:
        pass


def test_all_children_behavior() -> None:
    pytest.comp_str = ""
    g = DAG(list_execnodes, 1, behaviour=ErrorStrategy.all_children, logger=logging.getLogger())
    g.execute()
    assert pytest.comp_str == "ad"


def test_permissive_behavior() -> None:
    pytest.comp_str = ""
    g = DAG(list_execnodes, 1, behaviour=ErrorStrategy.permissive, logger=logging.getLogger())
    g.execute()
    assert pytest.comp_str == "acd"


# todo test using argname for ExecNode
