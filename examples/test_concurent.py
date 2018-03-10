import pytest
from pytest_yield import concurrent, Report


@pytest.mark.skip(reason="Skip this test")
def test_0(do_it):
    pass


@concurrent
def test_1(do_it):
    yield Report(do_it.state)


@pytest.mark.concurrent()
def test_2(one, do_it):
    yield Report("Hello World")
    yield "Hello Worl2"
    yield Report(do_it.state)
    assert one == 1

def test_22(do_it):
    pass

#
class TestClass(object):
    text = "Hello %s"

    def test_3(self, do_it):
        pass

    @concurrent()
    def test_4(self, two, do_it):
        yield Report(self.text % "World3")
        yield self.text % "World4"
        yield Report(do_it.state)
        assert two == 2

    @concurrent()
    @pytest.mark.skip(reason="Skip this test")
    def test_5(self, two, do_it):
        yield Report(do_it.state)
        assert two == 2

    @concurrent
    @pytest.mark.parametrize('v', [1, 2])
    def test_6(self, do_it, v):
        yield Report('V=%s' % v)
        yield Report(do_it.state)
