# This module generate various of sub key and session key.
# eg. kmc sub key and session key
# eg. udk sub key and session key
from perso_lib import des
from enum import Enum

__all__ = ['DIV_METHOD','SECURE_LEVEL','gen_kmc_sub_key','gen_dek_session_key',
'gen_mac_session_key','gen_enc_session_key','gen_session_key']

class DIV_METHOD(Enum):
    DO_DIV = 0
    DIV_CPG202 = 1
    DIV_CPG212 = 2

class SECURE_LEVEL(Enum):
    SL_NO_SECURE = 0
    SL_MAC = 1
    SL_MAC_ENC = 2

# This method generate three kmc sub key tuple
# tuple(auth,mac,enc)
def gen_kmc_sub_key(kmc, div_method, div_data):
	left_div_data = ''
	right_div_data = ''
	if div_method == DIV_METHOD.DIV_CPG202:
		left_div_data = div_data[0:4] + div_data[8:16]
		right_div_data = left_div_data
	elif div_method == DIV_METHOD.DIV_CPG212:
		left_div_data = div_data[8:20]
		right_div_data = left_div_data
	else:
		return kmc,kmc,kmc
	dek_key = _gen_dek_key(kmc, left_div_data, right_div_data)
	mac_key = _gen_mac_key(kmc, left_div_data, right_div_data)
	enc_key = _gen_enc_key(kmc, left_div_data, right_div_data)
	return dek_key,mac_key,enc_key

def gen_dek_session_key(kmc,div_method,host_challenge,initialize_update_data):
    dek_session_key,*_ = gen_session_key(kmc,div_method,host_challenge,initialize_update_data)
    return dek_session_key

def gen_mac_session_key(kmc,div_method,host_challenge,initialize_update_data):
    _,mac_session_key,_ = gen_session_key(kmc,div_method,host_challenge,initialize_update_data)
    return mac_session_key

def gen_enc_session_key(kmc,div_method,host_challenge,initialize_update_data):
    *_,enc_session_key = gen_session_key(kmc,div_method,host_challenge,initialize_update_data)
    return enc_session_key

def gen_session_key(kmc,div_method,host_challenge,initialize_update_data):
	dek_session_key = ''
	mac_session_key = ''
	enc_session_key = ''
	div_data = initialize_update_data[0:20]
	key_version = initialize_update_data[20:22]
	scp = initialize_update_data[22:24]
	card_challenge = initialize_update_data[24:40]
	card_cryptogram = initialize_update_data[40:56]
	dek_key,mac_key,enc_key = gen_kmc_sub_key(kmc, div_method, div_data)
	if scp == 1:
		left_div_data = card_challenge[8:16] + host_challenge[0:8]
		right_div_data = card_challenge[0:8] + host_challenge[8:16]
		div_data = left_div_data + right_div_data
		dek_session_key = des.des3_ecb_encrypt(dek_key, div_data)
		mac_session_key = des.des3_ecb_encrypt(mac_key, div_data)
		enc_session_key = des.des3_ecb_encrypt(enc_key, div_data)
	else:	#scp == 2
		seq_no = card_challenge[0:4]
		dek_session_key = _gen_dek_session_key(seq_no, dek_key)
		mac_session_key = _gen_mac_session_key(seq_no, mac_key)
		enc_session_key = _gen_enc_session_key(seq_no, enc_key)
	return dek_session_key,mac_session_key,enc_session_key


def _gen_enc_session_key(seq_no,enc_key):
	left_div_data = '0182' + seq_no + '00000000'
	right_div_data = '0000000000000000'
	return _gen_session_key(enc_key, left_div_data, right_div_data)

def _gen_mac_session_key(seq_no,mac_key):
	left_div_data = '0101' + seq_no + '00000000'
	right_div_data = '0000000000000000'
	return _gen_session_key(mac_key, left_div_data, right_div_data)

def _gen_dek_session_key(seq_no,dek_key):
	left_div_data = '0181' + seq_no + '00000000'
	right_div_data = '0000000000000000'
	return _gen_session_key(dek_key, left_div_data, right_div_data)


def _gen_session_key(key,left_div_data,right_div_data):
	left_key = des.des3_encrypt(key, left_div_data)
	tmp = des.xor(left_key, right_div_data)
	right_key = des.des3_encrypt(key, tmp)
	return left_key + right_key


def _gen_enc_key(kmc,left_div_data_part,right_div_data_part):
	left_div_data = left_div_data_part + 'F001'
	right_div_data = right_div_data_part + '0F01'
	return _gen_kmc_sub_key(kmc, left_div_data, right_div_data)

def _gen_mac_key(kmc,left_div_data_part,right_div_data_part):
	left_div_data = left_div_data_part + 'F002'
	right_div_data = right_div_data_part + '0F02'
	return _gen_kmc_sub_key(kmc, left_div_data, right_div_data)

def _gen_dek_key(kmc,left_div_data_part,right_div_data_part):
	left_div_data = left_div_data_part + 'F003'
	right_div_data = right_div_data_part + '0F03'
	return _gen_kmc_sub_key(kmc, left_div_data, right_div_data)

def _gen_kmc_sub_key(kmc,left_div_data,right_div_data):
	left_key = des.des3_encrypt(kmc, left_div_data)
	right_key = des.des3_encrypt(kmc, right_div_data)
	return left_key + right_key