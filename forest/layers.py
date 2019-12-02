

SET_VISIBLE = "SET_VISIBLE"


def set_visible(flag):
    return {"kind": SET_VISIBLE, "payload": flag}


def reducer(state, action):
    if action["kind"] == SET_VISIBLE:
        return {"visible": action["payload"]}
    return state
