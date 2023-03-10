from typing import Dict, List, Tuple

import pytest
from tawazi import dag, xn


def test_lazy_exec_nodes_return_dict_indexed() -> None:
    @xn
    def generate_dict() -> Dict[str, int]:
        return {"1": 1, "2": 2, "3": 3}

    @xn
    def incr(a: int) -> int:
        return a + 1

    @dag
    def pipe() -> Tuple[int, int, int]:
        d = generate_dict()
        return incr(d["1"]), incr(d["2"]), incr(d["3"])

    assert (2, 3, 4) == pipe()


def test_lazy_exec_nodes_return_tuple_indexed() -> None:
    @xn
    def generate_tuple() -> Tuple[int, ...]:
        return (1, 2, 3, 4)

    @xn
    def incr(a: int) -> int:
        return a + 1

    @dag
    def pipe() -> Tuple[int, int, int]:
        d = generate_tuple()
        return incr(d[0]), incr(d[1]), incr(d[2])

    assert (2, 3, 4) == pipe()


def test_lazy_exec_nodes_return_list_indexed() -> None:
    @xn
    def generate_list() -> List[int]:
        return [1, 2, 3, 4]

    @xn
    def incr(a: int) -> int:
        return a + 1

    @dag
    def pipe() -> List[int]:
        d = generate_list()
        return [incr(d[0]), incr(d[1]), incr(d[2])]

    assert [2, 3, 4] == pipe()


def test_lazy_exec_nodes_return_multiple_index() -> None:
    @xn
    def generate_nested_list() -> Tuple[List[int], int, Tuple[int, Tuple[int]]]:
        return ([1], 2, (3, (4,)))

    @xn
    def incr(a: int) -> int:
        return a + 1

    @dag
    def pipe() -> List[int]:
        d = generate_nested_list()
        return [incr(d[0][0]), incr(d[1]), incr(d[2][0]), incr(d[2][1][0])]

    assert [2, 3, 4, 5] == pipe()


def test_lazy_exec_nodes_return_multiple_index_reused() -> None:
    @xn
    def generate_nested_list() -> Tuple[List[int], int, Tuple[int, Tuple[int]]]:
        return ([1], 2, (3, (4,)))

    @xn
    def incr(a: int) -> int:
        return a + 1

    @xn
    def add(a: int, b: int) -> int:
        return a + b

    @dag
    def pipe() -> Tuple[int, ...]:
        d = generate_nested_list()
        d0, d1, d2, d3 = d[0][0], d[1], d[2][0], d[2][1][0]
        d0_, d1_, d2_, d3_ = incr(d0), incr(d1), incr(d2), incr(d3)
        return add(d0_, d0), add(d1_, d1), add(d2_, d2), add(d3_, d3)

    assert (3, 5, 7, 9) == pipe()


def test_lazy_exec_nodes_multiple_return_values() -> None:
    @xn(unpack_to=3)
    def mulreturn() -> Tuple[int, int, int]:
        return 1, 2, 3

    @dag
    def pipe() -> Tuple[int, int]:
        r1, r2, _r3 = mulreturn()
        return r1, r2

    assert pipe() == (1, 2)


def test_lazy_exec_nodes_multiple_return_values_in_tuple() -> None:
    @xn(unpack_to=3)
    def mulreturn() -> Tuple[int, int, int]:
        return 1, 2, 3

    @dag
    def pipe() -> Tuple[int, int]:
        (r1, r2, _r3) = mulreturn()
        return r1, r2

    assert pipe() == (1, 2)


def test_lazy_exec_nodes_multiple_return_values_in_list() -> None:
    @xn(unpack_to=3)
    def mulreturn() -> Tuple[int, int, int]:
        return 1, 2, 3

    @dag
    def pipe() -> Tuple[int, int]:
        [r1, r2, _r3] = mulreturn()
        return r1, r2

    assert pipe() == (1, 2)


def test_lazy_exec_nodes_multiple_return_values_wrong_bigger_unpack_to_number() -> None:
    @xn(unpack_to=4)
    def mulreturn() -> Tuple[int, int, int]:
        return 1, 2, 3

    with pytest.raises(ValueError):

        @dag
        def pipe() -> Tuple[int, int]:
            r1, r2, _r3 = mulreturn()
            return r1, r2


def test_lazy_exec_nodes_multiple_return_values_wrong_lower_unpack_to_number() -> None:
    @xn(unpack_to=1)
    def mulreturn() -> Tuple[int, int, int]:
        return 1, 2, 3

    with pytest.raises(ValueError):

        @dag
        def pipe() -> Tuple[int, int]:
            r1, r2, _r3 = mulreturn()
            return r1, r2