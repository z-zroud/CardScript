from perso_lib import pcsc
from perso_lib import utils
from perso_lib.gen_kmc_session import SECURE_LEVEL,DIV_METHOD
from perso_lib import gen_kmc_session
from perso_lib import des

class Store_Data_Type:
    plant = "00"
    encrypted = "60"
    end_data = "80"

# Select Command
def select(instance_id):
    aid_len = utils.get_strlen(instance_id)
    cmd = '00A40400' + aid_len + instance_id
    return pcsc.send(cmd) 

def select_file(file_id):
    file_id_len = utils.get_strlen(file_id)
    cmd = '00A40000' + file_id_len + file_id
    return pcsc.send(cmd)

store_count = 0
def store_data(data,data_type,reset=False):
    global store_count
    if reset:
        store_count = 0
    cmd_header = "80E2" + data_type
    cmd_header += utils.int_to_hex_str(store_count)
    cmd = cmd_header + utils.get_strlen(data) + data
    store_count += 1
    if data_type == "80":
        store_count = 0
    return pcsc.send(cmd)

def delete_app(aid):
    aid_len = utils.get_strlen(aid)
    data = '4F' + aid_len + aid
    data_len = utils.get_strlen(data)
    cmd = '80E40000' + data_len + data
    return pcsc.send(cmd)

def init_update(host_challenge, key_verson='00', key_id='00'):
    cmd_header = '8050' + key_verson + key_id
    cmd = cmd_header + utils.get_strlen(host_challenge) + host_challenge
    return pcsc.send(cmd)

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
    card_mac = des.des3_full_mac(enc_session_key, card_cryptogram_input)
    if card_mac != card_cryptogram:
        return '',(0x6300,'')
    host_cryptogram_input = card_challenge + host_challenge
    host_mac = des.des3_full_mac(enc_session_key,host_cryptogram_input)
    cmd += cmd_data_len + host_mac
    if scp == '01':
        mac = des.des3_full_mac(enc_session_key, cmd)
    else:	#scp == '02'
        mac = des.des3_mac(mac_session_key, cmd)
    cmd += mac
    return dek_session_key,pcsc.send(cmd)


