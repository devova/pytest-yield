from pytest_yield import concurrent, Report


def test_0():
    pass


@concurrent
def test_1():
    yield


def test_2(one):
    """concurrent"""
    yield Report("Hello World")
    yield "Hello Worl2"
    yield
    assert one == 1


class TestClass(object):
    text = "Hello %s"

    def test_3(self):
        pass

    @concurrent
    def test_4(self, two):
        yield Report(self.text % "World3")
        yield self.text % "World4"
        yield
        assert two == 2

    def test_5(self, one, two):
        """
        Verify sum of numbers
        """
        yield
        assert one + two == 3