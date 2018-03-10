import pytest
import time

pytest_plugins = ['pytest_yield']


class O(object):
    state = None

    def __repr__(self):
        return self.state


@pytest.fixture(autouse=True)
def one():
    return 1


@pytest.fixture(autouse=True)
def two():
    return 2


@pytest.fixture(autouse=True)
def do_it(request):
    obj = O()
    obj.state = request.node.name + '[1]'
    yield obj
    obj.state = request.node.name + '[2]'
    print '%s teardown' % obj.state



def pytest_round_finished():
    time.sleep(1)
