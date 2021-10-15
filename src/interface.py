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
from .taskview import ListTask, DescriptionTask

locale.setlocale(locale.LC_ALL, '')
lcode = locale.getpreferredencoding()

os.environ.setdefault('ESCDELAY', '25')

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Commands:
    @staticmethod
    def edit_scheduled():
        Window.current_tasks[State.tm.current.cursor_line].scheduled.edit(Window)
        
    @staticmethod
    def edit_priority():
        Window.current_tasks[State.tm.current.cursor_line].priority.edit(Window, replace=True)

    @staticmethod
    def edit_due():
        Window.current_tasks[State.tm.current.cursor_line].due.edit(Window)

    @staticmethod
    def edit_categories():
        Window.current_tasks[State.tm.current.cursor_line].categories.edit(Window)

    @staticmethod
    def edit_title():
        Window.current_tasks[State.tm.current.cursor_line].title.edit(Window)

    @staticmethod
    def replace_title():
        Window.current_tasks[State.tm.current.cursor_line].title.edit(Window)

    @staticmethod
    def edit_text():
        Window.description_task.text.edit(Window)

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
        Window.move_cursor(1)

    @staticmethod
    def up():
        Window.move_cursor(-1)

    @staticmethod
    def down_flat():
        Window.move_cursor_flat(1)

    @staticmethod
    def up_flat():
        Window.move_cursor_flat(-1)

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
    def new_task_child_bottom():
        new_task = State.tm.current.new_task_child_bottom()
        Window.draw()
        Commands.edit_title()
        if new_task.title == "":
            State.tm.current.delete(new_task)

    @staticmethod
    def new_task_child_top():
        new_task = State.tm.current.new_task_child_bottom()
        Window.draw()
        Commands.edit_title()
        if new_task.title == "":
            State.tm.current.delete(new_task)

    @staticmethod
    def left():
        try:
            Window.cursor_left()
        except TreeError:
            pass

    @staticmethod
    def right():
        try:
            Window.cursor_right()
        except TreeError:
            logging.debug("new task")

    @staticmethod
    def collapse():
        State.tm.current.cursor.toggle_collapse()

    @staticmethod
    def toggle_done():
        c = State.tm.current.cursor
        if not Config.get("behaviour.show_done"):
            Window.move_cursor(-1)

        c.toggle_done()

    @staticmethod
    def toggle_cancelled():
        c = State.tm.current.cursor
        if not Config.get("behaviour.show_cancelled"):
            Window.move_cursor(-1)

        c.toggle_cancelled()

    @staticmethod
    def toggle_show_done():
        if Config.get("behaviour.show_done"):
            while State.tm.current.cursor.done:
                Window.move_cursor(-1)
            Config.set("behaviour.show_done", False)
        else:
            Config.set("behaviour.show_done", True)



    @staticmethod
    def toggle_show_cancelled():
        if Config.get("behaviour.show_cancelled"):
            while State.tm.current.cursor.cancelled:
                Window.move_cursor(-1)
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
            'delete_task' : Commands.delete_task,
            'cut_task' : Commands.cut_task,
            'paste_before' : Commands.paste_before,
            'paste_after' : Commands.paste_after,
            'paste_below_prepend' : Commands.paste_below_prepend,
            'paste_below_append' : Commands.paste_below_append,
            'save' : Commands.save,
            'copy_cursor' : Commands.copy_cursor
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
            logging.debug("running: " + str(action))
            action()
            self.keychain_scope = None
        else:
            self.keychain_scope = action

#class Scroller:
#    def __init__(self, viewport_height):
#        self.viewport_height = viewport_height
#        self.display_list = None
#        self.cursor = None
#
#    def get_list(self, cursor, display_list):
#        assert cursor in display_list
#
#        index_new = display_list.index(cursor)
#        index_old = 
#
#        h = self.viewport_height - 1
#        new_cline = State.tm.current.cursor_line + index_new - index_old
#        new_cline = max(scrolloff, min(new_cline, h - scrolloff))
#        if new_cline >= index_new:
#            return index_new
#        elif h - new_cline >= len(State.tm.current.display_list) - index_new and h < len(State.tm.current.display_list):
#            delta = h - new_cline - len(State.tm.current.display_list) + index_new
#            return new_cline + delta + 1
#        else:
#            return new_cline






class Window:
    @staticmethod
    def handle_special_key(k):
        special_keys = {
                'KEY_RESIZE' : Window.calculate_coordinates
        }

        if k in special_keys:
            special_keys[k]()
            return True
        else:
            return False

    @staticmethod
    def main(stdscr):
        Window.coords = WindowCoordinates()
        Window.scr = stdscr
        Window.command_handler = CommandHandler()
        Window.calculate_coordinates()
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
    def update_cursor(index_new, index_old, cursor_line_old, window_h, scrolloff):
        h = window_h - 1
        new_cline = State.tm.current.cursor_line + index_new - index_old
        new_cline = max(scrolloff, min(new_cline, h - scrolloff))
        if new_cline >= index_new:
            return index_new
        elif h - new_cline >= len(State.tm.current.display_list) - index_new and h < len(State.tm.current.display_list):
            delta = h - new_cline - len(State.tm.current.display_list) + index_new
            return new_cline + delta + 1
        else:
            return new_cline

    @staticmethod
    def cursor_action(action):
        index_old, index_new = action() 
        State.tm.current.cursor_line = Window.update_cursor(
                index_new,
                index_old,
                State.tm.current.cursor_line,
                Window.coords.tasks.h,
                Config.get("behaviour.scrolloffset")
            )

    @staticmethod
    def move_cursor(delta):
        Window.cursor_action(lambda : State.tm.current.move_cursor_hierarchic(delta))

    @staticmethod
    def move_cursor_flat(delta):
        Window.cursor_action(lambda : State.tm.current.move_cursor_flat(delta))

    @staticmethod
    def cursor_left():
        Window.cursor_action(lambda : State.tm.current.move_treeup())

    @staticmethod
    def cursor_right():
        Window.cursor_action(lambda : State.tm.current.move_treedown())

    @staticmethod
    def calculate_coordinates():
        h, w = Window.scr.getmaxyx()
        c = Window.coords

        # spacings from the border
        c.tasks.ul.x = 1
        c.tasks.ul.y = 1
        c.sched.br.x = w - 2
        c.sched.ul.y = c.tasks.ul.y
        c.descr.br.y = h - 2
        c.descr.br.x = c.sched.br.x
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
        c.sched.br.y = c.tasks.br.y
        c.descr.ul.y = c.cross.y + 1

        # task window columns
        task_w = c.cross.x - c.tasks.ul.x

    @staticmethod
    def draw_tasks(win):
        x = Window.coords.tasks.ul.x + 1
        y = Window.coords.tasks.ul.y
        h = Window.coords.tasks.h

        iterlist = State.tm.current.display_list
        index_cursor = iterlist.index(State.tm.current.cursor)
        start = index_cursor - State.tm.current.cursor_line

        if start < 0:
            y -= start
            h += start
            start = 0

        Window.current_tasks = []
        for i, task in enumerate(iterlist[start:]):
            if i > h - 1:
                break

            lt = ListTask(task, RectCoordinates(x, y + i, x + Window.coords.tasks.w, y + i), win)
            Window.current_tasks.append(lt)

    @staticmethod
    def draw_description(win):
        Window.description_task = DescriptionTask(State.tm.current.cursor, Window.coords.descr, win)

    @staticmethod
    def draw_schedule(win):
        x = Window.coords.sched.ul.x
        y = Window.coords.sched.ul.y
        w = Window.coords.sched.w
        title_str = "Schedule"
        spacing_len = int((w - len(title_str)) / 2)
        spacing = " " * (0 if spacing_len < 0 else spacing_len)
        win.addnstr(y, x, spacing + "Schedule", w, curses.A_BOLD)

    @staticmethod
    def draw():
        Window.scr.erase()
        Window.scr.border()
        Window.scr.addstr(0, 1, "TreeTasks - welcome!")
        y, x = Window.scr.getmaxyx()

        Window.scr.addstr(y - 1, 0, "-> " + State.message)
        Window.draw_tasks(Window.scr)
        Window.draw_schedule(Window.scr)

        if Config.get("appearance.schedule_show"):
            Window.draw_schedule(Window.scr)
            Window.scr.vline(1, Window.coords.cross.x, 
                    curses.ACS_VLINE, Window.coords.cross.y - 1)

        if Config.get("appearance.description_show"):
            Window.draw_description(Window.scr)
            Window.scr.hline(Window.coords.cross.y, Window.coords.tasks.ul.x,
                    curses.ACS_HLINE, x - 2)

        Window.scr.refresh()

    @staticmethod
    def draw_schedule(scr):
        
        pass

    @staticmethod
    def insert(x, y, maxc, maxl=1, s="", replace=False):
        # state-machine style bodgy editing/inserting of text
        # initialise editing
        lines = s.splitlines()
        if len(lines) == 0:
            lines.append("")

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

        return '\n'.join(lines)



    


