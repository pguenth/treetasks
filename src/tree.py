from anytree import NodeMixin, RenderTree, AnyNode, PreOrderIter, TreeError
from enum import Enum
from datetime import date
import xml.etree.ElementTree as ET
from .config import Config
from .node import LinkedListNodeMixin, AnyLinkedListNode
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

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def categories(self):
        return tuple(self._fields['categories'])

    @categories.setter
    def categories(self, value):
        self._fields['categories'] = list(value)

    def add_category(self, category):
        if not type(category) == str:
            raise ValueError("Categories must be of type str")

        if not category in self.categories: 
            self._fields['categories'].append(category)

    def remove_category(self, category):
        if category in self.categories:
            self._fields['categories'].remove(category)

    @property
    def priority(self):
        return self._fields['priority']

    @priority.setter
    def priority(self, value):
        self._fields['priority'] = int(value)

    @property
    def text(self):
        return self._fields['text']
    
    @text.setter
    def text(self, value):
        self._fields['text'] = str(value)

    @property
    def state(self):
        return self._fields['state']

    @state.setter
    def state(self, value):
        if not type(value) == type(TaskState.PENDING):
            raise ValueError("State not of enum class type TaskState")

        self._fields['state'] = value

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
        if not type(value) == date:
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValueError("Date not given as isoformat string")
        
        self._fields['scheduled'] = value

    @property
    def due(self):
        return self._fields['due']

    @due.setter
    def due(self, value):
        if not type(value) == date:
            try:
                value = date.fromisoformat(value)
            except ValueError:
                raise ValueError("Date not given as isoformat string")
        
        self._fields['due'] = value

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

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        return self.collapsed


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

        return True

    @property
    def cancelled(self):
        return self.state == TaskState.CANCELLED
    
    @property
    def done(self):
        return self.state == TaskState.DONE

class TaskTreeParserXML:
    @staticmethod
    def _parse_recursive(elem, parent):
        if not elem.tag == 'todo':
            raise ValueError("No Todo given")

        # find title and create tree node
        title_element = elem.find('title')
        if title_element is None:
            raise ValueError("Given Todo has no title")

        title = title_element.text
        node = Task(title, parent)

        # parse attributes
        if 'collapse' in elem.attrib:
            node.collapsed = True if elem.attrib['collapse'] == "yes" else False

        if 'done' in elem.attrib and elem.attrib['done'] == "yes":
            node.state = TaskState.DONE

        if 'cancelled' in elem.attrib and elem.attrib['cancelled'] == "yes":
            node.state = TaskState.CANCELLED

        # parse children
        for child in elem:
            if child.tag == "text":
                node.text = child.text

            elif child.tag == "category":
                node.add_category(child.text)

            elif child.tag == "todo":
                TaskTreeParserXML._parse_recursive(child, node)

            elif child.tag == "deadline":
                node.due = date(int(child.find("year").text), int(child.find("month").text), int(child.find("day").text))

            elif child.tag == "scheduled":
                node.scheduled = date(int(child.find("year").text), int(child.find("month").text), int(child.find("day").text))

            elif child.tag == "priority":
                node.priority = int(child.text)

        return node

    @staticmethod
    def _encode_recursive(task, this_element):
        this_element.set('collapse', 'yes' if task.collapsed else 'no')
        if task.state == TaskState.DONE:
            this_element.set('done', 'yes')
            this_element.set('cancelled', 'no')
        elif task.state == TaskState.CANCELLED:
            this_element.set('done', 'no')
            this_element.set('cancelled', 'yes')
        elif task.state == TaskState.PENDING:
            this_element.set('done', 'no')
            this_element.set('cancelled', 'no')

        ET.SubElement(this_element, 'title').text = task.title
        ET.SubElement(this_element, 'text').text = task.text
        
        for cat in task.categories:
            ET.SubElement(this_element, 'category').text = cat

        for child in task.children:
            c_elem = ET.SubElement(this_element, 'todo')
            TaskTreeParserXML._encode_recursive(child, c_elem)

        if not task.due is None:
            deadline_elem = ET.SubElement(this_element, 'deadline')
            ET.SubElement(deadline_elem, 'day').text = str(task.due.day)
            ET.SubElement(deadline_elem, 'month').text = str(task.due.month)
            ET.SubElement(deadline_elem, 'year').text = str(task.due.year)

        if not task.scheduled is None:
            schedule_elem = ET.SubElement(this_element, 'scheduled')
            ET.SubElement(schedule_elem, 'day').text = str(task.scheduled.day)
            ET.SubElement(schedule_elem, 'month').text = str(task.scheduled.month)
            ET.SubElement(schedule_elem, 'year').text = str(task.scheduled.year)
            ET.SubElement(schedule_elem, 'position').text = str(1) # dont know what this tag means for tudu

        if not task.priority is None:
            ET.SubElement(this_element, 'priority').text = str(task.priority)

        return this_element

    @staticmethod
    def load(path, root_node):
        tree = ET.parse(path)
        root = tree.getroot()

        for child in root:
            TaskTreeParserXML._parse_recursive(child, root_node)

    @staticmethod
    def save(path, root_node):
        root = ET.Element('todo')
        for child in root_node.children:
            c_elem = ET.SubElement(root, 'todo')
            TaskTreeParserXML._encode_recursive(child, c_elem)


        with open(path, mode='w') as f:
            f.write(ET.tostring(root, encoding='unicode'))

class TaskTreeParserJSON:
    @staticmethod 
    def load(path, root_node):
        pass

    @staticmethod
    def save(path, root_node):
        pass


class TaskTreeSortKey(Enum):
    NATURAL = 0
    TITLE = 1
    PRIORITY = 2
    DUE = 3
    SCHEDULED = 4
    CATEGORY = 5

class TaskTree:
    def __init__(self, path, manager, parser=TaskTreeParserXML):
        self.path = path
        self.root = AnyLinkedListNode()
        self.parser = parser()
        self.cursor = None
        self.manager = manager

        self.sort_key = TaskTreeSortKey.NATURAL
        self.sort_reverse = False

        self.parser.load(self.path, self.root)
        self.cursor = self.display_list[0]
        self.cursor_sched = self.schedule_list[0]

    @property
    def display_list(self):
        self.update_order()

        def filt(task):
            if not isinstance(task, AnyNode):
                return task.show
            else:
                return False

        tasks = list(PreOrderIter(self.root, filt))
        return tasks

    @property
    def schedule_list(self):
        def filt(task):
            if isinstance(task, AnyNode):
                return False
            if task.scheduled is None and task.due is None:
                return False

            return True

        sched_list = list(PreOrderIter(self.root, filt))
        sched_list.sort(key=lambda t: t.sort_date)

        return sched_list

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

    def set_order(self, key, reverse=False):
        self.sort_key = key
        self.sort_reverse = reverse
    
    def save(self):
        self._sort_natural()
        self.parser.save(self.path, self.root)

    def sync_cursors(self):
        if Config.get("behaviour.follow_schedule") and self.cursor_sched in self.display_list:
            self.cursor = self.cursor_sched

    def move_schedule_up(self):
        index = self.schedule_list.index(self.cursor_sched)
        self.cursor_sched = self.schedule_list[max(0, index - 1)]

        self.sync_cursors()

    def move_schedule_down(self):
        index = self.schedule_list.index(self.cursor_sched)
        self.cursor_sched = self.schedule_list[min(len(self.schedule_list) - 1, index + 1)]

        self.sync_cursors()

    def move_schedule_top(self):
        self.cursor_sched = self.schedule_list[0]

        self.sync_cursors()

    def move_schedule_today(self):
        while self.cursor_sched.sort_date < date.today():
            self.move_schedule_down()

        while self.cursor_sched.sort_date > date.today():
            self.move_schedule_up()

        self.sync_cursors()

    def move_cursor_flat(self, delta):
        tasks = self.display_list
        index_new = tasks.index(self.cursor) + delta

        # roundtrip
        if index_new >= len(tasks):
            index_new -= len(tasks)
        elif index_new < 0:
            index_new += len(tasks)
        self.cursor = tasks[index_new]

    def move_cursor_hierarchic_up(self):
        parentchildren = [c for c in self.cursor.parent.children if c.show]
        if len(parentchildren) == 1 or parentchildren.index(self.cursor) == 0:
            if isinstance(self.cursor.parent, AnyNode):
                self.cursor = parentchildren[-1]
            else:
                self.move_treeup()
        else:
            self.cursor = parentchildren[parentchildren.index(self.cursor) - 1]

    def move_cursor_hierarchic_down(self):
        parentchildren = [c for c in self.cursor.parent.children if c.show]
        if len(parentchildren) == 1 or parentchildren.index(self.cursor) == len(parentchildren) - 1:
            if isinstance(self.cursor.parent, AnyNode):
                self.cursor = parentchildren[0]
            else:
                self.move_treeup()
                self.move_cursor_hierarchic_down()
        else:
            self.cursor = parentchildren[parentchildren.index(self.cursor) + 1]

    def move_cursor_hierarchic(self, delta):
        tasks = self.display_list

        while delta > 0:
            self.move_cursor_hierarchic_down()
            delta -= 1

        while delta < 0:
            self.move_cursor_hierarchic_up()
            delta += 1

    def move_treeup(self):
        tasks = self.display_list

        if type(self.cursor.parent) is AnyNode:
            raise TreeError("Cursor is on top level")

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
        return ntask

    def _new_task_child_bottom(self, parent):
        ntask = Task("")
        
        if parent.last_link_child is None:
            ntask.parent = parent
        else:
            parent.last_link_child.insert_after(ntask)

        self.cursor = ntask
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
        return ntask

    def new_task_sibling_below(self):
        ntask = Task("", parent=self.cursor.parent)
        self.cursor.insert_after(ntask)
        self.cursor = ntask
        return ntask

    def new_task_top(self):
        return self._new_task_child_top(self.root)

    def new_task_bottom(self):
        return self._new_task_child_bottom(self.root)

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

        task.parent = None

        if cut:
            self.manager.clipboard = task
        else:
            del task

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

    def insert_clipboard_after(self):
        if not self.manager.clipboard is None:
            self.insert_after_cursor(self.manager.clipboard)

    def insert_clipboard_before(self):
        if not self.manager.clipboard is None:
            self.insert_before_cursor(self.clipboard)

    def copy_cursor(self):
        self.manager.clipboard = self.cursor


def convert_parser(path_in, path_out, parser_in, parser_out):
    tree = TaskTree(path_in, None, parser_in)
    tree.path = path_out
    tree.parser = parser_out
    tree.save()
