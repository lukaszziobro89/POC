import re

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def camel_to_snake(name):
    """Convert CamelCase string to snake_case."""
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", name).lower()


def underscore_to_human(name):
    """Convert underscore_separated string to Human Readable format with only first letter capitalized."""
    return " ".join(name.split("_")).capitalize()


def pytest_itemcollected(item):
    """Change test name display in output."""
    # Replace 'tests/anything/' with empty string
    item._nodeid = re.sub(r"tests/[^/]+/", "", item._nodeid)
    item._nodeid = item._nodeid.replace(".py", "").replace("test_", "")

    # Convert class name from CamelCase to snake_case if pattern matches
    parts = item._nodeid.split("::")
    if len(parts) == 3:
        parts[1] = camel_to_snake(parts[1])
        if parts[1].startswith("test_"):
            parts[1] = parts[1][5:]  # Remove "test_" prefix
        item._nodeid = "::".join(parts)

    # Remove "describe_" prefix in parts[1]
    if parts[1].startswith("describe_"):
        parts[1] = parts[1][9:]

    # Convert the last part (test case name) to human readable format
    if len(parts) > 1:
        parts[-1] = underscore_to_human(parts[-1])

    item._nodeid = "::".join(parts)