import os
import sys
from perso_lib import utils
from perso_lib.log import Log
from ctypes import *

__all__ = ['ApduResponse','init','send','get_readers','open_reader','warm_reset']

_has_init = False
_pcsc_lib = None

class ApduResponse:
    def __init__(self):
        self.request = ''
        self.response = ''
        self.sw = 0

#init the smart card reader context
def init():
    '''
    初始化读卡器环境，True表示初始化成功，失败返回False
    '''
    global _has_init
    global _pcsc_lib
    if _has_init == False:
        dll_name = 'PCSC.dll'
        dll_name_depends = 'Log.dll'
        dll_path = os.path.dirname(os.path.abspath(__file__))
        dir_list = dll_path.split(os.path.sep)
        dll_path = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep + dll_name
        dll_path_depends = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep + dll_name_depends
        CDLL(dll_path_depends)
        _pcsc_lib = CDLL(dll_path)
        if _pcsc_lib is not None:
            _has_init = True
        return True
    return False

def send(cmd_header,data,resp_sw_list=(0x9000,)):
    '''
    在连接读卡器后，发送APDU指令。
    cmd_header 表示指令头
    data 表示要发送给终端的数据
    resp_sw_list 表示期望的响应返回码列表，若返回不是期望的响应码，则自动退出APDU的交互
    '''
    cmd = cmd_header + utils.get_strlen(data) + data
    return send_raw(cmd,resp_sw_list)

#send apdu command
def send_raw(cmd,resp_sw_list=None):
    '''
    在连接读卡器后，发送APDU指令。
    cmd 表示要发送的APDU命令，包括命令头，数据长度，数据。
    resp_sw_list 表示期望的响应返回码列表，若返回不是期望的响应码，则自动退出APDU的交互
    '''
    apdu_response = ApduResponse()
    bytes_cmd = str.encode(cmd)
    resp_len = c_int(2048)
    resp_data = create_string_buffer(resp_len.value)
    Log.info('APDU: %s',cmd)
    apdu_response.sw = _pcsc_lib.SendApdu(bytes_cmd,resp_data,resp_len)
    apdu_response.response = bytes.decode(resp_data.value)
    apdu_response.request = cmd
    Log.info('RESP: %X',apdu_response.sw)
    if resp_sw_list and apdu_response.sw not in resp_sw_list:
        sys.exit(1)
    return apdu_response

#Get all smard card readers
def get_readers():
    '''
    获取读卡器名称列表
    '''
    readers = []
    if init() is False:
        return readers
    char_arr_type = c_char_p * 10
    reader_arr = char_arr_type()
    reader_count = c_int(10)
    _pcsc_lib.GetReaders(reader_arr,byref(reader_count))
    for count in range(reader_count.value):
        readers.append(bytes.decode(reader_arr[count]))
    return readers

# Open the specified name reader,now
# you can communicate with APDU command
# after call this function
def open_reader(reader):
    '''
    打开指定名称的读卡器，与之交互
    '''
    #print('selected reader: ', readerName)
    name = str.encode(reader)
    _pcsc_lib.OpenReader.restype = c_bool
    result = _pcsc_lib.OpenReader(name)
    return result

def close_reader():
    '''
    使用完读卡器后，需要关闭资源，防止资源泄露
    '''
    _pcsc_lib.CloseReader()

def warm_reset():
    '''
    热复位
    '''
    _pcsc_lib.WarmReset.restype = c_bool
    return _pcsc_lib.WarmReset()


if __name__ == '__main__':
    readers = get_readers()
    if open_reader(readers[1]):
        resp = send_raw("00A40400 08 A000000333010102")
        print(resp.sw)
    else:
        print("shit")