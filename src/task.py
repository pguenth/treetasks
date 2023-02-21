from .node import LinkedListNodeMixin, AnyLinkedListNode, AnyTaskTreeAwareNode
import logging
from .config import Config
from enum import Enum
from datetime import date
from anytree import AnyNode


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
            self.root.tasktree.outdate_tree_list()

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
            raise ValueError("Date is not of type date")
        
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
            raise ValueError("Date is not of type date")
        
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


    @property
    def pending(self):
        return self.state == TaskState.PENDING

    @property
    def done_inherited(self):
        if self.cancelled_inherited:
            # if it is cancelled by inheritance, it does not count as done by inheritance under any circumstances
            return False

        return self.done or len([a for a in self.ancestors if not a.is_root and a.done]) > 0

    @property
    def cancelled_inherited(self):
        return self.cancelled or len([a for a in self.ancestors if not a.is_root and a.cancelled]) > 0

    @property
    def pending_inherited(self):
        return self.pending and not self.done_inherited and not self.cancelled_inherited


    def descendants_with(self, condition):
        return [c for c in self.descendants if condition(c)]

    @property
    def descendants_count(self):
        return len(self.descendants)

    @property
    def done_descendants_count(self):
        return len(self.descendants_with(lambda c : c.done))

    @property
    def pending_descendants_count(self):
        return len(self.descendants_with(lambda c : c.pending))

    @property
    def cancelled_descendants_count(self):
        return len(self.descendants_with(lambda c : c.cancelled))

    @property
    def done_inherited_descendants_count(self):
        return len(self.descendants_with(lambda c : c.done_inherited))

    @property
    def pending_inherited_descendants_count(self):
        return len(self.descendants_with(lambda c : c.pending_inherited))

    @property
    def cancelled_inherited_descendants_count(self):
        return len(self.descendants_with(lambda c : c.cancelled_inherited))
    
    @property
    def progress(self):
        d = self.done_inherited_descendants_count
        p = self.pending_inherited_descendants_count
        if d + p == 0:
            return 1 if self.done else 0
        return d / (d + p)

    @property
    def timewarrior_is_tracking(self):
        if Config.get("plugins.timewarrior"):
            import ext.timewarrior as timewarrior
            if timewarrior.is_tracking_task(self, Config.get("plugins.timewarrior_parents_as_tags"), True):
                return True

        return False
