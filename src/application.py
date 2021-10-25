import curses
import os
import locale
import logging
from datetime import date, timedelta

from .commandhandler import CommandHandler
from .config import Config
from .task import TaskState
from .treemanager import TreeManager
from .geometry import *
from .taskview import ListTask, DescriptionTask, ScheduleTask

locale.setlocale(locale.LC_ALL, '')
lcode = locale.getpreferredencoding()

os.environ.setdefault('ESCDELAY', '25')

class DeepcopySafeCursesWindow:
    def __init__(self, cwindow):
        self.cwindow = cwindow

    def __deepcopy__(self, memo):
        return self

    def __getattr__(self, attr):
        return getattr(self.cwindow, attr)

class TreeTasksApplication:
    def resized(self):
        self._has_resized = True

    def handle_special_key(self, k):
        special_keys = {
                'KEY_RESIZE' : lambda self: self.resized()
        }

        if k in special_keys:
            special_keys[k](self)
            return True
        else:
            return False

    def __init__(self, stdscr):
        #init colors
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        
        curses.curs_set(0)

        self.scr = DeepcopySafeCursesWindow(stdscr)
        self.command_handler = CommandHandler(self)
        self.tm = TreeManager()
        self.message = ""

        self._break_loop = False
        self._has_resized = True

    def run(self):
        self.draw()
        while not self._break_loop:
            try:
                self.loop()
            except KeyboardInterrupt:
                self.tm.save_all()
                self.quit()

    def __call__(self):
        self.run()

    def loop(self):
        k = self.scr.getkey()

        if not self.handle_special_key(k):
            self.command_handler.handle(k)

        if Config.get("behaviour.autosave"):
            self.tm.save_all()

        self.draw()

    def quit(self):
        self._break_loop = True

    def get_input(self, message):
        msgstr = "-> " + message + ": "
        maxh, maxw = self.scr.getmaxyx()
        maxw -= len(msgstr) + 1
        self.scr.addstr(maxh - 1, 0, msgstr) 
        return self.insert(len(msgstr), maxh - 1, maxw)

    def _calculate_coordinates(self):
        h, w = self.scr.getmaxyx()
        self._coordinates = WindowCoordinates.calculated(h, w)

    @property
    def coordinates(self):
        if self._has_resized:
            self._calculate_coordinates()
            self._has_resized = False

        return self._coordinates

    def draw_tasks_decoration(self):
        cols = self.coordinates.columns
        x = self.coordinates.tasks.ul.x + 1
        y = self.coordinates.tasks.ul.y 
        height = self.coordinates.tasks.h

        if 'c' in Config.get("appearance.columns"): 
            self.scr.vline(y, x + cols.category.x - 1, curses.ACS_VLINE, height)
            self.scr.addnstr(y, x + cols.category.x, "Categories", cols.category.w, curses.A_BOLD)
        if 'd' in Config.get("appearance.columns"): 
            self.scr.vline(y, x + cols.due.x - 1, curses.ACS_VLINE, height)
            self.scr.addnstr(y, x + cols.due.x, "Due", cols.due.w, curses.A_BOLD)
        if 's' in Config.get("appearance.columns"): 
            self.scr.vline(y, x + cols.scheduled.x - 1, curses.ACS_VLINE, height)
            self.scr.addnstr(y, x + cols.scheduled.x, "Scheduled", cols.scheduled.w, curses.A_BOLD)

    def draw_tasks(self):
        x = self.coordinates.tasks.ul.x + 1
        y = self.coordinates.tasks.ul.y
        h = self.coordinates.tasks.h

        self.tm.current.viewport_height = h - 1
        dl = self.tm.current.view.display_list
        self.draw_tasks_decoration()
        y += 1

        for i, task in enumerate(dl):
            ListTask(task, RectCoordinates(x, y + i, self.coordinates.tasks.br.x, y + i), self)

    def draw_description(self):
        if not self.tm.current.cursor is None:
            self.description_task = DescriptionTask(self.tm.current.cursor, self.coordinates.descr, self)

    def draw_schedule(self):
        x = self.coordinates.sched.ul.x
        y = self.coordinates.sched.ul.y
        w = self.coordinates.sched.w
        h = self.coordinates.sched.h
        title_str = "Schedule"
        spacing_len = int((w - len(title_str)) / 2)
        spacing = " " * (0 if spacing_len < 0 else spacing_len)
        self.scr.addnstr(y, x, spacing + "Schedule", w, curses.A_BOLD)
        y += 1

        scoords = ScheduleCoordinates(w)
        self.scr.addnstr(y, x + scoords.due_offset, "Due", scoords.datewidth, curses.A_DIM)
        self.scr.addnstr(y, x + scoords.scheduled_offset, "Scheduled", scoords.datewidth, curses.A_DIM)
        y += 2

        max_tasks = int((h - 2) / 3)

        self.tm.schedule.viewport_height = max_tasks
        dl = self.tm.schedule.display_list

        for i, task in enumerate(dl):
            ScheduleTask(task, RectCoordinates(x, y + i * 3, self.coordinates.sched.br.x, y + i * 3 + 3), self)

    def draw_filterstr(self):
        so_cat = self.tm.current.show_only_categories
        hi_cat = self.tm.current.hidden_categories
        if not so_cat is None and len(so_cat) != 0:
            filter_str = " Showing only: " + " ".join(so_cat) + " "
        elif not len(hi_cat) == 0:
            filter_str = " Hiding: " + " ".join(hi_cat) + " "
        else:
            filter_str = ""

        l = len(filter_str)

        self.scr.addstr(self.coordinates.tasks.br.y + 1, self.coordinates.tasks.br.x - l, filter_str, curses.A_DIM)

    def draw_sortkey(self):
        sortkey = self.tm.current.sort_key.name.lower()
        if sortkey == "natural":
            sortkey_str = " Sorted in natural order "
        else:
            sortkey_str = " Sorted by {} ".format(sortkey)

        if self.tm.current.sort_reverse:
            sortkey_str += "(inv) "

        self.scr.addstr(self.coordinates.tasks.br.y + 1, self.coordinates.tasks.ul.x + 1, sortkey_str, curses.A_DIM)

    def draw_tabbar(self, x, w):
        tab_width = Config.get("appearance.tab_width")
        tab_count = int(w / tab_width)
        self.tm.tabs.viewport_height = tab_count
        display_tabs = self.tm.tabs.display_list 

        for t in display_tabs:
            if t == self.tm.current:
                attr = curses.A_STANDOUT
            else:
                attr = curses.A_NORMAL
            tab_name = t.name[-(tab_width - 3):].center(tab_width - 3)
            self.scr.addstr(0, x, "[{}]".format(tab_name), attr)
            x += tab_width

    def draw(self):
        self.scr.erase()
        self.scr.border()

        wintitle = "TreeTasks"
        self.scr.addstr(0, 1, wintitle, curses.A_BOLD)
        y, x = self.scr.getmaxyx()

        self.scr.addstr(y - 1, 0, "-> " + self.message + " ")
        self.draw_tabbar(len(wintitle) + 2, x - 2 - len(wintitle))
        self.draw_tasks()

        if Config.get("appearance.schedule_show"):
            self.draw_schedule()
            self.scr.vline(1, self.coordinates.cross.x, 
                    curses.ACS_VLINE, y - 2)

        if Config.get("appearance.description_show"):
            self.draw_description()
            self.scr.hline(self.coordinates.cross.y, self.coordinates.tasks.ul.x,
                    curses.ACS_HLINE, self.coordinates.cross.x - 1)

        self.draw_filterstr()
        self.draw_sortkey()

        self.scr.refresh()

    def insert(self, x, y, maxc, maxl=1, s="", replace=False):
        # state-machine style bodgy editing/inserting of text
        # initialise editing
        lines = s.splitlines()
        if len(lines) == 0:
            lines.append("")
        curses.curs_set(2)

        # initialise state variables
        cursor_line = len(lines) - 1
        cursor_pos = len(lines[cursor_line])
        old_len = max([len(i) for i in lines])

        # editing loop
        while True:
            # refresh string (and overwrite possible old parts)
            # remove old string
            for line_no in range(maxl):
                self.scr.addstr(y + line_no, x, "".ljust(maxc))
            for line_no, line in enumerate(lines):
                self.scr.addstr(y + line_no, x, line, curses.A_UNDERLINE)

            old_len = max([len(i) for i in lines])

            # move cursor
            self.scr.move(y + cursor_line, x + cursor_pos)

            # wait for char
            k = self.scr.get_wch()
            try:
                logging.debug("Char {}".format(k.encode('utf-8')))
            except AttributeError:
                logging.debug("Char {}".format(k))


            # handle command keys
            if k == curses.KEY_HOME:
                cursor_pos = 0
            elif k == curses.KEY_END:
                cursor_pos = len(lines[cursor_line])
            elif k == curses.KEY_LEFT:
                if not cursor_pos == 0:
                    cursor_pos -= 1
                elif cursor_line != 0:
                    cursor_line -= 1
                    cursor_pos = len(lines[cursor_line])
            elif k == curses.KEY_RIGHT:
                if not cursor_pos == len(lines[cursor_line]):
                    cursor_pos += 1
                elif cursor_line + 1 < len(lines):
                    cursor_line += 1
                    cursor_pos = 0
            elif k == curses.KEY_DOWN:
                if not cursor_line + 1 == len(lines):
                    cursor_line += 1
                    if cursor_pos > len(lines[cursor_line]):
                        cursor_pos = len(lines[cursor_line])
                else:
                    cursor_pos = len(lines[cursor_line])
            elif k == curses.KEY_UP:
                if not cursor_line == 0:
                    cursor_line -= 1
                    if cursor_pos > len(lines[cursor_line]):
                        cursor_pos = len(lines[cursor_line])
                else:
                    cursor_pos = 0
            elif k == curses.KEY_SLEFT:
                if not cursor_pos == 0:
                    cursor_pos -= 1
                while cursor_pos > 0:
                    if lines[cursor_line][cursor_pos] == " ":
                        break
                    cursor_pos -= 1
            elif k == curses.KEY_SRIGHT:
                if not cursor_pos == len(lines[cursor_line]):
                    cursor_pos += 1
                while cursor_pos < len(lines[cursor_line]):
                    if lines[cursor_line][cursor_pos] == " ":
                        break
                    cursor_pos += 1
            elif k == curses.KEY_DC:
                lines[cursor_line] = lines[cursor_line][:cursor_pos] + lines[cursor_line][cursor_pos + 1:]
            elif k == curses.KEY_BACKSPACE or k == b"\x7f".decode("utf-8"):
                # \x7f is shift-backspace on some terminals, backspace on others (VTE for example)
                if not cursor_pos == 0:
                    lines[cursor_line] = lines[cursor_line][:cursor_pos - 1] + lines[cursor_line][cursor_pos:]
                    cursor_pos -= 1
                elif cursor_line != 0:
                    cursor_pos = len(lines[cursor_line - 1])
                    lines[cursor_line - 1] += lines[cursor_line]
                    logging.debug(lines)
                    lines.pop(cursor_line)
                    logging.debug(lines)
                    cursor_line -= 1
            elif k == '\n': # enter
                if maxl == 1:
                    # in the case of single-line editing, enter confirms
                    break

                if cursor_line + 1 < maxl and len(lines) + 1 <= maxl:
                    # if there is capacity for a new line
                    if cursor_pos < len(lines[cursor_line]):
                        # split current line
                        lines.insert(cursor_line + 1, lines[cursor_line][cursor_pos:])
                        lines[cursor_line] = lines[cursor_line][:cursor_pos]
                    else:
                        # add new line
                        lines.insert(cursor_line + 1, "")

                    # move cursors
                    cursor_line += 1
                    cursor_pos = 0
            elif k == b"\x18".decode("utf-8"): #C-x
                lines = None
                break
            elif k == b"\x1b".decode("utf-8"): #escape
                break
            elif type(k) == str:
                if not len(lines[cursor_line]) == maxc:
                    lines[cursor_line] = lines[cursor_line][:cursor_pos] + k + lines[cursor_line][cursor_pos:]
                    cursor_pos += 1

        curses.curs_set(0)

        if lines is None:
            return None

        return '\n'.join(lines)

