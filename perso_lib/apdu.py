import sys
import logging
from enum import Enum
from perso_lib import pcsc
from perso_lib import utils
from perso_lib.gen_kmc_session import SECURE_LEVEL,DIV_METHOD
from perso_lib import gen_kmc_session
from perso_lib import algorithm


class Store_Data_Type:
    plant = "00"
    encrypted = "60"
    end_data = "80"

class Crypto_Type(Enum):
    AAC = 0
    TC = 4
    ARQC = 8
    AAC_CDA = 1
    TC_CDA = 5
    ARQC_CDA = 9


def gpo(pdol,resp_sw_list=(0x9000,)):
    pdol_len = utils.get_strlen(pdol)
    data = '83' + pdol_len + pdol
    data_len = utils.get_strlen(data)
    cmd = '80A80000' + data_len + data
    return pcsc.send_raw(cmd,resp_sw_list)

def read_record(sfi,record_no,resp_sw_list=(0x9000,)):
    sfi = (sfi << 3) + 4
    p1 = utils.int_to_hex_str(record_no)
    p2 = utils.int_to_hex_str(sfi)
    cmd = '00B2' + p1 + p2
    return pcsc.send_raw(cmd,resp_sw_list)

def gac(crypto_type,data,resp_sw_list=(0x9000,)):
    p1 = str(crypto_type.value) + '0'
    cmd = '80AE' + p1 + '00' + utils.get_strlen(data) + data
    return pcsc.send_raw(cmd,resp_sw_list)
    
def delete_app(aid,resp_sw_list=(0x9000,)):
    aid_len = utils.get_strlen(aid)
    data = '4F' + aid_len + aid
    data_len = utils.get_strlen(data)
    cmd = '80E40000' + data_len + data
    return pcsc.send_raw(cmd,resp_sw_list)

def install_app(packet_aid,applet_aid,inst_aid,priviliage,install_param,token='00',resp_sw_list=(0x9000,)):
    cmd_header = '80E60C00'
    packet_aid_len = utils.get_strlen(packet_aid)
    applet_aid_len = utils.get_strlen(applet_aid)
    inst_aid_len = utils.get_strlen(inst_aid)
    priviliage_len = utils.get_strlen(priviliage)
    install_param_len = utils.get_strlen(install_param)
    data = packet_aid_len + packet_aid + applet_aid_len + applet_aid + inst_aid_len + inst_aid
    data += priviliage_len + priviliage + install_param_len + install_param + token
    cmd = cmd_header + utils.get_strlen(data) + data
    return pcsc.send_raw(cmd,resp_sw_list) 

# Select Command
def select(instance_id):
    aid_len = utils.get_strlen(instance_id)
    cmd = '00A40400' + aid_len + instance_id
    return pcsc.send_raw(cmd) 

def select_file(file_id):
    file_id_len = utils.get_strlen(file_id)
    cmd = '00A40000' + file_id_len + file_id
    return pcsc.send_raw(cmd)

def get_data(tag):
    if len(tag) == 2:
        tag = '00' + tag
    cmd = '80CA' + tag
    return pcsc.send_raw(cmd)

store_count = 0
def store_data(data_type,data,reset=False):
    global store_count
    if reset:
        store_count = 0
    cmd_header = "80E2" + data_type
    cmd_header += utils.int_to_hex_str(store_count)
    cmd = cmd_header + utils.get_strlen(data) + data
    store_count += 1
    if data_type == "80":
        store_count = 0
    return pcsc.send_raw(cmd,(0x9000,))

def store_data_mac(data,data_type,dek_session_key,mac_key,reset=False):
    global store_count
    if reset:
        store_count = 0
    cmd_header = "84E2" + data_type
    cmd_header += utils.int_to_hex_str(store_count)
    data = algorithm.des3_cbc_encrypt(dek_session_key,data)
    cmd = cmd_header + utils.get_strlen(data) + data
    store_count += 1
    if data_type == "80":
        store_count = 0
    return pcsc.send_raw(cmd,(0x9000,))

def init_update(host_challenge, key_verson='00', key_id='00'):
    cmd_header = '8050' + key_verson + key_id
    cmd = cmd_header + utils.get_strlen(host_challenge) + host_challenge
    return pcsc.send_raw(cmd)

def internal_auth(ddol):
    cmd = '00880000' + utils.get_strlen(ddol) + ddol
    return pcsc.send_raw(cmd)

def external_auth(arpc,arc):
    data = arpc + arc
    cmd = '00820000' + utils.get_strlen(data) + data
    return pcsc.send_raw(cmd)

def ext_auth(kmc,div_method,secure_level,host_challenge,init_update_data):
    cmd = ''
    cmd_data_len = '10'
    mac = ''
    if secure_level == SECURE_LEVEL.SL_MAC:
        cmd = '84820100'
    elif secure_level == SECURE_LEVEL.SL_MAC_ENC:
        cmd = '84820300'
    else:
        cmd = '84820000'
    scp = init_update_data[22:24]
    card_challenge = init_update_data[24:40]
    card_cryptogram = init_update_data[40:56]  
    dek_session_key,mac_session_key,enc_session_key = gen_kmc_session.gen_session_key(kmc,div_method,host_challenge,init_update_data)
    card_cryptogram_input = host_challenge + card_challenge
    card_mac = algorithm.des3_full_mac(enc_session_key, card_cryptogram_input)
    if card_mac != card_cryptogram:
        resp = pcsc.ApduResponse()
        resp.sw = 0x6300
        return '',resp
    host_cryptogram_input = card_challenge + host_challenge
    host_mac = algorithm.des3_full_mac(enc_session_key,host_cryptogram_input)
    cmd += cmd_data_len + host_mac
    if scp == '01':
        mac = algorithm.des3_full_mac(enc_session_key, cmd)
    else:	#scp == '02'
        mac = algorithm.des3_mac(mac_session_key, cmd)
    cmd += mac
    return dek_session_key,pcsc.send_raw(cmd)

def open_secure_channel(kmc,div_method=DIV_METHOD.NO_DIV,secure_level=SECURE_LEVEL.SL_NO_SECURE):
    host_challenge = '1122334455667788'
    resp = init_update(host_challenge)
    if resp.sw != 0x9000:
        sys.exit()
    dek_session_key,resp = ext_auth(kmc,div_method,secure_level,host_challenge,resp.response)
    if(resp.sw != 0x9000):
        sys.exit(1)
    return dek_session_key
