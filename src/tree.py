from anytree import NodeMixin, RenderTree, AnyNode, PreOrderIter, TreeError
from enum import Enum
from .config import Config
from .node import LinkedListNodeMixin, AnyLinkedListNode, AnyTaskTreeAwareNode
from .referenced import ReferencedDescriptor
from .cursor import ScheduleCursor, TreeCursor
from .task import Task
import logging
import datetime

class TaskTreeSortKey(Enum):
    NATURAL = 0
    TITLE = 1
    PRIORITY = 2
    DUE = 3
    SCHEDULED = 4
    CATEGORY = 5
    DATE = 6


class TaskTree:
    def __init__(self, path, manager, parser, name=None):
        self.path = path

        if name is None:
            name = path

        self.manager = manager
        self.name = name
        self.root = AnyTaskTreeAwareNode(self)
        self.parser = parser()

        self._tree_list_outdated = True
        self._tree_list_cache = None

        self.sort_key = TaskTreeSortKey.NATURAL
        self.sort_reverse = False

        self.schedule = ScheduleCursor(ReferencedDescriptor(TaskTree.schedule_list, self),
                                 self.sync_cursors)
        self.view = TreeCursor(ReferencedDescriptor(TaskTree.tree_list, self))
        
        # if show_only_categories is not empty, hidden_categories is ignored
        self.hidden_categories = set()
        self.show_only_categories = set() 

        try:
            open(self.path, mode='r')
        except FileNotFoundError:
            first_task = Task("empty", parent=self.root)
        else:
            self.parser.load(self.path, self)

    @property
    def hidden_categories(self):
        return self._hidden_categories

    @hidden_categories.setter
    def hidden_categories(self, categories):
        self._hidden_categories = set(categories)
        self.outdate_tree_list()

    @property
    def viewport_height(self):
        return self.view.viewport_height

    @viewport_height.setter
    def viewport_height(self, h):
        self.view.viewport_height = h

    @property
    def cursor(self):
        return self.view.cursor

    @cursor.setter
    def cursor(self, c):
        self.view.cursor = c

    @property
    def sort_reverse(self):
        return self._sort_reverse

    @sort_reverse.setter
    def sort_reverse(self, value):
        self._sort_reverse = value
        self.outdate_tree_list()

    @property
    def sort_key(self):
        return self._sort_key

    @sort_key.setter
    def sort_key(self, value):
        self._sort_key = value
        self.outdate_tree_list()

    def outdate_tree_list(self):
        self._tree_list_outdated = True

    def _regen_tree_list(self):
        self.update_order()

        def filt(task):
            if not isinstance(task, AnyNode):
                return task.show
            else:
                return False

        tasks = list(PreOrderIter(self.root, filt))

        self._tree_list_cache = tasks
        self._tree_list_outdated = False
            
    @property
    def tree_list(self):
        if self._tree_list_outdated or self._tree_list_cache is None:
            self._regen_tree_list()

        return self._tree_list_cache


    @property
    def schedule_list(self):
        def filt(task):
            if not isinstance(task, AnyNode):
                return task.show_on_schedule
            else:
                return False

        sched_list = list(PreOrderIter(self.root, filt))
        sched_list.sort(key=lambda t: t.sort_date)

        return sched_list

    def hide_categories(self, categories):
        self.hidden_categories |= set(categories)

    def unhide_categories(self, categories):
        self.hidden_categories -= set(categories)

    def unhide_all_categories(self):
        self.hidden_categories = set()

    @property
    def show_only_categories(self):
        return self._show_only_categories

    @show_only_categories.setter
    def show_only_categories(self, categories):
        self._show_only_categories = set(categories)
        self.outdate_tree_list()

    def _sort(self, key):
        self.root.sort_tree(key=key, reverse=self.sort_reverse)

        if Config.get("behaviour.sort_tagged_below"):
            self.root.sort_tree(key=lambda t: t.done or t.cancelled)

    def _sort_natural(self):
        self.root.sort_tree_link(reverse=self.sort_reverse)

        if Config.get("behaviour.sort_tagged_below"):
            self.root.sort_tree(key=lambda t: t.done or t.cancelled)

    def update_order(self):
        if self.sort_key == TaskTreeSortKey.NATURAL:
            self._sort_natural()
        elif self.sort_key == TaskTreeSortKey.TITLE:
            self._sort(lambda t: t.title)
        elif self.sort_key == TaskTreeSortKey.CATEGORY:
            def k(t):
                if len(t.categories) == 0:
                    return ''
                else:
                    return t.categories[0]
            self._sort(k)
        elif self.sort_key == TaskTreeSortKey.DUE:
            self._sort(lambda t: t.due if not t.due is None else datetime.date(2100,1,1))
        elif self.sort_key == TaskTreeSortKey.SCHEDULED:
            self._sort(lambda t: t.scheduled if not t.scheduled is None else datetime.date(2100,1,1))
        elif self.sort_key == TaskTreeSortKey.PRIORITY:
            self._sort(lambda t: t.priority if not t.priority is None else 10)
        elif self.sort_key == TaskTreeSortKey.DATE:
            def k(t):
                sort_date = t.sort_date
                return sort_date if not sort_date is None else datetime.date(2100, 1, 1)

            self._sort(k)

    def set_order(self, key, reverse=False):
        self.sort_key = key
        self.sort_reverse = reverse
    
    def save(self):
        stb = Config.get("behaviour.sort_tagged_below")
        Config.set("behaviour.sort_tagged_below", False)

        self._sort_natural()
        self.parser.save(self.path, self)

        Config.set("behaviour.sort_tagged_below", stb)

    def sync_cursors(self):
        if Config.get("behaviour.follow_schedule") and self.schedule.cursor in self.tree_list:
            self.cursor = self.schedule.cursor
        
    def _new_task_child(self, parent, top=True):
        ntask = Task("")

        if top:
            relevant_child = parent.first_link_child
        else:
            relevant_child = parent.last_link_child

        if relevant_child is None:
            ntask.parent = parent
        else:
            relevant_child.insert(ntask, before=top)

        self.cursor = ntask
        self.outdate_tree_list()
        return ntask

    def new_task_child(self, top=True):
        return self._new_task_child(self.cursor, top=top)

    def new_task_child_top(self):
        return self.new_task_child(True)

    def new_task_child_bottom(self):
        return self.new_task_child(False)

    def new_task_sibling_end(self, top=True):
        return self._new_task_child(self.cursor.parent, top=top)

    def new_task_sibling_top(self):
        return self.new_task_sibling_end(True)

    def new_task_sibling_bottom(self):
        return self.new_task_sibling_end(False)

    def new_task_sibling_besides(self, before=True):
        ntask = Task("", parent=self.cursor.parent)
        self.cursor.insert(ntask, before=before)
        self.cursor = ntask
        self.outdate_tree_list()
        return ntask

    def new_task_sibling_before(self):
        return self.new_task_sibling_besides(before=True)

    def new_task_sibling_after(self):
        return self.new_task_sibling_besides(before=False)

    def new_task_top(self):
        return self._new_task_child(self.root, top=True)

    def new_task_bottom(self):
        return self._new_task_child(self.root, top=False)

    def move_selected_task(self, up=True):
        task = self.cursor
        displayed_children = [t for t in self.tree_list
                                if t in self.cursor.parent.children]
        cursor_index = displayed_children.index(task)

        amu = Config.get("behaviour.auto_move_up")
        Config.set("behaviour.auto_move_up", False)
        self.view.move_hierarchic(delta=(-1 if up else 1))
        Config.set("behaviour.auto_move_up", amu)

        if task == self.cursor:
            return

        end_index = 0 if up else len(displayed_children) - 1
        if cursor_index == end_index:
            self.paste(task=task, before=(not up), below=False)
        else:
            self.paste(task=task, before=up, below=False)

        self.cursor = task

    def move_selected_task_up(self):
        self.move_selected_task(True)

    def move_selected_task_down(self):
        self.move_selected_task(False)

    def move_selected_task_treeup(self):
        if isinstance(self.cursor.parent, AnyNode):
            return

        task = self.cursor
        self.view.move_treeup()
        self.paste(task=task, before=True, below=False)
        self.cursor = task

    def _move_schedule_before_deleting(self):
        if len(self.manager.schedule.list) == 1:
            self.manager.schedule.cursor = None
        else:
            self.manager.schedule.move_up()

    def _move_before_deleting(self):
        if len(self.cursor.siblings) == 0:
            self.view.move_treeup()
        else:
            self.view.move_hierarchic_down()

    def _delete_or_cut(self, cut=False, task=None):
        if task is None:
            task = self.cursor

        if not task in PreOrderIter(self.root):
            raise TreeError("Given task not in tree")

        if task == self.cursor:
            self._move_before_deleting()

        if task == self.manager.schedule.cursor:
            self._move_schedule_before_deleting()

        task.parent = None

        if cut:
            self.manager.clipboard = task
        else:
            del task

        self.outdate_tree_list()

    def delete(self, task=None):
        self._delete_or_cut(cut=False, task=task)

    def cut(self, task=None):
        self._delete_or_cut(cut=True, task=task)

    def paste(self, task=None, before=False, below=True):
        if task is None:
            task = self.manager.clipboard

        if task is None:
            return

        if self.cursor == task:
            raise TreeError("Cannot paste a task relative to itself (task == cursor)")

        if below and before:
            self.cursor.insert_as_first_child(task)
        elif not below and before:
            self.cursor.insert_before(task)
        elif below and not before:
            self.cursor.insert_as_last_child(task)
        elif not below and not before:
            self.cursor.insert_after(task)
        
        self.outdate_tree_list()

    def copy_cursor(self):
        self.manager.clipboard = self.cursor
