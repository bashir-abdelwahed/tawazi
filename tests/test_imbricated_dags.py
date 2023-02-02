# type: ignore
from tawazi import to_dag, xnode


def test_imbricated_dags():
    @xnode
    def op1(img):
        return sum(img)

    @xnode
    def op2(op1):
        return 1 - op1

    @xnode
    @to_dag
    def op3(img):
        toto = op2(op1(img))
        return toto

    @xnode
    def op4(img):
        return sum(img) ** 2

    @xnode
    def op5(mean, std):
        return mean + std

    @to_dag
    def op6(img):
        titi = op3(img)
        toto = op4(img)

        return op5(titi, toto)

    pipe = op6([1, 2, 3, 4])