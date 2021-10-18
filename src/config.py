import configparser
import logging
import curses
class Config:
    _config = {
            'appearance': {
                'tasks_lines' : 50,
                'tasks_columns' : 100,
                'indent': 4,
                'columns' : 'csd',
                'col_scheduled_min' : 10,
                'col_scheduled_max' : 10,
                'col_scheduled_ratio' : 0.08,
                'col_due_min' : 10,
                'col_due_max' : 10,
                'col_due_ratio' : 0.08,
                'col_category_min' : 4,
                'col_category_max' : 16,
                'col_category_ratio' : 0.15,
                'schedule_show' : False,
                'schedule_min' : 10,
                'schedule_max' : 40,
                'schedule_ratio' : 0.2,
                'description_show' : False,
                'description_min' : 6,
                'description_max' : 20,
                'description_ratio' : 0.2,
                'indent_guide' : "⁝",
                'columns_max_total_ratio' : 0.3,
                'columns_border' : True
            },
            'keys' : {
                'down' : 'j',
                'up' : 'k',
                'left' : 'h',
                'right' : 'l',
                'down_flat' : 'J',
                'up_flat' : 'K',

                'schedule_down' : 'n',
                'schedule_up' : 'm',
                'schedule_top' : 'M',
                'schedule_goto_today' : 'N',

                'move_cursor_up' : 'B',
                'move_cursor_down' : 'b',

                'replace_title' : 'C',
                'edit_title' : 'i',
                'edit_categories' : 'cc',
                'edit_scheduled' : 'cs',
                'edit_due' : 'cd',
                'edit_priority' : 'cp',
                'edit_text' : 'a',

                'toggle_done' : 'f',
                'toggle_cancelled' : 'g',

                'set_scheduled_today' : 'e',
                'set_scheduled_tomorrow' : 'E',
                'set_due_today' : 'r',
                'set_due_tomorrow' : 'R',

                'collapse' : 'v',
                'toggle_show_done' : 'F',
                'toggle_show_cancelled' : 'G',
                'toggle_sort_tagged_below' : 'V',
                'show_only_categories' : 'z',
                'show_all_categories' : 'Z',
                'hide_categories' : 'x',
                'unhide_categories' : 'X',
                'unhide_all_categories' : 'w',

                'sort_title' : 'st',
                'sort_priority' : 'sp',
                'sort_category' : 'sc',
                'sort_due' : 'sr',
                'sort_scheduled' : 'se',
                'sort_natural' : 'ss',
                'sort_title_rev' : 'sT',
                'sort_priority_rev' : 'sP',
                'sort_category_rev' : 'sC',
                'sort_due_rev' : 'sR',
                'sort_scheduled_rev' : 'sE',
                'sort_natural_rev' : 'sS',
                'sort_date_rev' : 'sD',
                'sort_date' : 'sd',

                'new_task_child_bottom' : 'A',
                'new_task_child_top' : 'I',
                'new_task_above' : 'O',
                'new_task_below' : 'o',

                'delete_task' : 'dD',
                'cut_task' : 'dd',
                'paste_before' : 'pP',
                'paste_after' : 'pp',
                'paste_below_prepend' : 'pO',
                'paste_below_append' : 'po',
                'copy_cursor' : 'y',

                'save' : 'S',
                'quit' : 'q',
                'quit_nosave' : 'Q'
                
            },
            'behaviour' : {
                'scrolloffset_tree' : 2,
                'scrolloffset_schedule' : 1,
                'show_done' : True,
                'show_cancelled' : False,
                'autosave' : True,
                'sort_tagged_below' : True,
                'follow_schedule' : True,
                'filter_categories_schedule' : False,
                'auto_move_up' : True,
                'roundtrip' : False
            }
    }


    @staticmethod
    def load(path):
        config = configparser.ConfigParser()
        config.read(path)
        for sec_name in config:
            if not sec_name == 'DEFAULT':
                if not sec_name in Config._config:
                    Config._config[sec_name] = {}

                for key in config[sec_name]:
                    if key in Config._config[sec_name]:
                        t = type(Config._config[sec_name][key])
                    else:
                        t = str

                    try:
                        if t is bool:
                            Config._config[sec_name][key] = (config[sec_name][key] == "True")
                        else:
                            Config._config[sec_name][key] = t(config[sec_name][key])
                    except (TypeError, ValueError) as e:
                        raise e

    @staticmethod
    def printall():
        print(Config._config)

    @staticmethod
    def get(uri):
        section, key = uri.split(".")
        if not section in Config._config:
            raise KeyError("Given section not existing")
        return Config._config[section][key]

    @staticmethod
    def set(uri, value):
        section, key = uri.split(".")
        if not section in Config._config:
            raise KeyError("Given section not existing")
        Config._config[section][key] = value

    @staticmethod
    def get_section(section):
        if not section in Config._config:
            raise KeyError("Given section not existing")
        return Config._config[section]
