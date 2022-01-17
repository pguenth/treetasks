from .tree import TaskTree, TaskTreeSortKey
from .cursor import ScheduleCursor, TabbarCursor
from .referenced import ReferencedDescriptor
from .config import Config
from .treeparser import TaskTreeParserAuto
import logging
import time
import copy
import psutil
import os
import signal


def check_pidfile(treetasks_path):
    pidfile = treetasks_path + ".pid"
    if not os.path.exists(pidfile):
        return None

    with open(pidfile) as pf:
        try:
            pid = int(pf.read())
        except ValueError:
            logging.warn("Could not parse pid file contents from {}".format(pidfile))
            return None

    return pid

def lock_pidfile(treetasks_path):
    pidfile = treetasks_path + ".pid"
    with open(pidfile, "w") as pf:
        pf.write(str(os.getpid()))

def remove_pidfile(treetasks_path):
    pidfile = treetasks_path + ".pid"
    os.remove(pidfile)

def is_self(pid):
    return pid == os.getpid()

def is_running(pid):
    return psutil.pid_exists(pid)

def kill_and_wait(pid, signal, timeout=3):
    os.kill(pid, signal)
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        if not is_running(pid):
            break

    return is_running(pid)

class TreeManager:
    def __init__(self, app):
        self._clipboard = None
        self._app = app
        self.global_schedule = ScheduleCursor(ReferencedDescriptor(TreeManager.global_schedule_list, self), self.sync_cursors)
        self.tabs = TabbarCursor(ReferencedDescriptor(TreeManager.trees, self))

    @property
    def trees(self):
        try:
            return self._trees
        except AttributeError:
            self._trees = []
            return self._trees

    #@trees.setter
    #def trees(self, value):
        #self._trees = value

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
        return self.tabs.cursor

    @current.setter
    def current(self, tree):
        if not tree in self.trees:
            self.trees.append(tree)
            tree.manager = self
        self.tabs.cursor = tree

    @property
    def global_schedule_list(self):
        gsl = []
        for tree in self.trees:
            gsl += tree.schedule_list

        gsl.sort(key=lambda t: t.sort_date)

        return gsl

    def outdate_tree_lists(self):
        for tree in self.trees:
            tree.outdate_tree_list()

    @property
    def schedule(self):
        if Config.get("behaviour.global_schedule"):
            return self.global_schedule
        else:
            return self.current.schedule

    def sync_cursors(self):
        if Config.get("behaviour.global_schedule"):
            for tree in self.trees:
                if self.global_schedule.cursor in tree.tree_list:
                    self.current = tree
                    self.current.cursor = self.global_schedule.cursor
                    break

    def next_tab(self):
        self.tabs.next()

    def prev_tab(self):
        self.tabs.prev()

    def open_tree(self, path, set_current=True, parser=TaskTreeParserAuto, name=None):
        if name is None:
            name = path

        pid = check_pidfile(path)
        if pid is None:
            lock_pidfile(path)
        else:
            if is_self(pid):
                self._app.message = "File already opened."
                return
            elif is_running(pid):
                if self._app.get_input("File {} open in another instance. Kill it? (y/n)".format(path)) != "y":
                    return
                else:
                    if kill_and_wait(pid, signal.SIGINT):
                        self._app.message = "PID {} is not reacting to SIGINT.".format(pid)
                        return
                    lock_pidfile(path)
            else:
                if self._app.get_input("Pidfile for {} existing, but no process found. Overwrite pidfile? (y/n)".format(path)) != "y":
                    return
                else:
                    lock_pidfile(path)


        newtree = TaskTree(path, self, parser=parser, name=name)
        self.trees.append(newtree)
        if set_current:
            self.current = newtree

    def close_tree(self, tree):
        if not tree in self.trees:
            raise ValueError("Tree not open")

        index = self.trees.index(tree) - len(self.trees) + 1
        
        self.trees.remove(tree)

        tree.manager = None

        if tree == self.current:
            self.current = self.trees[index]

        remove_pidfile(tree.path)

    def save_all(self):
        for tree in self.trees:
            tree.save()

    def close_current_tree(self):
        self.close_tree(self.current)

    def close_all(self):
        for tree in self.trees:
            self.close_tree(tree)
