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
    category : TaskWindowColumn
    scheduled : TaskWindowColumn
    due : TaskWindowColumn

    def __init__(self, cx=0, cw=0, sx=0, sw=0, dx=0, dw=0):
        self.category = TaskWindowColumn(cx, cw)
        self.scheduled = TaskWindowColumn(sx, sw)
        self.due = TaskWindowColumn(dx, dw)

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
