import pytest
import time

from collections import defaultdict

pytest_plugins = ['pytest_yield']


class CallCounter(object):
    def __init__(self):
        self.count = defaultdict(lambda: 0)

    def incr(self, lvl):
        self.count[lvl] += 1

    def decr(self, lvl):
        self.count[lvl] -= 1


@pytest.fixture(autouse=True)
def one():
    return 1


@pytest.fixture(autouse=True)
def two():
    return 2


@pytest.fixture(scope='session')
def call_counter(request):
    counter = CallCounter()
    counter.incr('session')
    yield counter
    counter.decr('session')
    assert counter.count['function'] == 0
    assert counter.count['class'] == 0
    assert counter.count['module'] == 0


@pytest.fixture(scope='module')
def check_teardown_module(call_counter):
    call_counter.incr('module')
    yield
    call_counter.decr('module')


@pytest.fixture(scope='class')
def check_teardown_class(call_counter):
    call_counter.incr('class')
    yield
    call_counter.decr('class')


@pytest.fixture(autouse=True)
def check_teardown_function(call_counter):
    call_counter.incr('function')
    yield
    call_counter.decr('function')


def pytest_round_finished():
    time.sleep(1)
