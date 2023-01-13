from datetime import date, timedelta
from anytree import TreeError, PreOrderIter
from functools import wraps
import copy
import os

from .tree import TaskTreeSortKey
from .config import Config

def task_modification(func):
    def run_recursive(func_bound, it):
        try:
            new = next(it)
            old = copy.deepcopy(new)
            run_recursive(func_bound, it)
        except StopIteration:
            func_bound()
        else:
            Config.modify_hook(old, new)
        
    @wraps(func)
    def f(self, *args, **kwargs):
        it = PreOrderIter(self.app.tm.current.cursor)
        run_recursive(lambda : func(self, *args, **kwargs), it)

    return f

class Commands:
    def __init__(self, treetasks_application):
        self.app = treetasks_application

    @task_modification
    def delete_scheduled(self):
        self.app.tm.current.cursor.scheduled = None
        
    @task_modification
    def delete_priority(self):
        self.app.tm.current.cursor.priority = None

    @task_modification
    def delete_due(self):
        self.app.tm.current.cursor.due = None

    @task_modification
    def delete_categories(self):
        self.app.tm.current.cursor.categories = None

    @task_modification
    def delete_text(self):
        self.app.tm.current.cursor.text = ""

    @task_modification
    def edit_scheduled(self, replace=False):
        self.app.tm.current.cursor.listview.scheduled.edit(replace=replace)
        
    @task_modification
    def edit_priority(self, replace=False):
        self.app.tm.current.cursor.listview.priority.edit(replace=replace)

    @task_modification
    def edit_due(self, replace=False):
        self.app.tm.current.cursor.listview.due.edit(replace=replace)

    @task_modification
    def edit_categories(self, replace=False):
        self.app.tm.current.cursor.listview.categories.edit(replace=replace)

    @task_modification
    def edit_title(self, replace=False):
        self.app.tm.current.cursor.listview.title.edit(replace=replace)

    @task_modification
    def edit_text(self, replace=False):
        self.app.tm.current.cursor.descriptionview.text.edit(replace=replace)

    def sort_title(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.TITLE, reverse)

    def sort_category(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.CATEGORY, reverse)

    def sort_due(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.DUE, reverse)

    def sort_scheduled(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.SCHEDULED, reverse)

    def sort_natural(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.NATURAL, reverse)

    def sort_priority(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.PRIORITY, reverse)

    def sort_date(self, reverse=False):
        self.app.tm.current.set_order(TaskTreeSortKey.DATE, reverse)

    def _movement(self, delta, primary):
        if Config.get("behaviour.primary_movement_hierarchic") ^ primary:
            self.app.tm.current.view.move_flat(delta)
        else:
            self.app.tm.current.view.move_hierarchic(delta)

    def down(self):
        self._movement(1, True)

    def up(self):
        self._movement(-1, True)

    def down_secondary(self):
        self._movement(1, False)

    def up_secondary(self):
        self._movement(-1, False)

    def cut_task(self):
        self.app.tm.current.cut()

    def delete_task(self):
        if self.app.get_input("Delete task forever? (y/n)") == "y":
            self.app.tm.current.delete()

    def copy_cursor(self):
        self.app.tm.current.copy_cursor()

    def paste_after(self):
        self.app.tm.current.paste(below=False, before=False)

    def paste_before(self):
        self.app.tm.current.paste(below=False, before=True)

    def paste_below_append(self):
        self.app.tm.current.paste(below=True, before=False)

    def paste_below_prepend(self):
        self.app.tm.current.paste(below=True, before=True)

    def _new_task_edit(self, new_task):
        self.app.draw()
        self.edit_title()
        if new_task.title == "":
            self.app.tm.current.delete(new_task)
            return False
        else:
            return True

    def new_task_child_bottom(self):
        new_task = self.app.tm.current.new_task_child_bottom()
        self._new_task_edit(new_task)

    def new_task_child_top(self):
        new_task = self.app.tm.current.new_task_child_top()
        self._new_task_edit(new_task)

    def new_task_above(self):
        new_task = self.app.tm.current.new_task_sibling_before()
        self._new_task_edit(new_task)

    def new_task_below(self):
        new_task = self.app.tm.current.new_task_sibling_after()
        if not self._new_task_edit(new_task):
            self.up()

    def left(self):
        try:
            self.app.tm.current.view.move_treeup()
        except TreeError:
            pass

    def right(self):
        try:
            self.app.tm.current.view.move_treedown()
        except TreeError:
            self.new_task_child_top()

    def collapse(self):
        self.app.tm.current.cursor.toggle_collapse()

    @task_modification
    def toggle_done(self):
        c = self.app.tm.current.cursor
        if not Config.get("behaviour.show_done"):
            self.app.tm.current.view.move_hierarchic(-1)

        c.toggle_done()

    @task_modification
    def toggle_cancelled(self):
        c = self.app.tm.current.cursor
        if not Config.get("behaviour.show_cancelled"):
            self.app.tm.current.view.move_hierarchic(-1)

        c.toggle_cancelled()

    def toggle_config(self, config_uri):
        if Config.get(config_uri):
            Config.set(config_uri, False)
        else:
            Config.set(config_uri, True)

        self.app.tm.outdate_tree_lists()

    def toggle_show_done(self):
        while self.app.tm.current.cursor.done:
            self.app.tm.current.view.move_hierarchic(-1)

        self.toggle_config("behaviour.show_done")


    def toggle_show_cancelled(self):
        while self.app.tm.current.cursor.cancelled:
            self.app.tm.current.view.move_hierarchic(-1)

        self.toggle_config("behaviour.show_cancelled")

    def quit_nosave(self):
        if self.app.get_input("Really quit without saving? (y/n)") == "y":
            self.app.quit()

    def quit(self):
        self.app.tm.save_all()
        # return paths of currently opened files 
        return self.app.quit()

    def save(self):
        self.app.tm.save_all()
        self.app.message = "Saved" 

    def schedule_up(self):
        self.app.tm.schedule.move_up()

    def schedule_down(self):
        self.app.tm.schedule.move_down()

    def schedule_goto_today(self):
        self.app.tm.schedule.move_today()

    def schedule_top(self):
        self.app.tm.schedule.move_top()

    def hide_categories(self):
        cats = self.app.get_input("Hide").split()
        self.app.tm.current.hide_categories(cats)
    
    def unhide_categories(self):
        cats = self.app.get_input("Unhide").split()
        self.app.tm.current.unhide_categories(cats)

    def show_only_categories(self):
        cats = self.app.get_input("Show only").split()
        self.app.tm.current.show_only_categories = cats

    def unhide_all_categories(self):
        self.app.tm.current.unhide_all_categories()

    def show_all_categories(self):
        self.app.tm.current.unhide_all_categories()
        self.app.tm.current.show_only_categories = set()

    def move_cursor_up(self):
        self.app.tm.current.move_selected_task_up()

    def move_cursor_down(self):
        self.app.tm.current.move_selected_task_down()

    def move_cursor_left(self):
        self.app.tm.current.move_selected_task_treeup()

    @task_modification
    def set_scheduled_today(self):
        self.app.tm.current.cursor.scheduled = date.today()

    @task_modification
    def set_scheduled_tomorrow(self):
        self.app.tm.current.cursor.scheduled = date.today() + timedelta(days=1)

    @task_modification
    def set_due_today(self):
        self.app.tm.current.cursor.due = date.today() 

    @task_modification
    def set_due_tomorrow(self):
        self.app.tm.current.cursor.due = date.today() + timedelta(days=1)

    def next_tab(self):
        self.app.tm.next_tab()

    def prev_tab(self):
        self.app.tm.prev_tab()

    def new_tab(self):
        path = self.app.get_input("Enter filename to open/create")
        if path != "" and not path is None:
            self.app.tm.open_tree(os.path.expanduser(path))

    def close_tab(self):
        if len(self.app.tm.trees) > 0:
            self.app.tm.close_current_tree()
        else:
            return self.quit()

    def close_all_tabs(self):
        self.app.tm.close_all()

    def timewarrior_start(self):
        if Config.get("plugins.timewarrior"):
            import ext.timewarrior as timewarrior
            msg = timewarrior.start_task(self.app.tm.current.cursor, Config.get("plugins.timewarrior_parents_as_tags"))
            if msg is None:
                msg = ""
            if msg != "":
                msg = ": \"" + msg.replace("\n", " ") + "\""
            self.app.message = "started task" + msg

    def timewarrior_stop(self):
        if Config.get("plugins.timewarrior"):
            import ext.timewarrior as timewarrior
            msg = timewarrior.stop()
            if msg is None:
                msg = ""
            if msg != "":
                msg = ": \"" + msg.replace("\n", " ") + "\""
            self.app.message = "stopped task" + msg
