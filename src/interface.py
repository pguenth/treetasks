import curses
import copy
import os
import locale
import logging

from anytree import PreOrderIter, TreeError

from .config import Config
from .state import State
from .tree import TaskState, TaskTreeSortKey
from .geometry import *
from .taskview import ListTask, DescriptionTask, ScheduleTask

locale.setlocale(locale.LC_ALL, '')
lcode = locale.getpreferredencoding()

os.environ.setdefault('ESCDELAY', '25')

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Commands:
    @staticmethod
    def edit_scheduled():
        State.tm.current.cursor.listview.scheduled.edit(Window)
        
    @staticmethod
    def edit_priority():
        State.tm.current.cursor.listview.priority.edit(Window, replace=True)

    @staticmethod
    def edit_due():
        State.tm.current.cursor.listview.due.edit(Window)

    @staticmethod
    def edit_categories():
        State.tm.current.cursor.listview.categories.edit(Window)

    @staticmethod
    def edit_title():
        State.tm.current.cursor.listview.title.edit(Window)

    @staticmethod
    def replace_title():
        State.tm.current.cursor.listview.title.edit(Window)

    @staticmethod
    def edit_text():
        State.tm.current.cursor.descriptionview.text.edit(Window)

    @staticmethod
    def sort_title(reverse=False):
        State.tm.current.set_order(TaskTreeSortKey.TITLE, reverse)

    @staticmethod
    def sort_category(reverse=False):
        State.tm.current.set_order(TaskTreeSortKey.CATEGORY, reverse)

    @staticmethod
    def sort_due(reverse=False):
        State.tm.current.set_order(TaskTreeSortKey.DUE, reverse)

    @staticmethod
    def sort_scheduled(reverse=False):
        State.tm.current.set_order(TaskTreeSortKey.SCHEDULED, reverse)

    @staticmethod
    def sort_natural(reverse=False):
        State.tm.current.set_order(TaskTreeSortKey.NATURAL, reverse)

    @staticmethod
    def sort_priority(reverse=False):
        State.tm.current.set_order(TaskTreeSortKey.PRIORITY, reverse)

    @staticmethod
    def down():
        State.tm.current.move_cursor_hierarchic(1)

    @staticmethod
    def up():
        State.tm.current.move_cursor_hierarchic(-1)

    @staticmethod
    def down_flat():
        State.tm.current.move_cursor_flat(1)

    @staticmethod
    def up_flat():
        State.tm.current.move_cursor_flat(-1)

    @staticmethod
    def cut_task():
        State.tm.current.cut()

    @staticmethod
    def delete_task():
        State.tm.current.delete()

    @staticmethod
    def copy_cursor():
        State.tm.current.copy_cursor()

    @staticmethod
    def paste_after():
        State.tm.current.paste(below=False, before=False)

    @staticmethod
    def paste_before():
        State.tm.current.paste(below=False, before=True)

    @staticmethod
    def paste_below_append():
        State.tm.current.paste(below=True, before=False)

    @staticmethod
    def paste_below_prepend():
        State.tm.current.paste(below=True, before=True)

    @staticmethod
    def _new_task_edit(new_task):
        Window.draw()
        Commands.edit_title()
        if new_task.title == "":
            State.tm.current.delete(new_task)
            return False
        else:
            return True

    @staticmethod
    def new_task_child_bottom():
        new_task = State.tm.current.new_task_child_bottom()
        Commands._new_task_edit(new_task)

    @staticmethod
    def new_task_child_top():
        new_task = State.tm.current.new_task_child_bottom()
        Commands._new_task_edit(new_task)

    @staticmethod
    def new_task_above():
        new_task = State.tm.current.new_task_sibling_above()
        Commands._new_task_edit(new_task)

    @staticmethod
    def new_task_below():
        new_task = State.tm.current.new_task_sibling_below()
        if not Commands._new_task_edit(new_task):
            Commands.up()

    @staticmethod
    def left():
        try:
            State.tm.current.move_treeup()
        except TreeError:
            pass

    @staticmethod
    def right():
        try:
            State.tm.current.move_treedown()
        except TreeError:
            Commands.new_task_child_top()

    @staticmethod
    def collapse():
        State.tm.current.cursor.toggle_collapse()

    @staticmethod
    def toggle_done():
        c = State.tm.current.cursor
        if not Config.get("behaviour.show_done"):
            State.tm.current.move_cursor_hierarchic(-1)

        c.toggle_done()

    @staticmethod
    def toggle_cancelled():
        c = State.tm.current.cursor
        if not Config.get("behaviour.show_cancelled"):
            State.tm.current.move_cursor_hierarchic(-1)

        c.toggle_cancelled()

    @staticmethod
    def toggle_show_done():
        if Config.get("behaviour.show_done"):
            while State.tm.current.cursor.done:
                State.tm.current.move_cursor_hierarchic(-1)
            Config.set("behaviour.show_done", False)
        else:
            Config.set("behaviour.show_done", True)



    @staticmethod
    def toggle_show_cancelled():
        if Config.get("behaviour.show_cancelled"):
            while State.tm.current.cursor.cancelled:
                State.tm.current.move_cursor_hierarchic(-1)
            Config.set("behaviour.show_cancelled", False)
        else:
            Config.set("behaviour.show_cancelled", True)


    @staticmethod
    def quit():
        State.tm.save_all()
        Window.quit()

    @staticmethod
    def save():

        State.tm.save_all()
        State.message = "Saved" 

    @staticmethod
    def schedule_up():
        State.tm.current.move_schedule_up()

    @staticmethod
    def schedule_down():
        State.tm.current.move_schedule_down()

    @staticmethod
    def schedule_goto_today():
        State.tm.current.move_schedule_today()

    @staticmethod
    def schedule_top():
        State.tm.current.move_schedule_top()

    @staticmethod
    def hide_categories():
        cats = Window.get_input("Hide").split()
        State.tm.current.hide_categories(cats)
    
    @staticmethod
    def unhide_categories():
        cats = Window.get_input("Unhide").split()
        State.tm.current.unhide_categories(cats)

    @staticmethod
    def show_only_categories():
        cats = Window.get_input("Show only").split()
        State.tm.current.show_only_categories = cats

    @staticmethod
    def unhide_all_categories():
        State.tm.current.unhide_all_categories()

    @staticmethod
    def show_all_categories():
        State.tm.current.unhide_all_categories()
        State.tm.current.show_only_categories = set()

class CommandHandler:
    config_call = {
            'down' : Commands.down,
            'up' : Commands.up,
            'down_flat' : Commands.down_flat,
            'up_flat' : Commands.up_flat,
            'left' : Commands.left,
            'right' : Commands.right,
            'collapse' : Commands.collapse,
            'edit_title' : Commands.edit_title,
            'edit_scheduled' : Commands.edit_scheduled,
            'edit_due' : Commands.edit_due,
            'edit_priority' : Commands.edit_priority,
            'edit_categories' : Commands.edit_categories,
            'toggle_done' : Commands.toggle_done,
            'toggle_show_done' : Commands.toggle_show_done,
            'toggle_cancelled' : Commands.toggle_cancelled,
            'toggle_show_cancelled' : Commands.toggle_show_cancelled,
            'replace_title' : Commands.replace_title,
            'edit_text' : Commands.edit_text,
            'sort_title' : Commands.sort_title,
            'sort_natural' : Commands.sort_natural,
            'sort_priority' : Commands.sort_priority,
            'sort_due' : Commands.sort_due,
            'sort_scheduled' : Commands.sort_scheduled,
            'sort_category' : Commands.sort_category,
            'sort_title_rev' : lambda : Commands.sort_title(True),
            'sort_natural_rev' : lambda : Commands.sort_natural(True),
            'sort_priority_rev' : lambda : Commands.sort_priority(True),
            'sort_due_rev' : lambda : Commands.sort_due(True),
            'sort_scheduled_rev' : lambda : Commands.sort_scheduled(True),
            'sort_category_rev' : lambda : Commands.sort_category(True),
            'new_task_child_bottom' : Commands.new_task_child_bottom,
            'new_task_child_top' : Commands.new_task_child_top,
            'new_task_above' : Commands.new_task_above,
            'new_task_below' : Commands.new_task_below,
            'delete_task' : Commands.delete_task,
            'cut_task' : Commands.cut_task,
            'paste_before' : Commands.paste_before,
            'paste_after' : Commands.paste_after,
            'paste_below_prepend' : Commands.paste_below_prepend,
            'paste_below_append' : Commands.paste_below_append,
            'save' : Commands.save,
            'quit' : Commands.quit,
            'copy_cursor' : Commands.copy_cursor,
            'schedule_down' : Commands.schedule_down,
            'schedule_up' : Commands.schedule_up,
            'schedule_goto_today' : Commands.schedule_goto_today,
            'schedule_top' : Commands.schedule_top,
            'show_only_categories' : Commands.show_only_categories,
            'show_all_categories' : Commands.show_all_categories,
            'hide_categories' : Commands.hide_categories,
            'unhide_categories' : Commands.unhide_categories,
            'unhide_all_categories' : Commands.unhide_all_categories
    }

    def __init__(self):
        self.key_actions = {}
        self.keychain_scope = None

        # load bindings
        for action_config, keys in Config.get_section('keys').items():
            if not action_config in CommandHandler.config_call:
                raise ValueError("Action '{}' not defined".format(action_config))

            key_actions_last = self.key_actions
            for key in keys[:-1]:
                if not key in key_actions_last:
                    key_actions_last[key] = {}
                key_actions_last = key_actions_last[key]

            key_actions_last[keys[-1]] = CommandHandler.config_call[action_config]


    def handle(self, key):
        logging.debug("key handler: {} (utf-8), {} (decoded)".format(str(key.encode("utf-8")), key))
        if self.keychain_scope == None:
            scope = self.key_actions
        else:
            scope = self.keychain_scope

        if key in scope:
            action = scope[key]
        else:
            action = None

        if callable(action):
            action()
            self.keychain_scope = None
        else:
            self.keychain_scope = action

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

        assert cursor in current_list

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

class Window:
    @staticmethod
    def handle_special_key(k):
        special_keys = {
                #'KEY_RESIZE' : Window.calculate_coordinates
        }

        if k in special_keys:
            special_keys[k]()
            return True
        else:
            return False

    @staticmethod
    def main(stdscr):
        #init colors
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        
        curses.curs_set(0)

        Window.scr = stdscr
        Window.command_handler = CommandHandler()
        Window.scroller_tree = Scroller(0, Config.get("behaviour.scrolloffset_tree"))
        Window.scroller_schedule = Scroller(0, Config.get("behaviour.scrolloffset_schedule"))
        Window.draw()
        while True:
            Window.loop()

    @staticmethod
    def loop():
        k = Window.scr.getkey()

        if not Window.handle_special_key(k):
            Window.command_handler.handle(k)

        if Config.get("behaviour.autosave"):
            State.tm.save_all()

        Window.draw()

    @staticmethod
    def quit():
        pass

    @staticmethod
    def get_input(message):
        msgstr = "-> " + message + ": "
        maxh, maxw = Window.scr.getmaxyx()
        maxw -= len(msgstr) + 1
        Window.scr.addstr(maxh - 1, 0, msgstr) 
        return Window.insert(len(msgstr), maxh - 1, maxw)

    @staticmethod
    def calculate_coordinates():
        h, w = Window.scr.getmaxyx()
        c = WindowCoordinates()

        # spacings from the border
        c.tasks.ul.x = 1
        c.tasks.ul.y = 1
        c.sched.br.x = w - 2
        c.sched.ul.y = c.tasks.ul.y
        c.descr.br.y = h - 2
        c.descr.ul.x = c.tasks.ul.x
        
        # find location where the inner-screen borders meet
        if Config.get("appearance.schedule_show"):
            r = Config.get("appearance.schedule_ratio")
            c.cross.x = int(c.sched.br.x - r * (c.sched.br.x - c.tasks.ul.x))
            sched_w = c.sched.br.x - c.cross.x
            if sched_w < Config.get("appearance.schedule_min"):
                if Config.get("appearance.schedule_min") <= w - 4:
                    sched_w = Config.get("appearance.schedule_min")
            elif sched_w > Config.get("appearance.schedule_max"):
                sched_w = Config.get("appearance.schedule_max")
            c.cross.x = c.sched.br.x - sched_w
        else:
            c.cross.x = w - 1

        if Config.get("appearance.description_show"):
            r = Config.get("appearance.description_ratio")
            c.cross.y = int(c.descr.br.y - r * (c.descr.br.y - c.tasks.ul.y))
            descr_h = c.descr.br.y - c.cross.y
            if descr_h < Config.get("appearance.description_min"):
                if Config.get("appearance.description_min") <= h - 5:
                    descr_h = Config.get("appearance.description_min")
            elif descr_h > Config.get("appearance.description_max"):
                descr_h = Config.get("appearance.description_max")
            c.cross.y = c.descr.br.y - descr_h
        else:
            c.cross.y = h - 1

        c.tasks.br.x = c.cross.x - 1
        c.tasks.br.y = c.cross.y - 1
        c.sched.ul.x = c.cross.x + 1
        c.descr.ul.y = c.cross.y + 1
        c.sched.br.y = c.descr.br.y
        c.descr.br.x = c.tasks.br.x

        return c

    @staticmethod
    def draw_tasks(win, coords):
        x = coords.ul.x + 1
        y = coords.ul.y
        h = coords.h

        Window.scroller_tree.viewport_height = h
        dl = Window.scroller_tree.get_display_list(
                State.tm.current.cursor,
                State.tm.current.display_list)

        for i, task in enumerate(dl):
            ListTask(task, RectCoordinates(x, y + i, x + coords.w, y + i), win)

    @staticmethod
    def draw_description(win, coords):
        if not State.tm.current.cursor is None:
            Window.description_task = DescriptionTask(State.tm.current.cursor, coords, win)

    @staticmethod
    def draw_schedule(win, coords):
        x = coords.ul.x
        y = coords.ul.y
        w = coords.w
        h = coords.h
        title_str = "Schedule"
        spacing_len = int((w - len(title_str)) / 2)
        spacing = " " * (0 if spacing_len < 0 else spacing_len)
        win.addnstr(y, x, spacing + "Schedule", w, curses.A_BOLD)

        y += 2

        max_tasks = int((h - 2) / 3)

        Window.scroller_schedule.viewport_height = max_tasks
        dl = Window.scroller_schedule.get_display_list(
                State.tm.current.cursor_sched,
                State.tm.current.schedule_list)

        for i, task in enumerate(dl):
            ScheduleTask(task, RectCoordinates(x, y + i * 3, x + coords.w, y + i * 3 + 3), win)

    @staticmethod
    def draw_filterstr(win, coords):
        so_cat = State.tm.current.show_only_categories
        hi_cat = State.tm.current.hidden_categories
        if not so_cat is None and len(so_cat) != 0:
            filter_str = " Showing only: " + " ".join(so_cat) + " "
        elif not len(hi_cat) == 0:
            filter_str = " Hiding: " + " ".join(hi_cat) + " "
        else:
            filter_str = ""

        l = len(filter_str)

        win.addstr(coords.tasks.br.y + 1, coords.tasks.br.x - l, filter_str, curses.A_DIM)

    @staticmethod
    def draw():
        Window.scr.erase()
        Window.scr.border()
        Window.scr.addstr(0, 1, "TreeTasks - welcome!")
        y, x = Window.scr.getmaxyx()

        wincoords = Window.calculate_coordinates()

        Window.scr.addstr(y - 1, 0, "-> " + State.message + " ")
        Window.draw_tasks(Window.scr, wincoords.tasks)

        if Config.get("appearance.schedule_show"):
            Window.draw_schedule(Window.scr, wincoords.sched)
            Window.scr.vline(1, wincoords.cross.x, 
                    curses.ACS_VLINE, y - 2)

        if Config.get("appearance.description_show"):
            Window.draw_description(Window.scr, wincoords.descr)
            Window.scr.hline(wincoords.cross.y, wincoords.tasks.ul.x,
                    curses.ACS_HLINE, wincoords.cross.x - 1)

        Window.draw_filterstr(Window.scr, wincoords)

        Window.scr.refresh()

    @staticmethod
    def insert(x, y, maxc, maxl=1, s="", replace=False):
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
                Window.scr.addstr(y + line_no, x, "".ljust(maxc))
            for line_no, line in enumerate(lines):
                Window.scr.addstr(y + line_no, x, line, curses.A_UNDERLINE)

            old_len = max([len(i) for i in lines])

            # move cursor
            Window.scr.move(y + cursor_line, x + cursor_pos)

            # wait for char
            k = Window.scr.get_wch()
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
                        logging.debug("i break a".format(s, len(s)))
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
            elif k == curses.KEY_BACKSPACE:
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

            elif k == b"\x7f".decode("utf-8"): #shift-backspace
                logging.debug("i break d".format(s, len(s)))
                return None
            elif k == b"\x1b".decode("utf-8"): #escape
                break
            elif type(k) == str:
                if not len(lines[cursor_line]) == maxc:
                    lines[cursor_line] = lines[cursor_line][:cursor_pos] + k + lines[cursor_line][cursor_pos:]
                    cursor_pos += 1

        curses.curs_set(0)
        return '\n'.join(lines)



    


