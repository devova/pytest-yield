from conftest import concurrent


def test_1():
    pass

@concurrent
def test_2(something):
    yield "Hello World"
    yield "Hello Worl2"
    yield
    assert something == 2

class TestClass(object):
    text = "Hello %s"
    def test_3(self):
        pass

    @concurrent
    def test_4(self, something):
        yield self.text % "World3"
        yield self.text % "World4"
        yield
        assert something == 3