import pytest
from forest import layers


@pytest.mark.parametrize("state,action,expect", [
        ({}, {}, {})
    ])
def test_reducer(state, action, expect):
    result = layers.reducer(state, action)
    assert expect == result
