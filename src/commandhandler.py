import logging

from .commands import Commands
from .config import Config

class CommandHandler:
    config_call_map = {
            'down' : Commands.down,
            'up' : Commands.up,
            'down_secondary' : Commands.down_secondary,
            'up_secondary' : Commands.up_secondary,
            'left' : Commands.left,
            'right' : Commands.right,
            'collapse' : Commands.collapse,
            'edit_title' : Commands.edit_title,
            'edit_scheduled' : Commands.edit_scheduled,
            'edit_due' : Commands.edit_due,
            'edit_priority' : Commands.edit_priority,
            'edit_categories' : Commands.edit_categories,
            'reset_scheduled' : Commands.reset_scheduled,
            'reset_due' : Commands.reset_due,
            'reset_priority' : Commands.reset_priority,
            'reset_categories' : Commands.reset_categories,
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
            'sort_title_rev' : lambda c: Commands.sort_title(c, True),
            'sort_natural_rev' : lambda c: Commands.sort_natural(c, True),
            'sort_priority_rev' : lambda c: Commands.sort_priority(c, True),
            'sort_due_rev' : lambda c: Commands.sort_due(c, True),
            'sort_scheduled_rev' : lambda c: Commands.sort_scheduled(c, True),
            'sort_category_rev' : lambda c: Commands.sort_category(c, True),
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
            'quit_nosave' : Commands.quit_nosave,
            'copy_cursor' : Commands.copy_cursor,
            'schedule_down' : Commands.schedule_down,
            'schedule_up' : Commands.schedule_up,
            'schedule_goto_today' : Commands.schedule_goto_today,
            'schedule_top' : Commands.schedule_top,
            'show_only_categories' : Commands.show_only_categories,
            'show_all_categories' : Commands.show_all_categories,
            'hide_categories' : Commands.hide_categories,
            'unhide_categories' : Commands.unhide_categories,
            'unhide_all_categories' : Commands.unhide_all_categories,
            'set_scheduled_today' : Commands.set_scheduled_today,
            'set_scheduled_tomorrow' : Commands.set_scheduled_tomorrow,
            'set_due_today' : Commands.set_due_today,
            'set_due_tomorrow' : Commands.set_due_tomorrow,
            'move_cursor_up' : Commands.move_cursor_up,
            'move_cursor_down' : Commands.move_cursor_down,
            'move_cursor_left' : Commands.move_cursor_left,
            'sort_date_rev' : lambda c: Commands.sort_date(c, True),
            'sort_date' : Commands.sort_date,
            'toggle_sort_tagged_below' : lambda c: Commands.toggle_config(c, "behaviour.sort_tagged_below"),
            'next_tab' : Commands.next_tab,
            'previous_tab' : Commands.prev_tab,
            'new_tab' : Commands.new_tab,
            'close_tab' : Commands.close_tab,
            'toggle_global_schedule' : lambda c: Commands.toggle_config(c, "behaviour.global_schedule"),
            'toggle_movement' : lambda c: Commands.toggle_config(c, "behaviour.primary_movement_hierarchic"),
            'timewarrior_start' : Commands.timewarrior_start,
            'timewarrior_stop' : Commands.timewarrior_stop,
            'toggle_flat_tree' : lambda c: Commands.toggle_config(c, "behaviour.flat_tree")
    }

    def __init__(self, tasktree_application):
        self.key_actions = {}
        self.keychain_scope = None
        self.commands = Commands(tasktree_application)

        # load bindings
        for action_config, keys in Config.get_section('keys').items():
            if not action_config in CommandHandler.config_call_map:
                raise ValueError("Action '{}' not defined".format(action_config))

            key_actions_last = self.key_actions
            for key in keys[:-1]:
                if not key in key_actions_last:
                    key_actions_last[key] = {}
                key_actions_last = key_actions_last[key]

            key_actions_last[keys[-1]] = CommandHandler.config_call_map[action_config]


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
            action(self.commands)
            self.keychain_scope = None
        else:
            self.keychain_scope = action
