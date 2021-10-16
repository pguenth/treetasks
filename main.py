from src.config import Config
from src.interface import Window
from src.state import State
from curses import wrapper

configfile = "src/test.ini"
taskfile = "temp/test.xml"

def run(stdscr):
    Config.load(configfile)
    State.tm.open_tree(taskfile)
    Window.main(stdscr)

wrapper(run)
