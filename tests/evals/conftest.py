"""Eval-harness configuration.

Options are declared here so `pytest --help` documents them and tests
receive values through fixtures rather than reading global state.
"""

from __future__ import annotations

import pytest

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_SAMPLE_SIZE = 20


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("evals")
    group.addoption(
        "--model",
        action="store",
        default=DEFAULT_MODEL,
        help="Model identifier under test.",
    )
    group.addoption(
        "--sample-size",
        action="store",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of golden cases to run. Use a small value for smoke runs.",
    )


@pytest.fixture(scope="session")
def model(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--model")


@pytest.fixture(scope="session")
def sample_size(request: pytest.FixtureRequest) -> int:
    return request.config.getoption("--sample-size")