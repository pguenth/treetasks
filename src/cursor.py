from anytree import AnyNode, TreeError
from .config import *
import logging

class CursorException(Exception):
    pass

class Scroller:
    def __init__(self, viewport_height, scrolloffset):
        self.viewport_height = viewport_height

        if scrolloffset < 0:
            scrolloffset = 0

        self.scrolloffset = scrolloffset
        self.list = [None]
        self.cursor = None
        self.display_list = [None]

    def get_display_list(self, cursor, current_list):
        if cursor is None:
            self.cursor = cursor
            self.display_list = current_list[:self.viewport_height]
            self.list = current_list

            return self.display_list

#        if not cursor in current_list:
#            raise CursorException("Cursor outside of list. Maybe it moved outside of it?")
#
#        assert cursor in current_list

        if not cursor in current_list:
            logging.warning("Cursor not in current list.")

            self.cursor = None
            self.display_list = current_list[:self.viewport_height]
            self.list = current_list

            return self.display_list
        else:
            index_new = current_list.index(cursor)

        if self.cursor is None:
            index_old = 0
            cursor_line_old = 0
        else:
            assert self.cursor in self.list
            index_old = self.list.index(self.cursor)
            cursor_line_old = self.display_list.index(self.cursor)

        h = self.viewport_height
        cursor_line_new = cursor_line_old + index_new - index_old
        cursor_line_new = max(self.scrolloffset, min(cursor_line_new, h - self.scrolloffset - 1))

        if cursor_line_new >= index_new:
            cursor_line_new = index_new
        elif h - cursor_line_new >= len(current_list) - index_new and h < len(current_list):
            delta = h - cursor_line_new - len(current_list) + index_new
            cursor_line_new = cursor_line_new + delta# + 1

        start = index_new - cursor_line_new 
        self.list = current_list[:]
        self.cursor = cursor
        self.display_list = current_list[start:][:h]

        return self.display_list

class ListCursor:
    def __init__(self, list_descriptor, scrolloffset=0):
        self._list_descriptor = list_descriptor
        self.cursor = None
        self._scroller = Scroller(0, scrolloffset)

    @property
    def cursor(self):
        if not self._cursor in self.list:
            if len(self.list) == 0:
                self._cursor = None
            else:
                self._cursor = self.list[0]

        return self._cursor

    @cursor.setter
    def cursor(self, value):
        if value not in self.list:
            logging.error("setting cursor {} to a value not in the list".format(str(value)[:30]))
        self._cursor = value

    @property
    def list(self):
        return self._list_descriptor.get()

    @property
    def display_list(self):
        return self._scroller.get_display_list(self.cursor, self.list)

    @property
    def viewport_height(self):
        return self._scroller.viewport_height

    @viewport_height.setter
    def viewport_height(self, h):
        self._scroller.viewport_height = h

class TabbarCursor(ListCursor):
    def __init__(self, list_descriptor):
        super().__init__(list_descriptor, Config.get("behaviour.scrolloffset_tabbar"))

    def next(self):
        index = self.list.index(self.cursor)
        index += 1 - len(self.list)
        self.cursor = self.list[index]

    def prev(self):
        index = self.list.index(self.cursor)
        index -= 1
        self.cursor = self.list[index]

class ScheduleCursor(ListCursor):
    def __init__(self, list_descriptor, move_callback):
        super().__init__(list_descriptor, Config.get("behaviour.scrolloffset_schedule"))

        self.move_callback = move_callback

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

class TreeCursor(ListCursor):
    def __init__(self, list_descriptor):
        super().__init__(list_descriptor, Config.get("behaviour.scrolloffset_tree"))

    def move_flat(self, delta):
        tasks = self.list
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

    def _move_hierarchic(self, up=True):
        displayed_children = [t for t in self.list
                                if t in self.cursor.parent.children]

        cursor_index = displayed_children.index(self.cursor)
        end_index = 0 if up else len(displayed_children) - 1

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
                    self._move_hierarchic(False)
            elif Config.get("behaviour.roundtrip"):
                # roundtrip in children
                self.cursor = displayed_children[-1 if up else 0]

        else:
            # normal movement
            delta = -1 if up else 1
            self.cursor = displayed_children[cursor_index + delta]

    def move_hierarchic_up(self):
        self._move_hierarchic(True)

    def move_hierarchic_down(self):
        self._move_hierarchic(False)

    def move_hierarchic(self, delta):
        tasks = self.list

        while delta > 0:
            self._move_hierarchic(False)
            delta -= 1

        while delta < 0:
            self._move_hierarchic(True)
            delta += 1

    def move_treeup(self):
        tasks = self.list

        if isinstance(self.cursor.parent, AnyNode):
            return

        self.cursor = self.cursor.parent
        
    def move_treedown(self):
        tasks = self.list

        # uncollapse if neccessary
        if self.cursor.collapsed:
            self.cursor.toggle_collapse()
            tasks = self.list

        try:
            self.cursor = self.cursor.children[0]
        except:
            raise TreeError("Cursor has no children")
