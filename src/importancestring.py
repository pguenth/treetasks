import copy

class ImportanceChar:
    def __init__(self, c, importance):
        self.importance = importance
        self.c = c

    def __str__(self):
        return self.c

    def __repr__(self):
        return "({}, {})".format(self.c, self.importance)

class ImportanceString:
    def __init__(self, list_of_importance_chars=None):
        if list_of_importance_chars is None:
            self._l = []
        else:
            self._l = list(list_of_importance_chars)

    @classmethod
    def from_two_lists(cls, string, importances):
        l = []
        for c, i in zip(string, importances):
            l.append(ImportanceChar(c, i))

        return cls(l)

    def __str__(self):
        chars = [ic.c for ic in self._l]
        return "".join(chars)

    def _remove_most_important(self, n):
        for _ in range(n):
            importances = [ic.importance for ic in self._l]
            li_index = importances.index(max(importances))
            del self._l[li_index]

    def _remove_least_important(self, n):
        for _ in range(n):
            importances = [ic.importance for ic in self._l]
            li_index = importances.index(min(importances))
            del self._l[li_index]

    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
            step = key.step if not key.step is None else 1
            if start is None and not stop is None:
                if stop > 0:
                    stop -= len(self._l)
                stop *= -1
                cp = copy.deepcopy(self)
                cp._remove_least_important(stop)
                return cp
            elif not start is None and stop is None:
                if start < 0:
                    start += len(self._l)
                cp = copy.deepcopy(self)
                cp._remove_most_important(start)
                return cp
            else:
                new_l = self._l[key]
                return ImportanceString(new_l)
        elif isinstance(key, int):
            return self._l[key]

    def __iadd__(self, other):
        if not type(other) is type(self):
            return NotImplemented

        self._l += other._l
        return self

    def __add__(self, other):
        if not type(other) is type(self):
            return NotImplemented

        new_l = self._l + other._l
        return ImportanceString(new_l)

    def __radd__(self, other):
        if not type(other) is type(self):
            return NotImplemented

        new_l = other._l + self._l
        return ImportanceString(new_l)

    def __len__(self):
        return len(self._l)

    def __repr__(self):
        string = ", ".join([repr(ic) for ic in self._l])
        return "[{}]".format(string)

