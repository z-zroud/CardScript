from enum import Enum
#原则1. 将枚举类型尽量定义为字符串类型，比整形更具有可理解性

# 脱机数据认证类型
class OfflineType(Enum):
    SDA = 'SDA'
    DDA = 'DDA'
    CDA = 'CDA'
    No_Auth = 'No_Auth'

# 定义应用主秘钥类型
class App_Master_Key(Enum):
    MDK = 'MDK'
    UDK = 'UDK'
    IDN_KEY = 'IDN_KEY'
    CVC3_KEY = 'CVC3_KEY'

class PROCESS_STEP(Enum):
    '''
    定义交易步骤，目前仅定义涉及到有APDU交互的交易步骤
    '''
    SELECT      = 0
    GPO         = 1
    READ_RECORD = 2
    GET_DATA    = 3
    ODA         = 4
    FIRST_GAC   = 5
    SECOND_GAC  = 6



class TransTag:
    '''
    定义了tag信息
    '''
    def __init__(self,step,tag,value):
        self.step = step
        self.tag = tag
        self.value = value
