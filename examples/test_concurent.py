import pytest
from pytest_yield import concurrent, Report


@pytest.mark.skip(reason="Skip this test")
def test_0():
    pass


@concurrent
def test_1():
    yield


@pytest.mark.concurrent(upstream='test_1')
def test_2(one):
    yield Report("Hello World")
    yield "Hello Worl2"
    yield
    assert one == 1


class TestClass(object):
    text = "Hello %s"

    def test_3(self):
        pass

    @concurrent(upstream='test_6[1]')
    def test_4(self, two):
        yield Report(self.text % "World3")
        yield self.text % "World4"
        yield
        assert two == 2

    @concurrent(downstream='test_3')
    @pytest.mark.skip(reason="Skip this test")
    def test_5(self, two):
        yield
        assert two == 2
    
    @concurrent
    @pytest.mark.parametrize('v', [1, 2])
    def test_6(self, one, v):
        yield Report('V=%s' % v)
