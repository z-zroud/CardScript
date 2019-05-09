from enum import Enum

class CR(Enum):
    ERROR = 0   # 报错
    WARN = 1    # 警告
    INFO = 2    # 提示
    OK = 3      # OK


def case_startswith(mark,buffer):
    if len(buffer) > 2 and buffer.startswith(mark):
        return CR.OK
    return CR.ERROR

    
def is_support_sda(tag82):
    pass

def is_support_dda(tag82):
    pass

def is_support_cda(tag82):
    pass

def is_support_offline_auth(tag82):
    pass