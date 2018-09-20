import os
import sys
from perso_lib import utils
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
    global _has_init
    global _pcsc_lib
    if _has_init == False:
        dll_name = 'PCSC.dll'
        dll_path = os.path.dirname(os.path.abspath(__file__))
        dir_list = dll_path.split(os.path.sep)
        dll_path = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep + dll_name
        _pcsc_lib = CDLL(dll_path)
        if _pcsc_lib is not None:
            _has_init = True
        return True
    return False

def send(cmd_header,data,resp_sw_list=(0x9000,)):
    cmd = cmd_header + utils.get_strlen(data) + data
    return send_raw(cmd,resp_sw_list)

#send apdu command
def send_raw(cmd,resp_sw_list=(0x9000,)):
    apdu_response = ApduResponse()
    bytes_cmd = str.encode(cmd)
    resp_len = c_int(2048)
    resp_data = create_string_buffer(resp_len.value)
    apdu_response.sw = _pcsc_lib.SendApdu(bytes_cmd,resp_data,resp_len)
    apdu_response.response = bytes.decode(resp_data.value)
    apdu_response.request = cmd
    # sys.exit()
    for sw in resp_sw_list:
        if sw == apdu_response.sw:
            return apdu_response
    sys.exit()

#Get all smard card readers
def get_readers():
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
# after call this function witch returns true
def open_reader(reader):
    #print('selected reader: ', readerName)
    name = str.encode(reader)
    _pcsc_lib.OpenReader.restype = c_bool
    result = _pcsc_lib.OpenReader(name)
    return result

def warm_reset():
    _pcsc_lib.WarmReset.restype = c_bool
    return _pcsc_lib.WarmReset()


if __name__ == '__main__':
    readers = get_readers()
    if open_reader(readers[1]):
        resp = send_raw("00A40400 08 A000000333010102")
        print(resp.sw)
    else:
        print("shit")