from anytree import NodeMixin, RenderTree, AnyNode, PreOrderIter, TreeError
from enum import Enum
from datetime import date
from .config import Config
from .node import LinkedListNodeMixin, AnyLinkedListNode
from .scroller import Scroller
from .referenced import ReferencedDescriptor
import logging
import datetime

class TaskState(Enum):
    PENDING = 0
    DONE = 1
    CANCELLED = 2

class Task(LinkedListNodeMixin):
    def __init__(self, title, parent=None, children=None, **kwargs):
        self.title = title
        self.parent = parent
        if children:
            self.children = children

        self._fields = {
                'categories' : [],
                'priority' : None,
                'text' : "",
                'state' : TaskState.PENDING,
                'due' : None,
                'scheduled' : None,
                'collapsed' : False
        }

    def __str__(self):
        return "Task '{}', {}, prio {}, due {}, sched {}, {}collapsed, categories: {}, text: '{}'".format(
                self.title, self.state, self.priority, self.due, self.scheduled,
                'not ' if self.collapsed is False else '', self.categories, self.text)

    def _modification_hook(self):
        if isinstance(self.root, AnyTaskTreeAwareNode):
            self.root.tasktree.outdate_display_list()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self._modification_hook()

    @property
    def categories(self):
        return tuple(self._fields['categories'])

    @categories.setter
    def categories(self, value):
        if value is None:
            self._fields['categories'] = []
        else:
            self._fields['categories'] = list(value)
        self._modification_hook()

    def add_category(self, category):
        if not type(category) == str:
            raise ValueError("Categories must be of type str")

        if not category in self.categories: 
            self._fields['categories'].append(category)
        self._modification_hook()

    def remove_category(self, category):
        if category in self.categories:
            self._fields['categories'].remove(category)
        self._modification_hook()

    @property
    def priority(self):
        return self._fields['priority']

    @priority.setter
    def priority(self, value):
        if value is None:
            self._fields['priority'] = None
        else:
            self._fields['priority'] = int(value)
        self._modification_hook()

    @property
    def text(self):
        return self._fields['text']
    
    @text.setter
    def text(self, value):
        self._fields['text'] = str(value)
        self._modification_hook()

    @property
    def state(self):
        return self._fields['state']

    @state.setter
    def state(self, value):
        if not type(value) == type(TaskState.PENDING):
            raise ValueError("State not of enum class type TaskState")

        self._fields['state'] = value
        self._modification_hook()

    def toggle_done(self):
        if self.state == TaskState.PENDING:
            self.state = TaskState.DONE
        elif self.state == TaskState.DONE:
            self.state = TaskState.PENDING
        elif self.state == TaskState.CANCELLED:
            self.state = TaskState.DONE

    def toggle_cancelled(self):
        if self.state == TaskState.PENDING:
            self.state = TaskState.CANCELLED
        elif self.state == TaskState.DONE:
            self.state = TaskState.CANCELLED
        elif self.state == TaskState.CANCELLED:
            self.state = TaskState.PENDING

    @property
    def scheduled(self):
        return self._fields['scheduled']

    @scheduled.setter
    def scheduled(self, value):
        if value is None:
            self._fields['scheduled'] = None
            return

        if not type(value) == date:
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValueError("Date not given as isoformat string")
        
        self._fields['scheduled'] = value
        self._modification_hook()

    @property
    def due(self):
        return self._fields['due']

    @due.setter
    def due(self, value):
        if value is None:
            self._fields['due'] = None
            return

        if not type(value) == date:
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValueError("Date not given as isoformat string")
        
        self._fields['due'] = value
        self._modification_hook()

    @property
    def sort_date(self):
        if self.scheduled is None:
            return self.due

        if self.due is None:
            return self.scheduled

        return min(self.scheduled, self.due)

    @property
    def collapsed(self):
        return self._fields['collapsed']

    @collapsed.setter
    def collapsed(self, value):
        if not type(value) == bool:
            raise ValueError("Collapsed must be set to a boolean value")

        self._fields['collapsed'] = value
        self._modification_hook()

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        return self.collapsed

    @property
    def _category_visible_by_hidden(self):
        assert type(self.root.tasktree.hidden_categories) is set

        intersection = self.root.tasktree.hidden_categories & set(self.categories)
        if len(intersection) == 0:
            return True
        else:
            return False

    @property
    def _category_visible_by_showonly(self):
        assert type(self.root.tasktree.show_only_categories) is set

        so_cat = self.root.tasktree.show_only_categories 
        if not so_cat is None and len(so_cat) != 0:
            intersection = so_cat & set(self.categories)
            if len(intersection) == 0:
                return False
            else:
                return True
        else:
            return None

    @property
    def _category_visible(self):
        for child in self.children:
            if child._category_visible_by_showonly:
                return True

        vis_by_so = self._category_visible_by_showonly
        if not vis_by_so is None:
            return vis_by_so

        return self._category_visible_by_hidden




    @property
    def show(self):
        for ancestor in self.ancestors:
            if not isinstance(ancestor, AnyNode):
                if ancestor.collapsed or not ancestor.show:
                    return False

        if not Config.get("behaviour.show_done") and self.done:
            return False

        if not Config.get("behaviour.show_cancelled") and self.cancelled:
            return False

        return self._category_visible

    @property
    def show_on_schedule(self):
        if self.scheduled is None and self.due is None:
            # not scheduled or due
            return False

        if self.done or self.cancelled:
            # done or cancelled
            return False

        if Config.get("behaviour.filter_categories_schedule"):
            return self._category_visible
        else:
            return True


    @property
    def cancelled(self):
        return self.state == TaskState.CANCELLED
    
    @property
    def done(self):
        return self.state == TaskState.DONE

class Schedule:
    def __init__(self, list_descriptor, move_callback):
        self._list_descriptor = list_descriptor
        self.move_callback = move_callback

        self.cursor = None
        self.scroller = Scroller(0, Config.get("behaviour.scrolloffset_schedule"))

    @property
    def display_list(self):
        return self.scroller.get_display_list(self.cursor, self.list)

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = None if len(self.list) == 0 else self.list[0]

        return self._cursor

    @cursor.setter
    def cursor(self, value):
        self._cursor = value

    @property
    def list(self):
        return self._list_descriptor.get()

    def move_up(self):
        index = self.list.index(self.cursor)
        self.cursor= self.list[max(0, index - 1)]

        self.move_callback()

    def move_down(self):
        index = self.list.index(self.cursor)
        self.cursor= self.list[min(len(self.list) - 1, index + 1)]

        self.move_callback()

    def move_top(self):
        self.cursor = self.list[0]

        self.move_callback()

    def move_today(self):
        while self.cursor.sort_date > date.today():
            self.move_up()

        while self.cursor.sort_date < date.today():
            self.move_down()

        self.move_callback()


class TaskTreeSortKey(Enum):
    NATURAL = 0
    TITLE = 1
    PRIORITY = 2
    DUE = 3
    SCHEDULED = 4
    CATEGORY = 5
    DATE = 6

class AnyTaskTreeAwareNode(AnyLinkedListNode):
    def __init__(self, tasktree):
        super().__init__()
        self.tasktree = tasktree

class TaskTree:
    def __init__(self, path, manager, parser, name=None):
        self.path = path

        if name is None:
            name = path

        self.name = name
        self.root = AnyTaskTreeAwareNode(self)
        self.parser = parser()
        self.cursor = None
        self.manager = manager
        self.schedule = Schedule(ReferencedDescriptor(TaskTree.schedule_list, self), self.sync_cursors)

        self.scroller_tree = Scroller(0, Config.get("behaviour.scrolloffset_tree"))

        self.sort_key = TaskTreeSortKey.NATURAL
        self.sort_reverse = False
        
        # if show_only_categories is not empty, hidden_categories is ignored
        self.hidden_categories = set()
        self.show_only_categories = set() 

        try:
            open(self.path, mode='r')
        except FileNotFoundError:
            first_task = Task("empty", parent=self.root)
        else:
            self.parser.load(self.path, self.root)

        self.cursor = None if len(self.display_list) == 0 else self.display_list[0]
        self._display_list_outdated = True
        self._display_list_cache = None

    @property
    def cursor(self):
        # try setting the cursor to the first element in the display list
        # if it somehow vanished
        dl = self.display_list
        if not self._cursor in dl and not len(dl) == 0:
            self._cursor = dl[0]

        return self._cursor

    @cursor.setter
    def cursor(self, cursor):
        self._cursor = cursor

    @property
    def sort_reverse(self):
        return self._sort_reverse

    @sort_reverse.setter
    def sort_reverse(self, value):
        self._sort_reverse = value
        self.outdate_display_list()

    @property
    def sort_key(self):
        return self._sort_key

    @sort_key.setter
    def sort_key(self, value):
        self._sort_key = value
        self.outdate_display_list()

    def outdate_display_list(self):
        self._display_list_outdated = True

    def _regen_display_list(self):
        self.update_order()

        def filt(task):
            if not isinstance(task, AnyNode):
                return task.show
            else:
                return False

        tasks = list(PreOrderIter(self.root, filt))

        self._display_list_cache = tasks
        self._display_list_outdated = False
            
    @property
    def display_list(self):
        if self._display_list_outdated or self._display_list_cache is None:
            self._regen_display_list()

        return self._display_list_cache


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
        self.outdate_display_list()

    def unhide_categories(self, categories):
        self.hidden_categories -= set(categories)
        self.outdate_display_list()

    def unhide_all_categories(self):
        self.hidden_categories = set()
        self.outdate_display_list()

    @property
    def show_only_categories(self):
        return self._show_only_categories

    @show_only_categories.setter
    def show_only_categories(self, categories):
        self._show_only_categories = set(categories)
        self.outdate_display_list()

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
        self.parser.save(self.path, self.root)

        Config.set("behaviour.sort_tagged_below", stb)

    def sync_cursors(self):
        if Config.get("behaviour.follow_schedule") and self.schedule.cursor in self.display_list:
            self.cursor = self.schedule.cursor


    def move_cursor_flat(self, delta):
        tasks = self.display_list
        index_new = tasks.index(self.cursor) + delta

        # roundtrip
        if index_new >= len(tasks):
            if Config.get("behaviour.roundtrip"):
                index_new -= len(tasks)
            else:
                index_new = len(tasks) - 1
        elif index_new < 0:
            if Config.get("behaviour.roundtrip"):
                index_new += len(tasks)
            else:
                index_new = 0

        self.cursor = tasks[index_new]

    def _move_cursor_hierarchic(self, up=True):
        displayed_children = [t for t in self.display_list
                                if t in self.cursor.parent.children]

        cursor_index = displayed_children.index(self.cursor)
        end_index = 0 if up else len(displayed_children) - 1
        logging.error("newmove")

        if len(displayed_children) == 1 or cursor_index == end_index:
            if     (isinstance(self.cursor.parent, AnyNode) and
                    Config.get("behaviour.roundtrip")):
                # roundtrip in root level
                self.cursor = displayed_children[-1 if up else 0]
            elif   (not isinstance(self.cursor.parent, AnyNode) and
                    Config.get("behaviour.auto_move_up")):
                # auto move up
                self.move_treeup()
                if not up:
                    self._move_cursor_hierarchic(False)
            elif Config.get("behaviour.roundtrip"):
                # roundtrip in children
                self.cursor = displayed_children[-1 if up else 0]

        else:
            # normal movement
            delta = -1 if up else 1
            self.cursor = displayed_children[cursor_index + delta]

    def move_cursor_hierarchic_up(self):
        self._move_cursor_hierarchic(True)

    def move_cursor_hierarchic_down(self):
        self._move_cursor_hierarchic(False)

    def move_cursor_hierarchic(self, delta):
        tasks = self.display_list

        while delta > 0:
            self._move_cursor_hierarchic(False)
            delta -= 1

        while delta < 0:
            self._move_cursor_hierarchic(True)
            delta += 1

    def move_treeup(self):
        tasks = self.display_list

        if isinstance(self.cursor.parent, AnyNode):
            return
            #raise TreeError("Cursor is on top level")

        self.cursor = self.cursor.parent
        
    def move_treedown(self):
        tasks = self.display_list

        # uncollapse if neccessary
        if self.cursor.collapsed:
            self.cursor.toggle_collapse()
            tasks = self.display_list

        try:
            self.cursor = self.cursor.children[0]
        except:
            raise TreeError("Cursor has no children")
        
        
    def _new_task_child_top(self, parent):
        ntask = Task("")

        if parent.first_link_child is None:
            ntask.parent = parent
        else:
            parent.first_link_child.insert_before(ntask)

        self.cursor = ntask
        self.outdate_display_list()
        return ntask

    def _new_task_child_bottom(self, parent):
        ntask = Task("")
        
        if parent.last_link_child is None:
            ntask.parent = parent
        else:
            parent.last_link_child.insert_after(ntask)

        self.cursor = ntask
        self.outdate_display_list()
        return ntask

    def new_task_child_top(self):
        return self._new_task_child_top(self.cursor)

    def new_task_child_bottom(self):
        return self._new_task_child_bottom(self.cursor)

    def new_task_sibling_top(self):
        return self._new_task_child_top(self.cursor.parent)

    def new_task_sibling_bottom(self):
        return self._new_task_child_bottom(self.cursor.parent)

    def new_task_sibling_above(self):
        ntask = Task("", parent=self.cursor.parent)
        self.cursor.insert_before(ntask)
        self.cursor = ntask
        self.outdate_display_list()
        return ntask

    def new_task_sibling_below(self):
        ntask = Task("", parent=self.cursor.parent)
        self.cursor.insert_after(ntask)
        self.cursor = ntask
        self.outdate_display_list()
        return ntask

    def new_task_top(self):
        return self._new_task_child_top(self.root)

    def new_task_bottom(self):
        return self._new_task_child_bottom(self.root)

    def move_selected_task_up(self):
        task = self.cursor
        parentchildren = [c for c in self.cursor.parent.children if c.show]
        parentindex = parentchildren.index(task)

        amu = Config.get("behaviour.auto_move_up")
        Config.set("behaviour.auto_move_up", False)
        self.move_cursor_hierarchic_up()
        Config.set("behaviour.auto_move_up", amu)

        if len(parentchildren) == 1 or parentindex == 0:
            self.paste(task=task, before=False, below=False)
        else:
            self.paste(task=task, before=True, below=False)
        self.cursor = task

    def move_selected_task_down(self):
        task = self.cursor
        parentchildren = [c for c in self.cursor.parent.children if c.show]
        parentindex = parentchildren.index(task)

        amu = Config.get("behaviour.auto_move_up")
        Config.set("behaviour.auto_move_up", False)
        self.move_cursor_hierarchic_down()
        Config.set("behaviour.auto_move_up", amu)

        if len(parentchildren) == 1 or parentindex == len(parentchildren) - 1:
            self.paste(task=task, before=True, below=False)
        else:
            self.paste(task=task, before=False, below=False)
        self.cursor = task

    def move_selected_task_treeup(self):
        if isinstance(self.cursor.parent, AnyNode):
            return

        task = self.cursor
        self.move_treeup()
        self.paste(task=task, before=True, below=False)
        self.cursor = task

    def _move_schedule_before_deleting(self):
        if len(self.manager.schedule_in_use.list) == 1:
            self.manager.schedule_in_use.cursor = None
        else:
            self.manager.schedule_in_use.move_up()

    def _move_before_deleting(self):
        if len(self.cursor.siblings) == 0:
            self.move_treeup()
        else:
            self.move_cursor_hierarchic_down()


    def _delete_or_cut(self, cut=False, task=None):
        if task is None:
            task = self.cursor

        if not task in PreOrderIter(self.root):
            raise TreeError("Given task not in tree")

        if task == self.cursor:
            self._move_before_deleting()

        if task == self.manager.schedule_in_use.cursor:
            self._move_schedule_before_deleting()

        task.parent = None

        if cut:
            self.manager.clipboard = task
        else:
            del task

        self.outdate_display_list()

    def delete(self, task=None):
        self._delete_or_cut(cut=False, task=task)

    def cut(self, task=None):
        self._delete_or_cut(cut=True, task=task)

    def paste(self, task=None, before=False, below=True):
        if task is None:
            task = self.manager.clipboard

        if task is None:
            return

        if below and before:
            self.cursor.insert_as_first_child(task)
        elif not below and before:
            self.cursor.insert_before(task)
        elif below and not before:
            self.cursor.insert_as_last_child(task)
        elif not below and not before:
            self.cursor.insert_after(task)
        
        self.outdate_display_list()

    def copy_cursor(self):
        self.manager.clipboard = self.cursor
