import os
from ctypes import *

dll_name = 'Authencation.dll'
dll_depends = 'sqlite3.dll'
dll_depends2 = 'ChineseSM.dll'
dll_path = os.path.dirname(os.path.abspath(__file__))
dir_list = dll_path.split(os.path.sep)
dll_path = os.path.sep.join(dir_list) + os.path.sep + "dll" + os.path.sep
dll_depends = dll_path + dll_depends
dll_depends2 = dll_path + dll_depends2
dll_name = dll_path + dll_name
CDLL(dll_depends)
CDLL(dll_depends2)
_authencation_lib = CDLL(dll_name)


def gen_rsa(cert_len,cert_exp):
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
    _authencation_lib.GenRSA(cert_len,byte_cert_exp,d,n,p,q,dp,dq,qinv)
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
    _authencation_lib.GenIssuerCert(byte_p_d,byte_p_n,byte_format_flag,byte_issue_bin,byte_expiry_date,byte_n,byte_exp,cert,remainder)
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
    _authencation_lib.GenIccCert(byte_issuer_d,byte_issuer_n,byte_card_no,byte_expiry_date,byte_icc_n,byte_icc_exp,byte_sig_data,cert,remainder)
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
    _authencation_lib.GenSSDA(byte_d,byte_n,byte_sig_data,byte_tag82,byte_dac,tag93)
    return bytes.decode(tag93.value)

def gen_kcv(app_key,algorithm_type='DES'):
    byte_key = str.encode(app_key)
    kcv_key = create_string_buffer(33)
    if algorithm_type == 'DES':
        _authencation_lib.GenDesKcv(byte_key,kcv_key,33)
    else:
        _authencation_lib.GenSmKcv(byte_key,kcv_key,33)
    return bytes.decode(kcv_key.value)[0:6]

def gen_app_key_kcv(app_key,algorithm_type='DES'):
    byte_ac = str.encode(app_key[0:32])
    byte_mac = str.encode(app_key[32:64])
    byte_enc = str.encode(app_key[64:])
    kcv_ac = create_string_buffer(33)
    kcv_mac = create_string_buffer(33)
    kcv_enc = create_string_buffer(33)
    if algorithm_type == 'DES':
        _authencation_lib.GenDesKcv(byte_ac,kcv_ac,33)
        _authencation_lib.GenDesKcv(byte_mac,kcv_mac,33)
        _authencation_lib.GenDesKcv(byte_enc,kcv_enc,33)
    else:
        _authencation_lib.GenSmKcv(byte_ac,kcv_ac,33)
        _authencation_lib.GenSmKcv(byte_mac,kcv_mac,33)
        _authencation_lib.GenSmKcv(byte_enc,kcv_enc,33)
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
        _authencation_lib.GenUdk(byte_mdk_ac,byte_tag5A,byte_tag5F34,udk_ac,0)
        _authencation_lib.GenUdk(byte_mdk_mac,byte_tag5A,byte_tag5F34,udk_mac,0)
        _authencation_lib.GenUdk(byte_mdk_enc,byte_tag5A,byte_tag5F34,udk_enc,0)
    else:
        _authencation_lib.GenUdk(byte_mdk_ac,byte_tag5A,byte_tag5F34,udk_ac,1)
        _authencation_lib.GenUdk(byte_mdk_mac,byte_tag5A,byte_tag5F34,udk_mac,1)
        _authencation_lib.GenUdk(byte_mdk_enc,byte_tag5A,byte_tag5F34,udk_enc,1)
    return bytes.decode(udk_ac.value) + bytes.decode(udk_mac.value) + bytes.decode(udk_enc.value)

