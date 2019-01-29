import os
from ctypes import *

dll_name = 'Des0.dll'
dll_path = os.path.dirname(os.path.abspath(__file__))
dir_list = dll_path.split(os.path.sep)
dll_path = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep + dll_name
_des_lib = CDLL(dll_path)
# key should be 8 bytes, so this key param should be 16 bytes bcd code
# also the same with data
def des_encrypt(key, data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_des_lib.Des(output,bytes_key,bytes_data)
	return bytes.decode(output.value) 

def des_decrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_des_lib._Des(output,bytes_key,bytes_data)
	return bytes.decode(output.value)

def des3_encrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_des_lib.Des3(output,bytes_key,bytes_data)
	return bytes.decode(output.value)

def des3_decrypt(key,data):
    data_len = len(data)
    output = create_string_buffer(data_len + 1)
    bytes_key = str.encode(key)
    bytes_data = str.encode(data)
    _des_lib._Des3(output,bytes_key,bytes_data)
    return bytes.decode(output.value)

def des3_ecb_decrypt(key,data):
	result = ''
	block_count = len(data) / 16
	for i in range(int(block_count)):
		block_data = data[i * 16 :i* 16 + 16]
		result += des3_decrypt(key,block_data)
	return result


# algorithm description:
# step1. 8 bytes block + 3Des encrypt ==> result1
# step2. next 8 bytes block + 3Des encrypt ==> result2
# step3. recursive... step2
# step4. result = result1 + result2 + ... + resultn
def des3_ecb_encrypt(key,data):	
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_des_lib.Des3_ECB(output,bytes_key,bytes_data,data_len)
	return bytes.decode(output.value)


def des3_cbc_encrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	_des_lib.Des3_CBC(output,bytes_key,bytes_data,data_len)
	return bytes.decode(output.value)	

# algorithm description:
# step1. initData xor block1  + key(L) ==> result1
# step2. result1 xor next block + key(L) ==> result2
# step3. recursive step2 until the last block ==> resultn
# step4. resultn + key(R) decrypt ==> ret1
# step5. ret1 + key(L) encrypt ==> mac
def des3_mac(key, in_data, init_data = '0000000000000000'):
	bytes_key = str.encode(key)
	bytes_init_data = str.encode(init_data)
	bytes_in_data = str.encode(in_data)
	output = create_string_buffer(17)
	_des_lib.DES_3DES_CBC_MAC(bytes_in_data,bytes_key,bytes_init_data,output)
	return bytes.decode(output.value)

def des3_full_mac(key,in_data,init_data = '0000000000000000'):
	bytes_key = str.encode(key)
	bytes_init_data = str.encode(init_data)
	bytes_in_data = str.encode(in_data)
	output = create_string_buffer(17)
	_des_lib.Full_3DES_CBC_MAC(bytes_in_data,bytes_key,bytes_init_data,output)
	return bytes.decode(output.value)


# xor two string. note data1 and data2 must have the same length.
def xor(data1, data2):
	bytes_data1 = str.encode(data1)
	bytes_data2 = str.encode(data2)
	data_len = len(data1)
	output = create_string_buffer(data_len + 1)
	output.value = bytes_data1
	_des_lib.str_xor(output,bytes_data2,data_len)
	return bytes.decode(output.value)

def dcdd(tag56,tag9F6B,key):
	tagDC = des3_mac(key,tag56)
	tagDD = des3_mac(key,tag9F6B)
	return tagDC[-4:] + tagDD[-4:]


if __name__ == "__main__":
	key = 'F6241FCA77459F62ACB2CA38CDFD7175'
	tag56 = '42353335383932303030303030313730375E4249522F544553542020202020202020202020202020202020205E3233313232303130303030303030303030313030'
	tag9F6B = '5358920000001707D2312201000000000010'
	print(dcdd(tag56,tag9F6B,key))


