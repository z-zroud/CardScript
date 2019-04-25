from ctypes import *
import time
from perso_lib import sm_lib,des_lib,auth_lib
from perso_lib import algorithm
from perso_lib.transaction.utils import terminal
from perso_lib.log import Log

def get_ca_pub_key(rid,ca_index):
    '''
    获取CA公钥信息
    '''
    byte_rid = str.encode(rid)
    byte_ca_index = str.encode(ca_index)
    ca = create_string_buffer(2048)
    ca_exp = create_string_buffer(12)
    auth_lib.GenCAPublicKey(byte_ca_index,byte_rid,ca,ca_exp)
    exp = bytes.decode(ca_exp.value)
    if len(exp) % 2 != 0:
        exp = '0' + exp
    return bytes.decode(ca.value),exp

def gen_recovery_data(pN,pE,child_cert):
    '''
    根据证书获取恢复数据
    '''
    byte_pN = str.encode(pN)
    byte_pE = str.encode(pE)
    byte_child_cert = str.encode(child_cert)
    recovery_data = create_string_buffer(2048)
    auth_lib.DES_GenRecovery(byte_pN,byte_pE,byte_child_cert,recovery_data,2048)
    return bytes.decode(recovery_data.value)

def get_issuer_pub_key(ca_pub_key,ca_exp,tag90,tag92,tag9F32,tag5A,tag5F24):
    '''
    获取发卡行公钥
    '''
    issuer_pub_key = ''
    recovery_data = gen_recovery_data(ca_pub_key,ca_exp,tag90)
    if not recovery_data:
        Log.error('can not require recovery data through public cert tag90')
        return issuer_pub_key
    Log.info('issuer recovery data: %s',recovery_data)
    if recovery_data[0:4] != '6A02' or recovery_data[-2:] != 'BC':
        Log.error('recovery data format incorrect, it should start with 6A02 and end with BC')
        return issuer_pub_key
    issuer_bin = recovery_data[4:12].replace('F','')
    if len(issuer_bin) < 3 or not tag5A.startswith(issuer_bin):
        Log.error('issuer_bin: %s',issuer_bin)
        Log.error('tag5A: %s',tag5A)
        Log.error('issuer_bin required from recovery data is not accord with tag5A')
        return issuer_pub_key
    expiry_date = int(recovery_data[14:16] + recovery_data[12:14])
    now = int(time.strftime('%y%m'))
    if expiry_date < now:
        Log.warn('expiry date: %s',recovery_data[14:16] + recovery_data[12:14])
        Log.warn('issuer cert has been overdue')
    if expiry_date < int(tag5F24[0:4]):
        Log.warn('expiry date: %s',recovery_data[14:16] + recovery_data[12:14])
        Log.warn('tag5F24: %s',tag5F24)
        Log.warn('issuer cert overdue earlier than application expiry date')
    if recovery_data[22:26] != '0101':
        Log.error('hash algo flag: %s',recovery_data[22:24])
        Log.error('ipk algo flag: %s',recovery_data[24:26])
        return issuer_pub_key
    hash_input = recovery_data[2:-42] + tag92 + tag9F32
    hash_cert = recovery_data[-42:-2]
    hash_output = algorithm.gen_hash(hash_input)
    if hash_cert != hash_output:
        Log.error('hash input: %s',hash_input)
        Log.error('hash: %s',hash_output)
        Log.error('hash cert: %s',hash_cert)
        Log.error('hash compared failed whereby gen issuer recovery data failed ')
        return issuer_pub_key
    issuer_cert_len = int(recovery_data[26:28],16) * 2
    if issuer_cert_len <= len(ca_pub_key) - 72:
        issuer_pub_key = recovery_data[30:30 + issuer_cert_len]
    else:
        issuer_pub_key = recovery_data[30:-42] + tag92
    Log.info('issuer pub key: %s',issuer_pub_key)
    return issuer_pub_key
    
def get_icc_pub_key(issuer_pub_key,tag9F32,tag9F46,tag9F48,tag9F47,sig_data,tag5A,tag5F24):
    '''
    获取IC卡公钥
    '''
    icc_pub_key = ''
    recovery_data = gen_recovery_data(issuer_pub_key,tag9F32,tag9F46)
    if not recovery_data:
        Log.error('can not require recovery data through public cert tag90')
        return icc_pub_key
    Log.info('icc recovery data: %s',recovery_data)
    if recovery_data[0:4] != '6A04' or recovery_data[-2:] != 'BC':
        Log.error('recovery data format incorrect, it should start with 6A02 and end with BC')
        return icc_pub_key
    pan = recovery_data[4:24].replace('F','')
    if len(pan) < 16 or tag5A.replace('F','') != pan:
        Log.error('PAN: %s',pan)
        Log.error('tag5A: %s',tag5A)
        Log.error('pan required from recovery data is not accord with tag5A')
        return icc_pub_key
    expiry_date = int(recovery_data[26:28] + recovery_data[24:26])
    now = int(time.strftime('%y%m'))
    if expiry_date < now:
        Log.warn('expiry date: %s',recovery_data[26:28] + recovery_data[24:26])
        Log.warn('icc cert has been overdue')
    if expiry_date < int(tag5F24[0:4]):
        Log.warn('expiry date: %s',recovery_data[26:28] + recovery_data[24:26])
        Log.warn('tag5F24: %s',tag5F24)
        Log.info('icc cert overdue earlier than application expiry date')
        return icc_pub_key
    if recovery_data[34:38] != '0101':
        Log.error('hash algo flag: %s',recovery_data[34:36])
        Log.error('ipk algo flag: %s',recovery_data[36:38])
    hash_input = recovery_data[2:-42] + tag9F48 + tag9F47 + sig_data
    hash_cert = recovery_data[-42:-2]
    hash_output = algorithm.gen_hash(hash_input)
    if hash_cert != hash_output:
        Log.error('hash input: %s',hash_input)
        Log.error('hash: %s',hash_output)
        Log.error('hash cert: %s',hash_cert)
        Log.error('hash compared failed whereby gen icc recovery data failed ')
        return icc_pub_key
    icc_cert_len = int(recovery_data[38:40],16) * 2
    if icc_cert_len <= len(issuer_pub_key) - 84:
        icc_pub_key = recovery_data[42:42 + icc_cert_len]
    else:
        icc_pub_key = recovery_data[42:-42] + tag9F48
    Log.info('icc pub key: %s',icc_pub_key)
    return icc_pub_key

def validate_9F4B(icc_pub_key,icc_exp,sig_data,tag9F4B):
    '''
    校验tag9F4B的正确性
    '''
    recovery_data = gen_recovery_data(icc_pub_key,icc_exp,tag9F4B)
    if not recovery_data:
        Log.error('can not require recovery data through public cert tag90')
        return False
    Log.info('tag9F4B recovery data: %s',recovery_data)
    if recovery_data[0:4] not in ('6A05','6A95') or recovery_data[-2:] != 'BC':
        Log.error('recovery data format incorrect, it should start with 6A05/6A95 and end with BC')
        return False
    hash_input = recovery_data[2:-42] + sig_data
    hash_9F4B = recovery_data[-42:-2]
    hash_output = algorithm.gen_hash(hash_input)
    if hash_9F4B != hash_output:
        Log.error('hash in tag9F4B: %s',hash_9F4B)
        Log.error('hash input: %s',hash_input)
        Log.error('hash calc: %s',hash_output)
        Log.error('hash compared failed whereby tag9F4B is not correct ')
        return False
    icc_dynamic_data_len = int(recovery_data[8:10],16) * 2
    tag9F4C = recovery_data[10:10 + icc_dynamic_data_len]
    terminal.set_terminal('9F4C',tag9F4C)
    return True

def gen_arpc_by_des3(key,ac,arc):
    byte_key = str.encode(key)
    byte_ac = str.encode(ac)
    byte_arc = str.encode(arc)
    arpc = create_string_buffer(33)
    auth_lib.GenArpcByDes3(byte_key,byte_ac,byte_arc,arpc,0)
    return bytes.decode(arpc.value)

def gen_arpc_by_mac(key,ac,csu,prop_auth_data=''):
    byte_key = str.encode(key)
    byte_ac = str.encode(ac)
    byte_csu = str.encode(csu)
    byte_prop_auth_data = str.encode(prop_auth_data)
    arpc = create_string_buffer(17)
    auth_lib.GenArpcByMac(byte_key,byte_ac,byte_csu,byte_prop_auth_data,arpc)
    return bytes.decode(arpc.value)

def gen_udk(key,tag5A,tag5F34):
    b_key = str.encode(key)
    b_tag5A = str.encode(tag5A)
    b_tag5F34 = str.encode(tag5F34)
    udk = create_string_buffer(33)
    auth_lib.GenUdk(b_key,b_tag5A,b_tag5F34,0)
    return bytes.decode(udk.value)

def gen_udk_session_key_uics(key,atc):
    '''
    使用分散因子：000000000000 和 ATC
    '''
    b_key = str.encode(key)
    b_tag9F36 = str.encode(atc)
    session_key = create_string_buffer(33)
    auth_lib.GenUdkSessionKey(b_key,b_tag9F36,session_key,0)
    return bytes.decode(session_key.value)

def gen_udk_session_key_emv(key,atc):
    '''
    使用分散因子：F00000000000/0F0000000000 和 ATC
    '''
    b_key = str.encode(key)
    b_tag9F36 = str.encode(atc)
    session_key = create_string_buffer(33)
    auth_lib.GenVisaUdkSessionKey(b_key,b_tag9F36,session_key)
    return bytes.decode(session_key.value)

def gen_ac(key,data):
    return algorithm.des3_mac(key,data)


if __name__ == '__main__':
    pass