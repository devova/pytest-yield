import sys
import py

from _pytest.outcomes import TEST_OUTCOME
from _pytest.runner import SetupState


class TreeStack(dict):

    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

    def __contains__(self, item):
        contains = dict.__contains__(self, item)
        if not contains:
            for val in self.values():
                contains = item in val
                if contains:
                    break
        return contains

    def add_nested(self, keys):
        d = self
        added = []
        for key in keys:
            if not dict.__contains__(d, key):
                added.append(key)
            d = d[key]
        return added

    def flat(self):
        res = list(self.keys())
        for val in self.values():
            res += val.flat()
        return list(res)

    def pop(self, key):
        contains = dict.__contains__(self, key)
        if contains:
            return dict.pop(self, key)
        else:
            for val in self.values():
                res = val.pop(key)
                if res is not None:
                    return res

    def get(self, key):
        contains = dict.__contains__(self, key)
        if contains:
            return dict.get(self, key)
        else:
            for val in self.values():
                res = val.get(key)
                if res is not None:
                    return res

    def popitem(self):
        for val in self.values():
            if val:
                return val.popitem()
        return dict.popitem(self)


class YieldSetupState(SetupState):

    def __init__(self):
        super(YieldSetupState, self).__init__()
        self.stack = TreeStack()
        self.collection_stack = TreeStack()

    def _teardown_towards(self, needed_collectors):
        return

    def _pop_and_teardown(self):
        colitem, _ = self.stack.popitem()
        self._teardown_with_finalization(colitem)

    def teardown_exact(self, item, nextitem):
        self._teardown_with_finalization(item)
        self.stack.pop(item)
        self.collection_stack.pop(item)
        items_on_same_lvl = self.collection_stack.get(item.parent)
        if items_on_same_lvl is not None and len(items_on_same_lvl) == 0:
            self.teardown_exact(item.parent, None)

    def prepare(self, colitem):
        """ setup objects along the collector chain to the test-method
            and teardown previously setup objects."""
        needed_collectors = colitem.listchain()

        # check if the last collection node has raised an error
        for col in self.stack.flat():
            if hasattr(col, '_prepare_exc'):
                py.builtin._reraise(*col._prepare_exc)

        added_to_stack = self.stack.add_nested(needed_collectors)
        for col in added_to_stack:
            try:
                col.setup()
            except TEST_OUTCOME:
                col._prepare_exc = sys.exc_info()
                raise
