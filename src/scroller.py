import logging

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
            logging.debug("C is None")
            self.cursor = cursor
            self.display_list = current_list[:self.viewport_height]
            self.list = current_list

            return self.display_list

        assert cursor in current_list

        logging.debug("gdl")
        logging.debug(self.list)
        logging.debug(self.cursor)
        logging.debug(current_list)
        logging.debug(cursor)
        index_new = current_list.index(cursor)
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
        self.list = current_list
        self.cursor = cursor
        self.display_list = current_list[start:][:h]

        return self.display_list
