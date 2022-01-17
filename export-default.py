from src.config import Config
import configparser

"""
This script reads the current configured defaults in src/config.py
via importing the Config class and exports them in data/default.ini
(potentially overriding this file) using the configparser library
"""

cfg = configparser.ConfigParser()
for sec_name, sec_dict in Config._config.items():
    cfg.add_section(sec_name)
    for k, v in sec_dict.items():
        cfg.set(sec_name, k, str(v))

with open('data/default.ini', mode='w') as f:
    cfg.write(f)
