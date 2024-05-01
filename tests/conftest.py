##
##

from io import TextIOWrapper

RESULTS_FILE: TextIOWrapper


def pytest_addoption():
    pass


def pytest_configure():
    pass


def pytest_sessionstart():
    global RESULTS_FILE
    RESULTS_FILE = open("results.log", "w")


def pytest_sessionfinish():
    global RESULTS_FILE
    if RESULTS_FILE:
        RESULTS_FILE.close()
        RESULTS_FILE = None


def pytest_unconfigure():
    pass


def pytest_runtest_logreport(report):
    RESULTS_FILE.write(f"{report.nodeid} {report.when} {report.outcome} {report.duration}\n")
