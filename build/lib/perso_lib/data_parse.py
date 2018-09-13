import os
import sys
from ctypes import *

__all__ = ['TL','AFL','TLV','parse_tl','parse_afl','parse_tlv']

_dll_name = 'DataParse.dll'
_dll_path = os.path.dirname(os.path.abspath(__file__))
_dir_list = _dll_path.split(os.path.sep)
_dll_path = os.path.sep.join(_dir_list) + os.path.sep + "dll" + os.path.sep + _dll_name
_data_parse_lib = CDLL(_dll_path)


class _TL(Structure):
    _fields_ = [("tag",c_char_p),("len",c_uint)]

class TL:
    def __init__(self):
        self.tag = ''
        self.len = 0

class _AFL(Structure):
    _fields_ = [("sfi",c_int),
                ("record_no",c_int),
                ("is_static_sign_data",c_bool)
        ]

class AFL:
    def __init__(self):
        self.sfi = 0
        self.record_no = 0
        self.is_static_sign_data = False

# this comment shows how to construct self-embed construct
# base on C/C++ strut
# # # # # # # class TLVEntity(Structure):
# # # # # # #     pass

# # # # # # # TLVEntity._fields_ = [("tag",c_char_p),
# # # # # # #                 ("length",c_char_p),
# # # # # # #                 ("value",c_char_p),
# # # # # # #                 ("tag_size",c_uint),
# # # # # # #                 ("len_size",c_uint),
# # # # # # #                 ("is_template",c_bool),
# # # # # # #                 ("subTLVEntity",POINTER(TLVEntity)),
# # # # # # #                 ("subTLVnum",c_uint)
# # # # # # #         ]

class _TLV(Structure):
    _fields_ = [("is_template",c_bool),
                ("level",c_int),
                ("tag",c_char_p),
                ("len",c_uint),
                ("value",c_char_p)
        ]

class TLV:
    def __init__(self):
        self.is_template = False
        self.level = 0
        self.tag = ''
        self.len = 0
        self.value = ''

class TV:
    def __init__(self,tag,value):
        self.tag = tag
        self.value = value

# parse tl struct 
def parse_tl(buffer):
    tls = []
    bytes_buffer = str.encode(buffer)
    tl_arr = _TL * 30
    _tls = tl_arr()
    tls_count = c_int(30)
    _data_parse_lib.ParseTL(bytes_buffer,_tls,byref(tls_count))
    for index in range(tls_count.value):
        tl = TL()
        tl.tag = bytes.decode(_tls[index].tag)
        tl.len = _tls[index].len
        tls.append(tl)
        #print("TL tag=",tl.tag," len=",tl.len)
    return tls

# parse afl struct
def parse_afl(buffer):
    afls = []
    bytes_buffer = str.encode(buffer)
    afl_arr = _AFL * 30
    _afls = afl_arr()
    afl_count = c_int(30)
    _data_parse_lib.ParseAFL(bytes_buffer,_afls,byref(afl_count))
    for index in range(afl_count.value):
        afl = AFL()
        afl.is_static_sign_data = _afls[index].is_static_sign_data
        afl.record_no = _afls[index].record_no
        afl.sfi = _afls[index].sfi
        afls.append(afl)
    return afls

def parse_tlv(buffer):
    tlvs = []
    bytes_buffer = str.encode(buffer)
    tlv_arr = _TLV * 30
    _tlvs = tlv_arr()
    tlv_count = c_uint(30)
    _data_parse_lib.ParseTLV.restype = c_bool
    ret = _data_parse_lib.ParseTLV(bytes_buffer,_tlvs,byref(tlv_count))   
    for index in range(tlv_count.value):
        _tlv = TLV()
        _tlv.is_template = _tlvs[index].is_template
        _tlv.len = _tlvs[index].len
        _tlv.level = _tlvs[index].level
        _tlv.tag = bytes.decode(_tlvs[index].tag)
        _tlv.value = bytes.decode(_tlvs[index].value)
        tlvs.append(_tlv)
    return tlvs

if __name__ == '__main__':
    tls = parse_tl("9F1F055F2D04")
    afls = parse_afl("08010100100103011010100018010400")
    tlvs = parse_tlv("6F27840E315041592E5359532E4444463031A5158801015F2D027A68BF0C0A9F4D020B0ADF4D020C0A")

