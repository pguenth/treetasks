from enum import Enum
from .treemanager import TreeManager
import logging

class UIMode(Enum):
    NORMAL = 0
    INSERT = 1


# singleton class containing all information related stuff
class State:
    tm = TreeManager()
    #trees = []
    #current_tree = None
    mode = UIMode.NORMAL
    keychain_scope = None
    message = ""

