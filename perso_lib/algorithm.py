import os
from ctypes import *
from perso_lib import sm_lib,des_lib,auth_lib

def gen_hash(data):
    byte_data = str.encode(data)
    output = create_string_buffer(64)
    auth_lib.GenHash(byte_data,output,64)
    return bytes.decode(output.value)

def gen_rsa(cert_len,cert_exp='03'):
    '''
    同时生成STD和CRT模式的公私钥对
    cert_len 公钥长度
    cert_exp 生成RSA公钥指数
    返回 D,N,P,Q,DP,DQ,Qinv
    '''
    byte_cert_exp = str.encode(cert_exp)
    d = create_string_buffer(2048)
    n = create_string_buffer(2048)
    p = create_string_buffer(1024)
    q = create_string_buffer(1024)
    dp = create_string_buffer(1024)
    dq = create_string_buffer(1024)
    qinv = create_string_buffer(1024)
    auth_lib.GenRSA(cert_len,byte_cert_exp,d,n,p,q,dp,dq,qinv)
    return bytes.decode(d.value),bytes.decode(n.value),bytes.decode(p.value),bytes.decode(q.value),bytes.decode(dp.value),bytes.decode(dq.value),bytes.decode(qinv.value)


def _gen_cert(p_d,p_n,n,exp,format_flag,issue_bin,expiry_date):
    byte_p_d = str.encode(p_d)
    byte_p_n = str.encode(p_n)
    byte_format_flag = str.encode(format_flag)
    byte_issue_bin = str.encode(issue_bin)
    byte_n = str.encode(n)
    byte_exp = str.encode(exp)
    byte_expiry_date = str.encode(expiry_date)
    cert = create_string_buffer(2048)
    remainder = create_string_buffer(1024)
    auth_lib.GenIssuerCert(byte_p_d,byte_p_n,byte_format_flag,byte_issue_bin,byte_expiry_date,byte_n,byte_exp,cert,remainder)
    return bytes.decode(cert.value),bytes.decode(remainder.value)


def gen_issuer_cert(ca_d,ca_n,issuer_n,issuer_exp,issuer_bin,expiry_date=1220):
    '''
    生成发卡行证书 
    ca_d CA D
    ca_n CA N
    issuer_n 发卡行 公钥
    issuer_exp 发卡行公钥指数
    issuer_bin 发卡行 Bin号
    expiry_date 证书失效日期 可选，默认2020年12月
    返回 tag90,92
    '''
    return _gen_cert(ca_d,ca_n,issuer_n,issuer_exp,"02",issuer_bin,expiry_date)

def gen_icc_cert(issuer_d,issuer_n,icc_n,icc_exp,pan,sig_data,expiry_date=1220):
    '''
    生成IC卡公钥证书
    issuer_d  发卡行 D
    issuer_n  发卡行 N
    icc_n IC卡公钥
    icc_exp IC卡公钥指数
    pan 账号
    sig_data 签名数据(该参数应包括tag82,也就是这个是完整的签名数据)
    expiry_date 证书失效日期 可选，默认2020年12月
    返回tag9F46 9F48
    '''
    byte_issuer_d = str.encode(issuer_d)
    byte_issuer_n = str.encode(issuer_n)
    byte_card_no = str.encode(pan)
    byte_icc_n = str.encode(icc_n)
    byte_icc_exp = str.encode(icc_exp)
    byte_expiry_date = str.encode(expiry_date)
    byte_sig_data = str.encode(sig_data)
    cert = create_string_buffer(2048)
    remainder = create_string_buffer(1024)
    auth_lib.GenIccCert(byte_issuer_d,byte_issuer_n,byte_card_no,byte_expiry_date,byte_icc_n,byte_icc_exp,byte_sig_data,cert,remainder)
    return bytes.decode(cert.value),bytes.decode(remainder.value)

def gen_tag93(d,n,sig_data,tag82,dac='DAC1'):
    '''
    生成静态签名数据
    d 发卡行 D
    n 发卡行 N
    sig_data 签名数据
    tag82 用于签名
    返回tag93
    '''
    byte_d = str.encode(d)
    byte_n = str.encode(n)
    byte_sig_data = str.encode(sig_data)
    byte_tag82 = str.encode(tag82)
    byte_dac = str.encode(dac)
    tag93 = create_string_buffer(1024)
    auth_lib.GenSSDA(byte_d,byte_n,byte_sig_data,byte_tag82,byte_dac,tag93)
    return bytes.decode(tag93.value)

def gen_kcv(app_key,algorithm_type='DES'):
    byte_key = str.encode(app_key)
    kcv_key = create_string_buffer(33)
    if algorithm_type == 'DES':
        auth_lib.GenDesKcv(byte_key,kcv_key,33)
    else:
        auth_lib.GenSmKcv(byte_key,kcv_key,33)
    return bytes.decode(kcv_key.value)[0:6]

def gen_app_key_kcv(app_key,algorithm_type='DES'):
    byte_ac = str.encode(app_key[0:32])
    byte_mac = str.encode(app_key[32:64])
    byte_enc = str.encode(app_key[64:])
    kcv_ac = create_string_buffer(33)
    kcv_mac = create_string_buffer(33)
    kcv_enc = create_string_buffer(33)
    if algorithm_type == 'DES':
        auth_lib.GenDesKcv(byte_ac,kcv_ac,33)
        auth_lib.GenDesKcv(byte_mac,kcv_mac,33)
        auth_lib.GenDesKcv(byte_enc,kcv_enc,33)
    else:
        auth_lib.GenSmKcv(byte_ac,kcv_ac,33)
        auth_lib.GenSmKcv(byte_mac,kcv_mac,33)
        auth_lib.GenSmKcv(byte_enc,kcv_enc,33)
    return bytes.decode(kcv_ac.value)[0:6] + bytes.decode(kcv_mac.value)[0:6] + bytes.decode(kcv_enc.value)[0:6]
    
def gen_app_key(mdk_ac,mdk_mac,mdk_enc,tag5A,tag5F34,algorithm_type='DES'):
    byte_mdk_ac = str.encode(mdk_ac)
    byte_mdk_mac = str.encode(mdk_mac)
    byte_mdk_enc = str.encode(mdk_enc)
    byte_tag5A = str.encode(tag5A)
    byte_tag5F34 = str.encode(tag5F34)
    udk_ac = create_string_buffer(33)
    udk_mac = create_string_buffer(33)
    udk_enc = create_string_buffer(33)
    if algorithm_type == 'DES':
        auth_lib.GenUdk(byte_mdk_ac,byte_tag5A,byte_tag5F34,udk_ac,0)
        auth_lib.GenUdk(byte_mdk_mac,byte_tag5A,byte_tag5F34,udk_mac,0)
        auth_lib.GenUdk(byte_mdk_enc,byte_tag5A,byte_tag5F34,udk_enc,0)
    else:
        auth_lib.GenUdk(byte_mdk_ac,byte_tag5A,byte_tag5F34,udk_ac,1)
        auth_lib.GenUdk(byte_mdk_mac,byte_tag5A,byte_tag5F34,udk_mac,1)
        auth_lib.GenUdk(byte_mdk_enc,byte_tag5A,byte_tag5F34,udk_enc,1)
    return bytes.decode(udk_ac.value) + bytes.decode(udk_mac.value) + bytes.decode(udk_enc.value)

# key should be 8 bytes, so this key param should be 16 bytes bcd code
# also the same with data
def des_encrypt(key, data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	des_lib.Des(output,bytes_key,bytes_data)
	return bytes.decode(output.value) 

def des_decrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	des_lib._Des(output,bytes_key,bytes_data)
	return bytes.decode(output.value)

def des3_encrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	des_lib.Des3(output,bytes_key,bytes_data)
	return bytes.decode(output.value)

def des3_decrypt(key,data):
    data_len = len(data)
    output = create_string_buffer(data_len + 1)
    bytes_key = str.encode(key)
    bytes_data = str.encode(data)
    des_lib._Des3(output,bytes_key,bytes_data)
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
	des_lib.Des3_ECB(output,bytes_key,bytes_data,data_len)
	return bytes.decode(output.value)


def des3_cbc_encrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	des_lib.Des3_CBC(output,bytes_key,bytes_data,data_len)
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
	des_lib.DES_3DES_CBC_MAC(bytes_in_data,bytes_key,bytes_init_data,output)
	return bytes.decode(output.value)

def des3_full_mac(key,in_data,init_data = '0000000000000000'):
	bytes_key = str.encode(key)
	bytes_init_data = str.encode(init_data)
	bytes_in_data = str.encode(in_data)
	output = create_string_buffer(17)
	des_lib.Full_3DES_CBC_MAC(bytes_in_data,bytes_key,bytes_init_data,output)
	return bytes.decode(output.value)

def des3_mac_padding00(key,data):
    b_key = str.encode(key)
    b_data = str.encode(data)
    output = create_string_buffer(17)
    auth_lib.GenMacPading00(b_key,b_data,output)
    return bytes.decode(output.value)

def des3_mac_padding80(key,data):
    b_key = str.encode(key)
    b_data = str.encode(data)
    output = create_string_buffer(17)
    auth_lib.GenMacPading80(b_key,b_data,output,0)
    return bytes.decode(output.value)

# xor two string. note data1 and data2 must have the same length.
def xor(data1, data2):
	bytes_data1 = str.encode(data1)
	bytes_data2 = str.encode(data2)
	data_len = len(data1)
	output = create_string_buffer(data_len + 1)
	output.value = bytes_data1
	des_lib.str_xor(output,bytes_data2,data_len)
	return bytes.decode(output.value)

def dcdd(tag56,tag9F6B,key):
	tagDC = des3_mac(key,tag56)
	tagDD = des3_mac(key,tag9F6B)
	return tagDC[-4:] + tagDD[-4:]



def sm4_ecb_decrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	sm_lib.dllSM4_ECB_DEC(bytes_key,bytes_data,output)
	return bytes.decode(output.value)

def sm4_ecb_encrypt(key,data):
	data_len = len(data)
	output = create_string_buffer(data_len + 1)
	bytes_key = str.encode(key)
	bytes_data = str.encode(data)
	sm_lib.dllSM4_ECB_ENC(bytes_key,bytes_data,output)
	return bytes.decode(output.value)



if __name__ == '__main__':
    ret = ''
    ret = des3_mac_padding00('1C71E2AE1EED4375603877A357427247','04DA9F790E000225E8EECE59D0B9AA000000090000')
    ret = des3_mac_padding80('1C71E2AE1EED4375603877A357427247','04DA9F790E000225E8EECE59D0B9AA000000090000')
    ret = des3_mac('1C71E2AE1EED4375603877A357427247','04DA9F790E000225E8EECE59D0B9AA000000090000')
    ret = ''