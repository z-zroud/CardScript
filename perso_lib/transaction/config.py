import logging

# 终端默认设置
terminal_cfg = {
    '':''
}

# 用户可根据该函数重置终端相关数据
def set_termianl(tag,value):
    if terminal_cfg.get(tag):
        terminal_cfg.setdefault(tag,value)

def get_terminal(tag,length=None):
    value = terminal_cfg.get(tag)
    if not value:
        if length:
            value = '0' * length
        logging.info('can not require terminal settings for tag %s',tag)
    return value


