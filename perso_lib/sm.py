import os
from ctypes import *

dll_name = 'ChineseSM.dll'
dll_depends = 'libeay32.dll'
dll_path = os.path.dirname(os.path.abspath(__file__))
dir_list = dll_path.split(os.path.sep)
dll_path = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep + dll_name
dll_depends_path = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep + dll_depends
CDLL(dll_depends_path)
_sm_lib = CDLL(dll_path)

def sm4_ecb_decrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_sm_lib.dllSM4_ECB_DEC(bytes_key,bytes_data,output)
	return bytes.decode(output.value)

def sm4_ecb_encrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_sm_lib.dllSM4_ECB_ENC(bytes_key,bytes_data,output)
	return bytes.decode(output.value)


if __name__ == '__main__':
    sm4_ecb_decrypt('11111111111111112222222222222222','11111111111111112222222222222222')