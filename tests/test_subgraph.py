from nis import match
from typing import Any

import pytest

from tawazi import op, to_dag

pytest.subgraph_comp_str = ""
T = 1e-3


@op
def a() -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "a"


@op
def b(a: Any) -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "b"


@op
def c(a: Any) -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "c"


@op
def d(c: Any) -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "d"


@op
def e(c: Any) -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "e"


@op
def f(e: Any) -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "f"


@op
def g() -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "g"


@op
def h() -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "h"


@op
def i(h: Any) -> None:
    pytest.subgraph_comp_str = str(pytest.subgraph_comp_str) + "i"


@to_dag
def dag_describer() -> None:
    var_a = a()
    var_b = b(var_a)
    var_c = c(var_a)
    var_d = d(var_c)
    var_e = e(var_c)
    var_f = f(var_e)

    var_g = g()

    var_h = h()
    var_i = i(var_h)


def test_dag_subgraph_all_nodes() -> None:
    pytest.subgraph_comp_str = ""
    dag = dag_describer()
    results = dag.execute([a, b, c, d, e, f, g, h, i])
    assert set("abcdefghi") == set(pytest.subgraph_comp_str)


def test_dag_subgraph_leaf_nodes() -> None:
    pytest.subgraph_comp_str = ""
    dag = dag_describer()
    results = dag.execute([b, d, f, g, i])
    assert set("abcdefghi") == set(pytest.subgraph_comp_str)


def test_dag_subgraph_leaf_nodes_with_extra_nodes() -> None:
    pytest.subgraph_comp_str = ""
    dag = dag_describer()
    results = dag.execute([b, c, e, h, g])
    assert set("abcegh") == set(pytest.subgraph_comp_str)


def test_dag_subgraph_nodes_ids() -> None:
    pytest.subgraph_comp_str = ""
    dag = dag_describer()
    results = dag.execute([b.id, c.id, e.id, h.id, g.id])
    assert set("abcegh") == set(pytest.subgraph_comp_str)


def test_dag_subgraph_non_existing_nodes_ids() -> None:
    with pytest.raises(ValueError, match="nodes are not in the graph"):
        dag = dag_describer()
        results = dag.execute(["gibirish"])
