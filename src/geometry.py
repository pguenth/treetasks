from dataclasses import dataclass
from .config import Config

@dataclass
class Point:
    x : int = 0
    y : int = 0

class RectCoordinates:
    ul : Point
    br : Point

    def __init__(self, ulx=0, uly=0, brx=0, bry=0):
        self.ul = Point(ulx, uly)
        self.br = Point(brx, bry)

    @property
    def w(self):
        return self.br.x - self.ul.x + 1

    @property
    def h(self):
        return self.br.y - self.ul.y + 1

@dataclass
class TaskWindowColumn:
    x : int = 0
    w : int = 0

class TaskWindowColumns:
    def __init__(self, taskwindow_width=0):
        self.taskwindow_width = taskwindow_width

    @property
    def taskwindow_width(self):
        return self._taskwindow_width

    @taskwindow_width.setter
    def taskwindow_width(self, value):
        self._taskwindow_width = value
        self._recalculate()

    @property
    def category(self):
        return self._category

    @property
    def scheduled(self):
        return self._scheduled

    @property
    def due(self):
        return self._due

    def _recalculate(self):
        self._category = TaskWindowColumn()
        self._scheduled = TaskWindowColumn()
        self._due = TaskWindowColumn()

        self._category.w = self._get_column_width("category")
        self._scheduled.w = self._get_column_width("scheduled")
        self._due.w = self._get_column_width("due")
        self._limit_col_widths()

        column_order = Config.get("appearance.columns")
        x_start = self.taskwindow_width - self.real_sum
        for cname in column_order:
            this_col = self.column_by_letter(cname)
            this_col.x = x_start
            x_start += this_col.w + 1

    # limits the calculated column widths so they
    # fill at maximum appearance.columns_max_total_ratio * task_w
    # use only columns that will be displayed
    def _limit_col_widths(self):
        wsum = self.real_sum

        if wsum > Config.get("appearance.columns_max_total_ratio") * self.taskwindow_width:
            f = Config.get("appearance.columns_max_total_ratio") * self.taskwindow_width / wsum 
            self._category.w = int(self._category.w * f)
            self._scheduled.w = int(self._scheduled.w * f)
            self._due.w = int(self._due.w * f)


    def _get_column_width(self, col_name):
        r = Config.get("appearance.col_" + col_name + "_ratio")
        mn = Config.get("appearance.col_" + col_name + "_min")
        mx = Config.get("appearance.col_" + col_name + "_max")

        w = int(self.taskwindow_width * r)
        if w < mn:
            w = mn
        if w > mx:
            w = mx

        return w

    # get column out of columns (type TaskWindowColumns)
    # from their first letter
    def column_by_letter(self, letter):
        if letter == 'c':
            return self.category
        elif letter == 'd':
            return self.due
        elif letter == 's':
            return self.scheduled

    @property
    def real_sum(self):
        cconf = Config.get("appearance.columns")
        wsum = 0
        for coln in cconf:
            wsum += self.column_by_letter(coln).w
            wsum += 1 # spacing

        return wsum - 1

class ScheduleCoordinates:
    def __init__(self, schedule_width):
        self.datespacing = 2
        self.schedule_width = schedule_width

    @property
    def schedule_width(self):
        return self._schedule_width

    @schedule_width.setter
    def schedule_width(self, value):
        self._schedule_width = value
        self._recalculate()

    def _recalculate(self):
        self.datewidth = int((self.schedule_width - 2 - self.datespacing) / 2)
        self.scheduled_offset = 1
        self.due_offset = self.datewidth + self.datespacing + 1

class WindowCoordinates:
    tasks : RectCoordinates
    sched : RectCoordinates
    descr : RectCoordinates
    cross: Point
    columns : TaskWindowColumns

    def __init__(self):
        self.tasks = RectCoordinates()
        self.sched = RectCoordinates()
        self.descr = RectCoordinates()
        self.cross = Point()
        self.columns = TaskWindowColumns()
