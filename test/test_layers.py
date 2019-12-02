import pytest
from forest import layers


@pytest.mark.parametrize("state,action,expect", [
    ({}, layers.set_visible(True), {"visible": True}),
    ({}, layers.set_visible(False), {"visible": False}),
    ({}, layers.add_layer(), {"layers": [0]}),
    ({"layers": [0]}, layers.remove_layer(), {"layers": []}),
])
def test_reducer(state, action, expect):
    result = layers.reducer(state, action)
    assert expect == result
