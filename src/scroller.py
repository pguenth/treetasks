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
