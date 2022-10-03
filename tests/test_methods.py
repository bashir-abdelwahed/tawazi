from logging import Logger
from typing import Union

import pytest

from tawazi import op, to_dag

logger = Logger(name="mylogger", level="ERROR")


class MyClass:
    @op
    def a(self) -> str:
        logger.debug("ran a")
        return "a"

    @op
    def b(self, a: str) -> str:
        logger.debug(f"a is {a}")
        logger.debug("ran b")
        return "b"

    @op
    def c(self, a: str) -> str:
        logger.debug(f"a is {a}")
        logger.debug("ran c")
        return "c"

    @op
    def d(
        self,
        b: str,
        c: str,
        third_argument: Union[str, int] = 1234,
        fourth_argument: Union[int, str] = 6789,
    ) -> str:
        logger.debug(f"b is {b}")
        logger.debug(f"c is {c}")
        logger.debug(f"third argument is {third_argument}")
        pytest.third_argument = third_argument
        logger.debug(f"fourth argument is {fourth_argument}")
        pytest.fourth_argument = fourth_argument
        logger.debug("ran d")
        return "d"

    @to_dag
    def my_custom_dag(self) -> None:
        vara = self.a()
        varb = self.b(vara)
        varc = self.c(vara)
        _vard = self.d(varb, c=varc, fourth_argument=1111)


def test_ops_interface() -> None:
    c = MyClass()

    d1 = c.my_custom_dag()
    logger.debug("\n1st execution of dag")
    d1.execute()
    assert pytest.third_argument == 1234
    assert pytest.fourth_argument == 1111
    logger.debug("\n2nd execution of dag")
    d1.execute()
