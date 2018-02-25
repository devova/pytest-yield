import pytest

pytest_plugins = ['pytest_yield']


@pytest.fixture(autouse=True)
def one():
    return 1


@pytest.fixture(autouse=True)
def two():
    return 2

def pytest_round_finished():
    import time
    time.sleep(1)
