from copy import deepcopy
from time import sleep
from typing import Any, Tuple

from tawazi import ErrorStrategy, Resource, dag, xn

from tests.helpers import UseDill

T = 0.001
# global behavior_comp_str
behavior_comp_str = ""


@xn
def a() -> None:
    sleep(T)
    global behavior_comp_str
    behavior_comp_str += "a"
    return


@xn(priority=2)
def b(a: Any) -> None:
    raise NotImplementedError
    return


@xn(priority=2)
def c(b: Any) -> None:
    sleep(T)
    global behavior_comp_str
    behavior_comp_str += "c"
    return


@xn
def d(a: Any) -> None:
    sleep(T)
    global behavior_comp_str
    behavior_comp_str += "d"
    return


@dag
def g() -> None:
    a_ = a()
    b_ = b(a_)
    c(b_)
    d(a_)


def test_strict_error_behavior() -> None:
    global behavior_comp_str
    behavior_comp_str = ""
    g_ = deepcopy(g)
    g_.behavior = ErrorStrategy.strict
    try:
        g_()
    except NotImplementedError:
        pass


def test_all_children_behavior() -> None:
    global behavior_comp_str
    behavior_comp_str = ""
    g_ = deepcopy(g)
    g_.behavior = ErrorStrategy.all_children
    g_()
    assert behavior_comp_str == "ad"


def test_permissive_behavior() -> None:
    global behavior_comp_str
    behavior_comp_str = ""
    g_ = deepcopy(g)
    g_.behavior = ErrorStrategy.permissive
    g_()
    assert behavior_comp_str == "acd"


@xn(resource=Resource.main_thread)
def a_main() -> None:
    sleep(T)
    global behavior_comp_str
    behavior_comp_str += "a"


@xn(priority=2, resource=Resource.main_thread)
def b_main(a: Any) -> None:
    raise NotImplementedError


@xn(priority=2, resource=Resource.main_thread)
def c_main(b: Any) -> None:
    sleep(T)
    global behavior_comp_str
    behavior_comp_str += "c"


@xn(resource=Resource.main_thread)
def d_main(a: Any) -> None:
    sleep(T)
    global behavior_comp_str
    behavior_comp_str += "d"


@dag
def g_main() -> None:
    a_ = a_main()
    b_ = b_main(a_)
    c_main(b_)
    d_main(a_)


def test_strict_error_behavior_main_thread() -> None:
    global behavior_comp_str
    behavior_comp_str = ""
    g_ = deepcopy(g_main)
    g_.behavior = ErrorStrategy.strict
    try:
        g_()
    except NotImplementedError:
        pass


def test_all_children_behavior_main_thread() -> None:
    global behavior_comp_str
    behavior_comp_str = ""
    g_ = deepcopy(g_main)
    g_.behavior = ErrorStrategy.all_children
    g_()
    assert behavior_comp_str == "ad"


def test_permissive_behavior_main_thread() -> None:
    global behavior_comp_str
    behavior_comp_str = ""
    g_ = deepcopy(g_main)
    g_.behavior = ErrorStrategy.permissive
    g_()
    assert behavior_comp_str == "acd"


def declare_process_xns_and_dag() -> Any:
    @xn(resource=Resource.process)
    def a_process() -> str:
        sleep(T)
        return "a"

    @xn(priority=2, resource=Resource.process)
    def b_process(a: Any) -> str:
        raise NotImplementedError

    @xn(priority=2, resource=Resource.process)
    def c_process(b: str) -> str:
        sleep(T)
        if b is None:
            return "c"
        b += "c"
        return b

    @xn(resource=Resource.process)
    def d_process(a: str) -> str:
        sleep(T)
        a += "d"
        return a

    @dag
    def g_process() -> Tuple[str, str, str, str]:
        a_ = a_process()
        b_ = b_process(a_)
        c_ = c_process(b_)
        d_ = d_process(a_)

        return a_, b_, c_, d_

    return g_process


def test_strict_error_behavior_process() -> None:
    with UseDill():
        g_process = declare_process_xns_and_dag()
        global behavior_comp_str
        behavior_comp_str = ""
        g_ = deepcopy(g_process)
        g_.behavior = ErrorStrategy.strict
        try:
            g_()
        except NotImplementedError:
            pass


def test_all_children_behavior_process() -> None:
    with UseDill():
        g_process = declare_process_xns_and_dag()
        global behavior_comp_str
        behavior_comp_str = ""
        g_ = deepcopy(g_process)
        g_.behavior = ErrorStrategy.all_children
        a, b, c, d = g_()
        # raise assertion error when dill is used instead of assert ... == ...
        #  because dill and pytest don't play well together
        if a != "a":
            raise AssertionError
        if b is not None:
            raise AssertionError
        if c is not None:
            raise AssertionError
        if d != "ad":
            raise AssertionError


def test_permissive_behavior_process() -> None:
    with UseDill():
        g_process = declare_process_xns_and_dag()
        global behavior_comp_str
        behavior_comp_str = ""
        g_ = deepcopy(g_process)
        g_.behavior = ErrorStrategy.permissive
        a, b, c, d = g_()
        if a != "a":
            raise AssertionError
        if b is not None:
            raise AssertionError
        if c != "c":
            raise AssertionError
        if d != "ad":
            raise AssertionError


# todo test using argname for ExecNode
