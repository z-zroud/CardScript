from perso_lib.log import Log
import time

# 终端默认设置
terminal_cfg = {
    'OfflineAuth':'DDA',
    '9F7A':'01',    # 电子现金终端支持指示器，默认支持
    '9F02':'000000000100',      # 授权金额，默认一元
    '9F03':'000000000000',  #其他金额，默认无
    '9F1A':'0156', #终端国家代码，默认中国
    '5F2A':'0156',  #交易货币代码，默认人民币
    'DF69':'00', #SM2算法支持指示器，默认不支持国密
    '9F37':'12345678', #随机数, 默认'12345678'
    '95':'0020106000',#'0000000000',  #终端交易结果，默认全0
    '9A':time.strftime('%C%m%d'), #交易日期
    '9F21':time.strftime('%H%M%S'), #交易时间
    '9C':'00', #交易类型(消费交易)
    '8A':'0000', # 终端生成的授权响应码
    '9F35':'22', # 终端类型
    '9F34':'000000',
    '9F66': '27000000', # 设置终端默认为非接联机交易
    '9F7C':'476F6C64706163454D565465616D'
}

# 用户可根据该函数重置终端相关数据
def set_terminal(tag,value):
    if not terminal_cfg.get(tag):
        terminal_cfg.setdefault(tag,value)
    else:
        terminal_cfg[tag] = value

def get_terminal(tag,length=None,default=None):
    value = terminal_cfg.get(tag)
    if not value:
        if length:
            value = '0' * length * 2
        Log.warn('can not require terminal settings for tag %s',tag)
        if value:
            Log.warn('set tag%s value:%s',tag,value)
            return value
        return default
    else:
        if length and len(value) != length * 2:
            if len(value) >= length * 2:
                value = value[0:length * 2]
            else:
                value += '0' * (length * 2 - len(value))
                Log.warn('padding 0 at tag %s',tag)
    return value

# 常用设置
def set_offline_only():
    set_terminal('9F66','28000000')

def set_currency_code(code):
    set_terminal('5F2A',code)

