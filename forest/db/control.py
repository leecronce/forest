"""Control navigation of FOREST data"""
import copy
import datetime as dt
import numpy as np
import bokeh.models
import bokeh.layouts
from . import util
from collections import namedtuple
from forest.observe import Observable
from forest.gridded_forecast import _to_datetime
from forest.export import export


__all__ = [
    "State",
]


SET_VALUE = "SET_VALUE"
NEXT_VALUE = "NEXT_VALUE"
PREVIOUS_VALUE = "PREVIOUS_VALUE"

@export
def set_value(key, value):
    return dict(kind=SET_VALUE, payload=locals())

@export
def next_valid_time():
    return next_value("valid_time", "valid_times")


@export
def next_initial_time():
    return next_value("initial_time", "initial_times")


@export
def next_value(item_key, items_key):
    return dict(kind=NEXT_VALUE, payload=locals())


@export
def previous_valid_time():
    return previous_value("valid_time", "valid_times")


@export
def previous_initial_time():
    return previous_value("initial_time", "initial_times")


@export
def previous_value(item_key, items_key):
    return dict(kind=PREVIOUS_VALUE, payload=locals())


State = namedtuple("State", (
    "pattern",
    "patterns",
    "variable",
    "variables",
    "initial_time",
    "initial_times",
    "valid_time",
    "valid_times",
    "pressure",
    "pressures",
    "valid_format"))
State.__new__.__defaults__ = (None,) * len(State._fields)

def statehash(self):
    return hash((self.pattern, str(self.patterns), self.variable, self.initial_time, str(self.initial_times), self.valid_time, str(self.valid_times), self.pressure, str(self.pressures), self.valid_format))

def time_equal(a, b):
    if (a is None) and (b is None):
        return True
    elif (a is None) or (b is None):
        return False
    else:
        return _to_datetime(a) == _to_datetime(b)

_vto_datetime = np.vectorize(_to_datetime)

def time_array_equal(x, y):
    if (x is None) and (y is None):
        return True
    elif (x is None) or (y is None):
        return False
    elif (len(x) == 0) or (len(y) == 0):
        return x == y
    return np.all(_vto_datetime(x) == _vto_datetime(y))

def equal_value(a, b):
    if (a is None) and (b is None):
        return True
    elif (a is None) or (b is None):
        return False
    else:
        return np.allclose(a, b)

def state_ne(self, other):
    return not (self == other)

def state_eq(self, other):
    return (
            (self.pattern == other.pattern) and
            np.all(self.patterns == other.patterns) and
            (self.variable == other.variable) and
            np.all(self.variables == other.variables) and
            time_equal(self.initial_time, other.initial_time) and
            time_array_equal(self.initial_times, other.initial_times) and
            time_equal(self.valid_time, other.valid_time) and
            time_array_equal(self.valid_times, other.valid_times) and
            equal_value(self.pressure, other.pressure) and
            equal_value(self.pressures, other.pressures)
    )

State.__hash__ = statehash
State.__eq__ = state_eq
State.__ne__ = state_ne


@export
def initial_state(navigator, pattern=None):
    """Find initial state given navigator"""
    state = {}
    state["pattern"] = pattern
    variables = navigator.variables(pattern)
    state["variables"] = variables
    if len(variables) == 0:
        return state
    variable = variables[0]
    state["variable"] = variable
    initial_times = navigator.initial_times(pattern, variable)
    state["initial_times"] = initial_times
    if len(initial_times) == 0:
        return state
    initial_time = max(initial_times)
    state["initial_time"] = initial_time
    valid_times = navigator.valid_times(
        variable=variable,
        pattern=pattern,
        initial_time=initial_time)
    state["valid_times"] = valid_times
    if len(valid_times) > 0:
        state["valid_time"] = min(valid_times)
    pressures = navigator.pressures(
            variable=variable,
            pattern=pattern,
            initial_time=initial_time)
    pressures = list(reversed(sorted(pressures)))
    state["pressures"] = pressures
    if len(pressures) > 0:
        state["pressure"] = pressures[0]
    return state


@export
def stamps(times):
    labels = []
    for t in times:
        if isinstance(t, np.datetime64):
            t = t.astype(dt.datetime)
        labels.append(str(t))
    return labels


@export
def reducer(state, action):
    state = copy.copy(state)
    kind = action["kind"]
    if kind == SET_VALUE:
        payload = action["payload"]
        key, value = payload["key"], payload["value"]
        state[key] = value
    return state


@export
class InverseCoordinate(object):
    """Translate actions on inverted coordinates"""
    def __init__(self, name):
        self.name = name

    def __call__(self, store, action):
        if self.is_next_previous(action) and self.has_name(action):
            yield self.invert(action)
        else:
            yield action

    @staticmethod
    def is_next_previous(action):
        return action["kind"] in [NEXT_VALUE, PREVIOUS_VALUE]

    def has_name(self, action):
        return self.name == action["payload"]["item_key"]

    @staticmethod
    def invert(action):
        kind = action["kind"]
        payload = action["payload"]
        item_key = payload["item_key"]
        items_key = payload["items_key"]
        if kind == NEXT_VALUE:
            return previous_value(item_key, items_key)
        else:
            return next_value(item_key, items_key)


@export
def next_previous(store, action):
    """Translate NEXT/PREVIOUS action(s) into SET action"""
    kind = action["kind"]
    if kind in [NEXT_VALUE, PREVIOUS_VALUE]:
        payload = action["payload"]
        item_key = payload["item_key"]
        items_key = payload["items_key"]
        if items_key not in store.state:
            # No further action to be taken
            return
        items = store.state[items_key]
        if item_key in store.state:
            item = store.state[item_key]
            if kind == NEXT_VALUE:
                value = next_item(items, item)
            else:
                value = previous_item(items, item)
        else:
            if kind == NEXT_VALUE:
                value = max(items)
            else:
                value = min(items)
        yield set_value(item_key, value)
    else:
        yield action


def next_item(items, item):
    items = list(sorted(items))
    i = items.index(item)
    return items[(i + 1) % len(items)]


def previous_item(items, item):
    items = list(sorted(items))
    i = items.index(item)
    return items[i - 1]


@export
class Navigator(object):
    """Interface for navigation menu system"""
    def variables(self, pattern):
        return ['air_temperature']

    def initial_times(self, pattern):
        return ['2019-01-01 00:00:00']

    def valid_times(self, pattern, variable, initial_time):
        return ['2019-01-01 12:00:00']

    def pressures(self, pattern, variable, initial_time):
        return [750.]


@export
class Converter(object):
    def __init__(self, maps):
        self.maps = maps

    def __call__(self, store, action):
        if action["kind"] == SET_VALUE:
            key = action["payload"]["key"]
            value = action["payload"]["value"]
            if key in self.maps:
                value = self.maps[key](value)
            yield set_value(key, value)
        else:
            yield action


@export
class Controls(object):
    def __init__(self, navigator):
        self.navigator = navigator

    def __call__(self, store, action):
        if action["kind"] == SET_VALUE:
            key = action["payload"]["key"]
            handlers = {
                "pressure": self._pressure,
                "pattern": self._pattern,
                "variable": self._variable,
                "initial_time": self._initial_time,
            }
            if key in handlers:
                yield from handlers[key](store, action)
            else:
                yield action
        else:
            yield action

    def _pressure(self, store, action):
        key = action["payload"]["key"]
        value = action["payload"]["value"]
        try:
            value = float(value)
        except ValueError:
            print("{} is not a float".format(value))
        yield set_value(key, value)

    def _pattern(self, store, action):
        value = action["payload"]["value"]
        variables = self.navigator.variables(pattern=value)
        initial_times = self.navigator.initial_times(pattern=value)
        initial_times = list(reversed(initial_times))
        yield action
        yield set_value("variables", variables)
        yield set_value("initial_times", initial_times)

    def _variable(self, store, action):
        for attr in ["pattern", "initial_time"]:
            if attr not in store.state:
                yield action
                return
        pattern = store.state["pattern"]
        variable = action["payload"]["value"]
        initial_time = store.state["initial_time"]
        valid_times = self.navigator.valid_times(
            pattern=pattern,
            variable=variable,
            initial_time=initial_time)
        valid_times = sorted(set(valid_times))
        pressures = self.navigator.pressures(
            pattern=pattern,
            variable=variable,
            initial_time=initial_time)
        pressures = list(reversed(pressures))
        yield action
        yield set_value("valid_times", valid_times)
        yield set_value("pressures", pressures)

    def _initial_time(self, store, action):
        for attr in ["pattern", "variable"]:
            if attr not in store.state:
                yield action
                return
        initial_time = action["payload"]["value"]
        valid_times = self.navigator.valid_times(
            pattern=store.state["pattern"],
            variable=store.state["variable"],
            initial_time=initial_time)
        valid_times = sorted(set(valid_times))
        yield action
        yield set_value("valid_times", valid_times)


@export
class ControlView(Observable):
    def __init__(self):
        dropdown_width = 180
        button_width = 75
        self.dropdowns = {
            "pattern": bokeh.models.Dropdown(
                label="Model/observation"),
            "variable": bokeh.models.Dropdown(
                label="Variable"),
            "initial_time": bokeh.models.Dropdown(
                label="Initial time",
                width=dropdown_width),
            "valid_time": bokeh.models.Dropdown(
                label="Valid time",
                width=dropdown_width),
            "pressure": bokeh.models.Dropdown(
                label="Pressure",
                width=dropdown_width)
        }
        for key, dropdown in self.dropdowns.items():
            util.autolabel(dropdown)
            util.autowarn(dropdown)
            dropdown.on_change("value", self.on_change(key))
        self.rows = {}
        self.buttons = {}
        for key, items_key in [
                ('pressure', 'pressures'),
                ('valid_time', 'valid_times'),
                ('initial_time', 'initial_times')]:
            self.buttons[key] = {
                'next': bokeh.models.Button(
                    label="Next",
                    width=button_width),
                'previous': bokeh.models.Button(
                    label="Previous",
                    width=button_width),
            }
            self.buttons[key]['next'].on_click(
                self.on_next(key, items_key))
            self.buttons[key]['previous'].on_click(
                self.on_previous(key, items_key))
            self.rows[key] = bokeh.layouts.row(
                self.buttons[key]["previous"],
                self.dropdowns[key],
                self.buttons[key]["next"])
        self.layout = bokeh.layouts.column(
            self.dropdowns["pattern"],
            self.dropdowns["variable"],
            self.rows["initial_time"],
            self.rows["valid_time"],
            self.rows["pressure"])
        super().__init__()

    def on_change(self, key):
        def callback(attr, old, new):
            self.notify(set_value(key, new))
        return callback

    def on_next(self, item_key, items_key):
        def callback():
            self.notify(next_value(item_key, items_key))
        return callback

    def on_previous(self, item_key, items_key):
        def callback():
            self.notify(previous_value(item_key, items_key))
        return callback

    def render(self, state):
        """Configure dropdown menus"""
        assert isinstance(state, dict), "Only support dict"
        for key, items_key in [
                ("pattern", "patterns"),
                ("variable", "variables"),
                ("initial_time", "initial_times"),
                ("valid_time", "valid_times"),
                ("pressure", "pressures")]:
            if items_key not in state:
                disabled = True
            else:
                values = state[items_key]
                disabled = len(values) == 0
                if key == "pressure":
                    menu = [(self.hpa(p), str(p)) for p in values]
                elif key == "pattern":
                    menu = state["patterns"]
                else:
                    menu = self.menu(values)
                self.dropdowns[key].menu = menu
            self.dropdowns[key].disabled = disabled
            if key in self.buttons:
                self.buttons[key]["next"].disabled = disabled
                self.buttons[key]["previous"].disabled = disabled

        if ("pattern" in state) and ("patterns" in state):
            for _, pattern in state["patterns"]:
                if pattern == state["pattern"]:
                    self.dropdowns["pattern"].value = pattern

        for key in [
                "variable",
                "initial_time",
                "pressure",
                "valid_time"]:
            if key in state:
                if state[key] is None:
                    continue
                self.dropdowns[key].value = str(state[key])

    @staticmethod
    def menu(values, formatter=str):
        return [(formatter(o), formatter(o)) for o in values]

    @staticmethod
    def hpa(p):
        if p < 1:
            return "{}hPa".format(str(p))
        return "{}hPa".format(int(p))
