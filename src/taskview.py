import curses
from math import ceil
import logging
import re
from datetime import date, timedelta, datetime
from anytree import AnyNode

from .task import TaskState
from .geometry import TaskWindowColumns, ScheduleCoordinates
from .config import Config
from .referenced import CallOnSet, ReferencedDescriptor



class EditableString:
    attr = CallOnSet("_redraw")
    x = CallOnSet("_redraw")
    y = CallOnSet("_redraw")
    maxcols = CallOnSet("_redraw")
    maxlines = CallOnSet("_redraw")
    app = CallOnSet("_redraw")
    def __init__(self, descriptor, maxcols=100, maxlines=1):
        self.descriptor = descriptor

        # noredraw until place()
        self._noredraw = True
        self.attr = curses.A_NORMAL
        self.maxcols = maxcols
        self.maxlines = maxlines

    @property
    def s(self):
        s = self.descriptor.get()
        if s is None:
            return ""
        else:
            return self.descriptor.get()

    @s.setter
    def s(self, value):
        self.descriptor.set(value)

    def __len__(self):
        return len(self.s)

    def place(self, x, y, treetasks_app, maxcols=-1, maxlines=1):
        self._noredraw = True
        self.app = treetasks_app
        self.x = x
        self.y = y
        self.maxcols = maxcols
        self.maxlines = maxlines

        self._noredraw = False
        self._redraw()

    def _redraw(self):
        # prevent multiple redrawings while __init__
        if self._noredraw:
            return

        for line_no, line in zip(range(0, self.maxlines), self.s.splitlines()):
            if self.maxcols < 0: 
                self.app.scr.addstr(self.y + line_no, self.x, line, self.attr)
            elif self.maxcols >= 0:
                self.app.scr.addnstr(self.y + line_no, self.x, line, self.maxcols, self.attr)

    # window is not the ncurses window, but the Window class
    def edit(self, replace=False):
        """
        open the string for interactive edit at the place where it is currently drawn.
        if replace is True, first remove the current contents from screen before entering
        the edit session.
        """

        self.attr = curses.A_NORMAL

        if replace:
            new_s = self.app.insert(self.x, self.y, self.maxcols, self.maxlines)
        else:
            new_s = self.app.insert(self.x, self.y, self.maxcols, self.maxlines, s=self.s)

        if not new_s is None:
            self.s = new_s

class EditableDate(EditableString):
    @property
    def s(self):
        date = self.descriptor.get()
        if date is None:
            return ""

        if date == date.today():
            dstr = "today"
        elif date == date.today() + timedelta(days=1):
            if self.maxcols < 8:
                dstr = "tmrrw"
            else:
                dstr = "tomorrow"
        elif (date - date.today()).days <= 7 and (date - date.today()).days > 0:
            dstr = date.strftime("%A")
            if len(dstr) > self.maxcols:
                dstr = date.strftime("%a")
        else:
            if self.maxcols < 8:
                dstr = date.strftime("%m-%d")
            elif self.maxcols < 10:
                dstr = date.strftime("%y-%m-%d")
            else:
                dstr = date.strftime("%Y-%m-%d")

        return dstr

    @s.setter
    def s(self, value):
        parsers = [
            EditableDate.parse_date_name,
            EditableDate.parse_date_weekday,
            EditableDate.parse_date_interval,
            EditableDate.parse_date_absolute
        ]

        for p in parsers:
            d = p(value)
            if not d is None:
                break

        if d is None:
            self.app.message = "Unable to parse date"
        else:
            self.descriptor.set(d)


    @staticmethod
    def parse_date_name(s):
        s = s.lower()
        if s == "tommorrow" or s == "tmmrw":
            return date.today() + timedelta(days=1)
        elif s == "today" or s == "tdy":
            return date.today()
        else:
            return None

    @staticmethod
    def parse_date_weekday(s):
        if "monday".startswith(s):
            wd = 0
        elif "tuesday".startswith(s):
            wd = 1
        elif "wednesday".startswith(s):
            wd = 2
        elif "thursday".startswith(s):
            wd = 3
        elif "friday".startswith(s):
            wd = 4
        elif "saturday".startswith(s):
            wd = 5 
        elif "sunday".startswith(s):
            wd = 6
        else:
            return None

        td = date.today().weekday()
        delta = wd - td
        delta = delta if delta > 0 else delta + 7
        return date.today() + timedelta(days=delta)

    @staticmethod
    def parse_date_interval(s):
        match = re.findall(r"([\-\+])(\d+)([DWMdwm])", s)
        if len(match) == 0:
            return None
       
        delta = timedelta(days=0)
        for op, n, unit in match:
            unit = unit.lower()
            n = int(n)
            if unit == 'd':
                this_d = timedelta(days=n)
            elif unit == 'w':
                this_d = timedelta(weeks=n)
            elif unit == 'm':
                this_d = timedelta(days=30*n)

            if op == '-':
                delta -= this_d 
            else:
                delta += this_d

        return date.today() + delta

    @staticmethod
    def parse_date_absolute(s):
        formats = [
                ('%Y-%m-%d', ''),
                ('%y-%m-%d', ''),
                ('%d.%m.%Y', ''),
                ('%d.%m.%y', ''),
                ('%m/%d/%y', ''),
                ('%m/%d/%Y', ''),
                ('%m-%d', 'y'),
                ('%d.%m', 'y'),
                ('%d.%m.', 'y'),
                ('%m/%d', 'y'),
                ('%d', 'ym'),
                ('%d.', 'ym')
            ]

        for fmt, defs in formats:
            try:
                d = datetime.strptime(s, fmt).date()
            except ValueError:
                continue

            if defs == 'y':
                d = d.replace(year=date.today().year)
                if d <= date.today():
                    d = d.replace(year=d.year + 1)
            if defs == 'ym':
                d = d.replace(year=date.today().year)
                d = d.replace(month=date.today().month)
                if d <= date.today():
                    if d.month == 12:
                        n_month = 1
                        n_dyear = 1
                    else:
                        n_month = d.month + 1
                        n_dyear = 0

                    d = d.replace(month=n_month, year=d.year + n_dyear)

            logging.debug("using {}, {}: s {}, d {}".format(fmt, defs, s, d))
            return d

        return None

class EditableList(EditableString):
    @property
    def s(self):
        l = self.descriptor.get()
        return " ".join(l)

    @s.setter
    def s(self, value):
        self.descriptor.set(value.split())

class EditableInt(EditableString):
    def __init__(self, descriptor, valid_range=None, invalid_handler=None):
        super().__init__(descriptor)
        self.valid_range = valid_range
        self.invalid_handler = invalid_handler

    def _validate(self, value):
        if self.valid_range is None:
            return True

        if not value in self.valid_range:
            if not self.invalid_handler is None:
                self.invalid_handler()
            return False
        else:
            return True


    @property
    def s(self):
        i = self.descriptor.get()
        if i is None:
            return ""
        else:
            return str(i)

    @s.setter
    def s(self, value):
        try:
            v = int(value)
        except ValueError:
            self.app.message = "Unable to parse int"
            return

        if self._validate(v):
            self.descriptor.set(v)
        
class TaskView:
    x = CallOnSet("_redraw")
    y = CallOnSet("_redraw")
    width = CallOnSet("_redraw")
    height = CallOnSet("_redraw")
    app = CallOnSet("_redraw")

    def __init__(self, task, geometry, treetasks_app):
        self._noredraw = True

        self.task = task
        self.x = geometry.ul.x
        self.y = geometry.ul.y
        self.width = geometry.w
        self.height = geometry.h
        self.app = treetasks_app

class ListTask(TaskView):
    def __init__(self, task, geometry, treetasks_app):
        super().__init__(task, geometry, treetasks_app)

        self.cols = TaskWindowColumns(self.width)

        self.categories = None
        self.scheduled = None
        self.due = None

        self.title = EditableString(ReferencedDescriptor(type(task).title, task))
        self.priority = EditableInt(ReferencedDescriptor(type(task).priority, task))

        self._noredraw = False
        self._redraw()

        self.task.listview = self

    def _readd_columns(self):
        if 'c' in Config.get("appearance.columns") and self.categories is None:
            self.categories = EditableList(
                    ReferencedDescriptor(
                        type(self.task).categories, self.task
                        )
                    )
        elif not 'c' in Config.get("appearance.columns"):
            self.categories = None

        if 'd' in Config.get("appearance.columns") and self.due is None:
            self.due = EditableDate(
                    ReferencedDescriptor(
                        type(self.task).due, self.task
                        )
                    )
        elif not 'd' in Config.get("appearance.columns"):
            self.due = None

        if 's' in Config.get("appearance.columns") and self.scheduled is None:
            self.scheduled = EditableDate(
                    ReferencedDescriptor(
                        type(self.task).scheduled, self.task
                        )
                    )
        elif not 's' in Config.get("appearance.columns"):
            self.scheduled = None

    def _get_state_attr(self):
        if self.task.state == TaskState.PENDING:
            attr = curses.A_NORMAL
        elif self.task.state == TaskState.DONE:
            attr = curses.A_DIM
        elif self.task.state == TaskState.CANCELLED:
            attr = curses.A_DIM

        return attr

    def _replace_columns(self):
        attr = self._get_state_attr()

        if not self.categories is None:
            self.categories.place(
                self.x + self.cols.category.x,
                self.y,
                self.app,
                self.cols.category.w
            )
            self.categories.attr = attr

        if not self.due is None:
            self.due.place(
                self.x + self.cols.due.x,
                self.y,
                self.app,
                self.cols.due.w
            )
            self.due.attr = attr

        if not self.scheduled is None:
            self.scheduled.place(
                self.x + self.cols.scheduled.x,
                self.y,
                self.app,
                self.cols.scheduled.w
            )
            self.scheduled.attr = attr

    def _redraw(self):
        if self._noredraw:
            return

        self.cols.taskwindow_width = self.width

        x = self.x
        if not Config.get("behaviour.flat_tree"):
            for i in range(len(self.task.ancestors) - 1):
                self.app.scr.addstr(self.y, x + 2, Config.get("appearance.indent_guide").ljust(1))
                x += Config.get("appearance.indent")

                # 1: width offset, 2: spacing, 6: prefix, 1: spacing to cols
        title_maxwidth = self.width - self.cols.real_sum - 1 - 6 - x + self.x
        attr = self._get_state_attr()
        attr_title = attr

        if Config.get("behaviour.flat_tree"):
            pathstr_maxlength = title_maxwidth - len(self.task.title)
            if pathstr_maxlength < 1:
                pathstr = ""
            else:
                pathstr = get_limited_path_overall(self.task, pathstr_maxlength)

            pathstr_offset = len(pathstr)
            self.app.scr.addstr(self.y, x + 5, pathstr)
            if attr_title == curses.A_NORMAL:
                attr_title = curses.A_BOLD
        else:
            pathstr_offset = 0


        self.priority.place(
                x + 2,
                self.y, 
                self.app,
                1
            )
        self.priority.attr = attr
        
        if self.task.state == TaskState.DONE:
            self.app.scr.addstr(self.y, x + 2, "d", attr)
        elif self.task.state == TaskState.CANCELLED:
            self.app.scr.addstr(self.y, x + 2, "c", attr)

        progress_symbols = " ▁▂▃▄▅▆▇█"
        nsymbol = int((len(progress_symbols) - 1) * self.task.progress + 0.5)
        self.app.scr.addstr(self.y, x + 3, progress_symbols[nsymbol], attr)


        if Config.get("plugins.timewarrior"):
            import ext.timewarrior as timewarrior
            
            if timewarrior.is_tracking_task(self.task, Config.get("plugins.timewarrior_parents_as_tags"), True):
                self.app.scr.addstr(self.y, x + 2, "R", curses.color_pair(2))

        self.app.scr.addstr(self.y, x + 1, "[", attr)
        self.app.scr.addstr(self.y, x + 4, "] ", attr)
        
        if len(self.task.children) != 0:
            if self.task.collapsed:
                self.app.scr.addstr(self.y, x, "+")
            else:
                self.app.scr.addstr(self.y, x, "-")

        self.title.place(
                x + 6 + pathstr_offset,
                self.y,
                self.app,
                title_maxwidth - pathstr_offset
            )

        self.title.attr = attr_title

        if self.app.tm.current.cursor == self.task:
            self.title.attr = curses.A_STANDOUT

        self._readd_columns()
        self._replace_columns()

def strf_timedelta(td):
    s = td.seconds
    d = td.days
    h = int(s / 3600)
    s -= h * 3600
    m = int(s / 60)
    s -= m * 60
    string = "{}d{:02d}h{:02d}m{:02d}s".format(d, h, m, s)
    return string

def get_limited_path(task, limit):
    dotstr = "…"
    path = [t.title for t in task.path if not isinstance(t, AnyNode) and not t == task]
    path_limited = [p[:limit - len(dotstr)] + dotstr if len(p) > limit else p for p in path]
    path_str = "/".join(path_limited) + "/" if len(path_limited) else ""
    return path_str



def get_limited_path_overall_old(task, overall_limit):
    dotstr = "…"
    path = [t.title for t in task.path if not isinstance(t, AnyNode) and not t == task]
    unlimited_length = len("/".join(path))
    if len(path) != 0:
        cut = max(0, ceil((unlimited_length - overall_limit) / len(path)))
        path_limited = [p[:-cut - len(dotstr)] + dotstr if cut > 0 else p for p in path]
        path_str = "/".join(path_limited) + "/" if len(path_limited) else ""
        return path_str
    else:
        return ""

def get_limited_path_overall(task, lim):
    path_parts = [t.title for t in task.path if not isinstance(t, AnyNode) and not t == task]
    count = len(path_parts)
    max_len = sum([len(p) for p in path_parts]) + count - 1
    slash_count = count
    if lim <= count + slash_count:
        rstr = ""
        for i, part in enumerate(reversed(path_parts)):
            if i == 0:
                if lim - len(rstr) < 1:
                    break
                rstr = part[0] + rstr
            else:
                if lim - len(rstr) < 2:
                    break
                rstr = part[0] + "/" + rstr

        return rstr 
    elif lim < max_len:
        part_lengths = [1] * count
        filling_index = count - 1
        while sum(part_lengths) < lim - slash_count:
            if part_lengths[filling_index] == len(path_parts[filling_index]):
                if filling_index == count - 1 and filling_index != 0:
                    filling_index = 0
                elif filling_index == 0 and count > 2:
                    filling_index = count - 2
                else:
                    filling_index -= 1
                if filling_index < 0:
                    break
            part_lengths[filling_index] += 1

        path_parts = [p[:l] for p, l in zip(path_parts, part_lengths)]

    return "/".join(path_parts) + "/" if not count == 0 else ""

class DescriptionTask(TaskView):
    def __init__(self, task, geometry, treetasks_app):
        super().__init__(task, geometry, treetasks_app)

        self.scheduled = EditableDate(ReferencedDescriptor(type(task).scheduled, task))
        self.due = EditableDate(ReferencedDescriptor(type(task).due, task))
        self.categories = EditableList(ReferencedDescriptor(type(task).categories, task))
        self.text = EditableString(ReferencedDescriptor(type(task).text, task), maxlines=self.height)
        self.title = EditableString(ReferencedDescriptor(type(task).title, task))
        self.priority = EditableInt(ReferencedDescriptor(type(task).priority, task))

        self._noredraw = False
        self._redraw()

        self.task.descriptionview = self

    def _redraw(self):
        if self._noredraw:
            return

        x = self.x
        y = self.y
        cat_len = len(self.categories)

        path_maxlen = Config.get("appearance.description_path_maxlength")
        if Config.get("appearance.description_show_path"):
            path_str = get_limited_path(self.task, path_maxlen)
            self.app.scr.addstr(y, x + 3, path_str)
        else:
            path_str = ""

        title_width = max(int(0.5 * self.width), self.width - cat_len)
        self.title.place(x + 3 + len(path_str), y, self.app, title_width - 3)
        self.title.attr = curses.A_BOLD
        self.priority.place(x + 1, y, self.app, 1)
        self.categories.place(x + self.width - cat_len - 1, y, self.app)
        self.text.place(x + 1, y + 2, self.app, self.width - 2, maxlines=self.height - 2)

        if Config.get("plugins.timewarrior") and Config.get("plugins.timewarrior_show_time"):
            import ext.timewarrior as timewarrior
            duration = timewarrior.get_duration(self.task, Config.get("plugins.timewarrior_parents_as_tags"), True)
            duration_str = strf_timedelta(duration)
            self.app.scr.addstr(y, x + self.width - cat_len - 2 - len(duration_str), duration_str)

        t_scheduled = "Scheduled"
        t_due = "Due"
        x_dates = x + 1
        if self.scheduled.s != "":
            self.app.scr.addstr(y + 5, x_dates, t_scheduled, curses.A_BOLD)
            x_dates += len(t_scheduled) + 1
            self.scheduled.place(x_dates, y + 5, self.app)
            x_dates += len(self.scheduled)
            if self.due.s != "":
                self.app.scr.addstr(y + 5, x_dates, ", ", curses.A_BOLD)
                x_dates += 2
        if self.due.s != "":
            self.app.scr.addstr(y + 5, x_dates, t_due + " ", curses.A_BOLD)
            x_dates += len(t_due) + 1
            self.due.place(x_dates, y + 5, self.app)

class ScheduleTask(TaskView):
    def __init__(self, task, geometry, treetasks_app):
        super().__init__(task, geometry, treetasks_app)

        self.scheduled = EditableDate(ReferencedDescriptor(type(task).scheduled, task))
        self.due = EditableDate(ReferencedDescriptor(type(task).due, task))
        self.title = EditableString(ReferencedDescriptor(type(task).title, task))
        self.priority = EditableInt(ReferencedDescriptor(type(task).priority, task))

        self.scheduled.attr = curses.A_DIM
        self.due.attr = curses.A_DIM


        self._noredraw = False
        self._redraw()

        self.task.scheduleview = self

    def _redraw(self):
        if self._noredraw:
            return

        x = self.x
        y = self.y

        if self.task.sort_date == date.today():
            attr = curses.color_pair(2)
        elif self.task.sort_date < date.today():
            attr = curses.color_pair(1)
        else:
            attr = curses.color_pair(0)

        if self.task == self.app.tm.schedule.cursor:
            attr |= curses.A_REVERSE

        sched_coords = ScheduleCoordinates(self.width)
        self.scheduled.place(x + sched_coords.scheduled_offset,
                y, self.app, sched_coords.datewidth)
        self.due.place(x + sched_coords.due_offset,
                y, self.app, sched_coords.datewidth)

        pathlen = self.width - 2 - len(self.title.s)
        if Config.get("appearance.description_show_path"):
            pathstr = get_limited_path_overall(self.task, pathlen)
            self.app.scr.addstr(y + 1, x + 1, pathstr)
        else:
            pathstr = ""
        self.title.place(x + 1 + len(pathstr), y + 1, self.app, self.width - 2)

        self.title.attr = attr

        if not self.task in self.app.tm.current.schedule_list:
            self.app.scr.addstr(y + 1, x + self.width - 3, ' +', curses.A_DIM)
