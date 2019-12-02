from forest import images


def test_on_dropdown_updates_models():
    controls = images.Controls([])
    cb = controls.on_dropdown(0)
    cb(None, None, "GA6")
    result = controls.models
    expect = {
        0: "GA6"
    }
    assert expect == result


def test_on_radio_updates_flags():
    controls = images.Controls([])
    cb = controls.on_radio(0)
    cb(None, [], [1])
    result = controls.flags
    expect = {
        0: [False, True, False]
    }
    assert expect == result


def test_remove_row_removes_state():
    controls = images.Controls([])
    controls.add_row()
    controls.on_dropdown(1)(None, None, "key")
    controls.on_radio(1)(None, [], [1])
    controls.remove_row()
    assert controls.models == {}
    assert controls.flags == {}


def test_combine():
    result = images.Controls.combine(
            {0: "A", 1: "A"},
            {0: [True, False, False],
             1: [False, False, True]})
    expect = {
        "A": [True, False, True]
    }
    assert expect == result
