import pytest


def pytest_configure(config):
    config.addinivalue_line('markers', 'incremental: skip remaining tests after first failure')


def pytest_runtest_makereport(item, call):
    if 'incremental' in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent.previous_failed = item


def pytest_runtest_setup(item):
    if 'incremental' in item.keywords:
        previous_failed = getattr(item.parent, 'previous_failed', None)
        if previous_failed is not None:
            pytest.skip(f'previous test failed ({previous_failed.name})')
