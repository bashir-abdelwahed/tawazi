from time import sleep
from typing import Any

import pytest

from tawazi import op, to_dag

pytest.compound_priority_str = ""
T = 1e-3


@op(priority=1)
def a() -> None:
    sleep(T)
    pytest.compound_priority_str = str(pytest.compound_priority_str) + "a"


@op(priority=1)
def b(a: Any) -> None:
    sleep(T)
    pytest.compound_priority_str = str(pytest.compound_priority_str) + "b"


@op(priority=1)
def c(a: Any) -> None:
    sleep(T)
    pytest.compound_priority_str = str(pytest.compound_priority_str) + "c"


@op(priority=1)
def d(b: Any) -> None:
    sleep(T)
    pytest.compound_priority_str = str(pytest.compound_priority_str) + "d"


@op(priority=1)
def e() -> None:
    sleep(T)
    pytest.compound_priority_str = str(pytest.compound_priority_str) + "e"


@to_dag
def dependency_describer() -> None:
    _a = a()
    _b = b(_a)
    _c = c(_a)
    _d = d(_b)
    _e = e()


def test_compound_priority() -> None:
    dag = dependency_describer()

    assert dag.node_dict_by_name["a"].compound_priority == 4
    assert dag.node_dict_by_name["b"].compound_priority == 2
    assert dag.node_dict_by_name["c"].compound_priority == 1
    assert dag.node_dict_by_name["d"].compound_priority == 1
    assert dag.node_dict_by_name["e"].compound_priority == 1


def test_compound_priority_results() -> None:
    pytest.compound_priority_str == ""
    dag = dependency_describer()
    dag.execute()

    test_str = str(pytest.compound_priority_str)
    assert test_str.startswith("ab")
    assert len(test_str) == 5
