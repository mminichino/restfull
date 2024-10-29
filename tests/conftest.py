##
##

import asyncio
import pytest


def pytest_addoption():
    pass


def pytest_configure():
    pass


def pytest_sessionstart():
    pass


def pytest_sessionfinish():
    pass


def pytest_unconfigure():
    pass


def pytest_runtest_logreport():
    pass


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
