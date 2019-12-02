

SET_VISIBLE = "SET_VISIBLE"
ADD_LAYER = "ADD_LAYER"
REMOVE_LAYER = "REMOVE_LAYER"


def set_visible(flag):
    return {"kind": SET_VISIBLE, "payload": flag}


def add_layer():
    return {"kind": ADD_LAYER}


def remove_layer():
    return {"kind": REMOVE_LAYER}


def reducer(state, action):
    kind = action["kind"]
    if kind == SET_VISIBLE:
        return {"visible": action["payload"]}
    elif kind == ADD_LAYER:
        return {"layers": [0]}
    elif kind == REMOVE_LAYER:
        return {"layers": []}
    return state


class View:
    def render(self, state):
        pass
