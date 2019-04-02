from ctypes import *
import logging
import time
from perso_lib import sm_lib,des_lib,auth_lib
from perso_lib import algorithm
from perso_lib.transaction import config

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
        logging.info('can not require recovery data through public cert tag90')
        return issuer_pub_key
    logging.info('issuer recovery data: %s',recovery_data)
    if recovery_data[0:4] != '6A02' or recovery_data[-2:] != 'BC':
        logging.info('recovery data format incorrect, it should start with 6A02 and end with BC')
        return issuer_pub_key
    pan = recovery_data[4:12].replace('F','')
    if len(pan) < 3 or not tag5A.startswith(pan):
        logging.info('pan required from recovery data is not accord with tag5A')
        return issuer_pub_key
    expiry_date = int(recovery_data[14:16] + recovery_data[12:14])
    now = int(time.strftime('%C%m'))
    if expiry_date < now:
        logging.info('issuer cert has been overdue')
        return issuer_pub_key
    if expiry_date < int(tag5F24[0:4]):
        logging.info('issuer cert overdue earlier than application expiry date')
        return issuer_pub_key
    if recovery_data[22:26] != '0101':
        logging.info('unknown hash algo flag')
        return issuer_pub_key
    hash_input = recovery_data[2:-42] + tag92 + tag9F32
    hash_cert = recovery_data[-42:-2]
    hash_output = algorithm.gen_hash(hash_input)
    if hash_cert != hash_output:
        logging.info('hash compared failed whereby gen issuer recovery data failed ')
        return issuer_pub_key
    issuer_cert_len = int(recovery_data[26:28],16) * 2
    if issuer_cert_len <= len(ca_pub_key) - 72:
        issuer_pub_key = recovery_data[30:30 + issuer_cert_len]
    else:
        issuer_pub_key = recovery_data[30:-42] + tag92
    return issuer_pub_key
    
def get_icc_pub_key(issuer_pub_key,tag9F32,tag9F46,tag9F48,tag9F47,sig_data,tag5A,tag5F24):
    '''
    获取IC卡公钥
    '''
    icc_pub_key = ''
    recovery_data = gen_recovery_data(issuer_pub_key,tag9F32,tag9F46)
    if not recovery_data:
        logging.info('can not require recovery data through public cert tag90')
        return icc_pub_key
    if recovery_data[0:4] != '6A04' or recovery_data[-2:] != 'BC':
        logging.info('recovery data format incorrect, it should start with 6A02 and end with BC')
        return icc_pub_key
    pan = recovery_data[4:24].replace('F','')
    if len(pan) < 16 or tag5A.replace('F','') != pan:
        logging.info('pan required from recovery data is not accord with tag5A')
        return icc_pub_key
    expiry_date = int(recovery_data[26:28] + recovery_data[24:26])
    now = int(time.strftime('%C%m'))
    if expiry_date < now:
        logging.info('icc cert has been overdue')
        return icc_pub_key
    if expiry_date < int(tag5F24[0:4]):
        logging.info('icc cert overdue earlier than application expiry date')
        return icc_pub_key
    if recovery_data[34:38] != '0101':
        logging.info('unknown hash algo flag')
        return icc_pub_key
    hash_input = recovery_data[2:-42] + tag9F48 + tag9F47 + sig_data
    hash_cert = recovery_data[-42:-2]
    hash_output = algorithm.gen_hash(hash_input)
    if hash_cert != hash_output:
        logging.info('hash compared failed whereby gen icc recovery data failed ')
        return icc_pub_key
    icc_cert_len = int(recovery_data[38:40],16) * 2
    if icc_cert_len <= len(issuer_pub_key) - 84:
        icc_pub_key = recovery_data[42:42 + icc_cert_len]
    else:
        icc_pub_key = recovery_data[42:-42] + tag9F48
    return icc_pub_key

def validate_9F4B(icc_pub_key,icc_exp,ddol,tag9F4B):
    '''
    校验tag9F4B的正确性
    '''
    recovery_data = gen_recovery_data(icc_pub_key,icc_exp,tag9F4B)
    if not recovery_data:
        logging.info('can not require recovery data through public cert tag90')
        return False
    if recovery_data[0:4] not in ('6A05','6A95') or recovery_data[-2:] != 'BC':
        logging.info('recovery data format incorrect, it should start with 6A05/6A95 and end with BC')
        return False
    hash_input = recovery_data[2:-42] + ddol
    hash_9F4B = recovery_data[-42:-2]
    hash_output = algorithm.gen_hash(hash_input)
    if hash_9F4B != hash_output:
        logging.info('hash compared failed whereby tag9F4B is not correct ')
        return False
    icc_dynamic_data_len = int(recovery_data[8:10],16) * 2
    tag9F4C = recovery_data[10:10 + icc_dynamic_data_len]
    config.set_termianl('9F4C',tag9F4C)
    return True


if __name__ == '__main__':
    pass