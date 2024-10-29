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


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()

    yield loop

    pending = asyncio.tasks.all_tasks(loop)
    loop.run_until_complete(asyncio.gather(*pending))
    loop.run_until_complete(asyncio.sleep(1))

    loop.close()
