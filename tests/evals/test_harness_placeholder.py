"""Placeholder proving the eval tree is collected and gated in CI.

Real evals land in Thread 05 and call live models. They are marked so they
can be excluded from the fast unit path.
"""
import pytest

@pytest.mark.eval
def test_eval_harness_is_wired(model: str, sample_size: int) -> None:
    assert model
    assert sample_size > 0