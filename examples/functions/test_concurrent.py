import pytest
from pytest_yield.mark import Report

pytestmark = pytest.mark.usefixtures('check_teardown_module')


def sub_generator(num):
    for x in range(num):
        yield x + 1


@pytest.mark.skip(reason="Skip this test")
@pytest.mark.concurrent
def test_skip_concurrent():
    yield
    assert 1 == 2


@pytest.mark.concurrent
def test_concurrent(one):
    yield
    assert one == 1


@pytest.mark.parametrize('v', [1, 2])
@pytest.mark.concurrent
def test_concurrent_with_param(one, v):
    assert one + v == 1 + v
    yield


@pytest.mark.concurrent
def test_concurrent_with_report(one, two):
    yield Report("Hello World")
    assert one + two == 3
    yield "Hello Worl2"


@pytest.mark.concurrent
def test_concurrent_with_sub_generator(one):
    number = yield sub_generator(2)
    assert one == 1
    assert number == 2


@pytest.mark.xfail
@pytest.mark.concurrent
def test_concurrent_xfail(two):
    yield
    assert two == 1
