from .tree import TaskTree, TaskTreeSortKey, TaskTreeParserXML, Schedule
from .referenced import ReferencedDescriptor
from .config import Config
import logging
import copy

class TreeManager:
    def __init__(self):
        self._current = None
        self._clipboard = None
        self.trees = []
        self.global_schedule = Schedule(ReferencedDescriptor(TreeManager.global_schedule_list, self), self.sync_cursors)

    @property
    def clipboard(self):
        if self._clipboard is None:
            return None
        else:
            return copy.deepcopy(self._clipboard)

    @clipboard.setter
    def clipboard(self, node):
        self._clipboard = node

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, tree):
        if not tree in self.trees:
            self.trees.append(tree)
            tree.manager = self
        self._current = tree

    @property
    def global_schedule_list(self):
        gsl = []
        for tree in self.trees:
            gsl += tree.schedule_list

        gsl.sort(key=lambda t: t.sort_date)

        return gsl

    def outdate_display_lists(self):
        for tree in self.trees:
            tree.outdate_display_list()

    @property
    def schedule_in_use(self):
        if Config.get("behaviour.global_schedule"):
            return self.global_schedule
        else:
            return self.current.schedule

    def sync_cursors(self):
        if Config.get("behaviour.global_schedule"):
            for tree in self.trees:
                if self.global_schedule.cursor in tree.display_list:
                    self.current = tree
                    self.current.cursor = self.global_schedule.cursor
                    break

    def next_tree(self):
        index = self.trees.index(self.current)
        index += 1 - len(self.trees)
        self.current = self.trees[index]

    def prev_tree(self):
        index = self.trees.index(self.current)
        index -= 1
        self.current = self.trees[index]
    
    def open_tree(self, path, set_current=True, parser=TaskTreeParserXML, name=None):
        if name is None:
            name = path

        newtree = TaskTree(path, self, parser=parser, name=name)
        self.trees.append(newtree)
        if set_current:
            self.current = newtree

    def close_tree(self, tree):
        if not tree in self.trees:
            raise ValueError("Tree not open")

        if len(self.trees) == 1:
            raise IndexError("Cannot close the last tree")

        index = self.trees.index(tree) - len(self.trees) + 1
        
        self.trees.remove(tree)

        tree.manager = None

        if tree == self.current:
            self.current = self.trees[index]

    def save_all(self):
        for tree in self.trees:
            tree.save()

    def close_current_tree(self):
        self.close_tree(self.current)
