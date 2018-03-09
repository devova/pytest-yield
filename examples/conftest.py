import pytest
import time

pytest_plugins = ['pytest_yield']


@pytest.fixture(autouse=True)
def one():
    return 1


@pytest.fixture(autouse=True)
def two():
    return 2


def pytest_round_finished():
    time.sleep(1)
