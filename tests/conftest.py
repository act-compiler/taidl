import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "incremental: skip remaining tests after first failure")


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.skip(f"previous test failed ({previousfailed.name})")
