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
                'edit_title' : 'g',
                'edit_categories' : 'c',
                'edit_scheduled' : 's',
                'edit_due' : 'd',
                'edit_priority' : 'P',
                'collapse' : 'f',
                'toggle_done' : 'D',
                'toggle_cancelled' : 'C',
                'toggle_show_done' : 'F',
                'toggle_show_cancelled' : 'V',
                'replace_title' : 'E',
                'edit_text' : 'x',
                'sort_title' : 'ot',
                'sort_priority' : 'op',
                'sort_category' : 'oc',
                'sort_due' : 'od',
                'sort_scheduled' : 'os',
                'sort_natural' : 'oo',
                'sort_title_rev' : 'oT',
                'sort_priority_rev' : 'oP',
                'sort_category_rev' : 'oC',
                'sort_due_rev' : 'oD',
                'sort_scheduled_rev' : 'oS',
                'sort_natural_rev' : 'oO',
                'new_task_child_bottom' : 'i',
                'new_task_child_top' : 'I',
                'new_task_above' : 'U',
                'new_task_below' : 'u',
                'delete_task' : 'W',
                'cut_task' : 'w',
                'paste_before' : 'pP',
                'paste_after' : 'pp',
                'paste_below_prepend' : 'pO',
                'paste_below_append' : 'po',
                'save' : 'S',
                'copy_cursor' : 'y',
                'schedule_down' : 'n',
                'schedule_up' : 'm',
                'schedule_top' : 'M',
                'schedule_goto_today' : 'N',


            },
            'behaviour' : {
                'scrolloffset_tree' : 2,
                'scrolloffset_schedule' : 1,
                'show_done' : True,
                'show_cancelled' : False,
                'autosave' : True,
                'sort_tagged_below' : True,
                'follow_schedule' : True
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
