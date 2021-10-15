from .tree import TaskTree, TaskTreeSortKey
import logging
import copy

class TreeManager:
    def __init__(self):
        self._current = None
        self._clipboard = None
        self.trees = []

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

    def next_tree(self):
        index = self.trees.index(current)
        index += 1 - len(self.trees)
        self.current = self.trees[index]

    def prev_tree(self):
        index = self.tree.index(current)
        index -= 1
        self.current = self.trees[index]
    
    def open_tree(self, path, set_current=True):
        newtree = TaskTree(path, self)
        self.trees.append(newtree)
        logging.debug("Opened")
        if set_current:
            logging.debug("Setting")
            self.current = newtree

    def close_tree(self, tree):
        if not tree in self.trees:
            raise ValueError("Tree not open")

        index = self.trees.index(tree) - len(self.trees)
        
        self.trees.remove(tree)

        tree.manager = None

        if tree == self.current:
            self.current = self.trees[index]

    def save_all(self):
        for tree in self.trees:
            #tree.set_order(TaskTreeSortKey.NATURAL)
            tree.save()
