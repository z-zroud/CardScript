import os
import sys
from ctypes import *
from perso_lib import data_parse_lib,tool_lib


def get_files(dirname):
    files = []
    if os.path.exists(dirname):
        filenames = os.listdir(dirname)
        for name in filenames:
            file_path = os.path.join(dirname,name)
            if os.path.isfile(file_path):
                files.append(file_path)
    return files

# convert int value to hex string type
# eg. 48 => '30'
def int_to_hex_str(int_value):
    '''将整形转化为十六进制的字符串'''
    num = '{0:X}'.format(int_value)
    if len(num) % 2 != 0:
        num = '0' + num
    return num

def str_to_int(str_value):
    '''将十六进制的字符串转化为整形'''
    result = 0
    str_len = len(str_value)
    for i in range(str_len):
        result += int(str_value[i],16) * (16 ** (str_len - 1 - i))
    return result

#convert hex str to int, eg. '30' => 48
def hex_str_to_int(str_value):
    '''将十六进制的字符串转化为整形'''
    return int(str_value,16)

    
# get bcd data hex str len
def get_strlen(data):
    '''获取数据的长度，并转化为十六进制的字符串'''
    bcd_len = int(len(data) / 2)
    return int_to_hex_str(bcd_len)

# convert int sw to string sw
def str_sw(sw, prefix=True):
    if prefix:
        s = '0x{0:04X}'.format(sw)
    else:
        s = '{0:04X}'.format(sw)
    return s

#convert bcd to asc str
def bcd_to_str(bcd):
    result = ""
    if len(bcd) % 2 != 0:
        return result
    for index in range(0, len(bcd), 2):
        temp = bcd[index:index + 2]
        asc = chr(int(temp,16))
        result += asc
    return result

# convert str to bcd str
def str_to_bcd(s):
    bcd = ''
    for index in range(len(s)):
        asc = ord(s[index])
        bcd += int_to_hex_str(asc)
    return bcd

def is_hex_str(hex_str):
    str_list = '0123456789ABCDEF'
    for c in hex_str:
        if c not in str_list:
            return False
    return True

def base64_to_bcd(base64):
    bcd = create_string_buffer(1024 * 2)
    bytes_base64 = str.encode(base64)
    tool_lib.Base64ToBcd(bytes_base64,bcd,1024 * 2)
    return bytes.decode(bcd.value)

def assemble_tlv(tag,data):
    '''拼接TLV格式，不考虑数据长度超过0xFF的情况'''
    data_len = len(data)
    if data_len >= 0x80 * 2:
        return tag + '81' + get_strlen(data) + data
    else:
        return tag + get_strlen(data) + data

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
    data_parse_lib.ParseTL(bytes_buffer,_tls,byref(tls_count))
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
    data_parse_lib.ParseAFL(bytes_buffer,_afls,byref(afl_count))
    for index in range(afl_count.value):
        afl = AFL()
        afl.is_static_sign_data = _afls[index].is_static_sign_data
        afl.record_no = _afls[index].record_no
        afl.sfi = _afls[index].sfi
        afls.append(afl)
    return afls

def remove_dgi(buffer,dgi):
    if len(buffer) < 4:
        return buffer
    buffer_dgi = buffer[0:len(dgi)]
    if buffer_dgi != dgi:
        return buffer
    else:
        buffer = buffer[len(dgi) : len(buffer)]
        if buffer[0:2] == '81':
            return buffer[4:len(buffer)]
        elif buffer[0:2] == '82':
            return buffer[6:len(buffer)]
        else:
            return buffer[2:len(buffer)]

def remove_template70(buffer):
    if len(buffer) < 4 or buffer[0:2] != '70':
        return buffer
    buffer = buffer[2:len(buffer)]
    if buffer[0:2] == '81':
        return buffer[4:len(buffer)]
    elif buffer[0:2] == '82':
        return buffer[6:len(buffer)]
    else:
        return buffer[2:len(buffer)]

# 尽管IsTLV返回的是bool类型，但它不一定返回的是0或者1
# 有可能返回其他整形，但若返回的是false,那ret肯定为0
def is_tlv(buffer):
    buffer_len = len(buffer)
    bytes_buffer = str.encode(buffer)
    data_parse_lib.IsTLV.restype = c_bool
    ret = data_parse_lib.IsTLV(bytes_buffer,buffer_len)
    # print(ret)
    # print('   ' + buffer)
    return False if ret == 0 else True

def is_rsa(dgi):
    dgi_list = ['8201','8202','8203','8204','8205','8000']
    if dgi in dgi_list:
        return True
    return False

def parse_tlv(buffer):
    tlvs = []
    bytes_buffer = str.encode(buffer)
    tlv_arr = _TLV * 30
    _tlvs = tlv_arr()
    tlv_count = c_uint(30)
    data_parse_lib.ParseTLV.restype = c_bool
    ret = data_parse_lib.ParseTLV(bytes_buffer,_tlvs,byref(tlv_count))
    if ret is False:
        return tlvs
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
    print(str_to_bcd('000PRN'))
    print(bcd_to_str("30303038"))
    print(int_to_hex_str(4))
    print(int_to_hex_str(26))
    print(get_strlen("3F00"))
    print(get_strlen("32149895898392844"))
    print(str_to_bcd("你好111"))
    print(base64_to_bcd('Lm595NXdgKqzX53sb1oEjviRYZ+lTW7rrg9LcJZ/60Hy8R+7Eq6x7srFTydmxEI/S2jkD1jkXHxM103oy1JXK2sqZG3TiIHB'))
    import pyDes,base64
    text = '333162134000000218'
    key = '3930340065cc47e9989f36af'
    k = pyDes.triple_des(key, pyDes.ECB,None, pad=None, padmode=pyDes.PAD_PKCS5)
    d = k.encrypt(text)
    res = base64.standard_b64encode(d)
    print(res)