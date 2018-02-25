from pytest_yield import concurrent


def test_1():
    pass

@concurrent
def test_2(one):
    yield "Hello World"
    yield "Hello Worl2"
    yield
    assert one == 1

class TestClass(object):
    text = "Hello %s"
    def test_3(self):
        pass

    @concurrent
    def test_4(self, two):
        yield self.text % "World3"
        yield self.text % "World4"
        yield
        assert two == 2