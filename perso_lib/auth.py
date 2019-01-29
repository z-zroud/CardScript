import sys
from perso_lib import apdu
from perso_lib.gen_kmc_session import DIV_METHOD,SECURE_LEVEL

def open_secure_channel(kmc,div_method=DIV_METHOD.NO_DIV,secure_level=SECURE_LEVEL.SL_NO_SECURE):
    host_challenge = '1122334455667788'
    resp = apdu.init_update(host_challenge)
    if resp.sw != 0x9000:
        sys.exit()
    dek_session_key,resp = apdu.ext_auth(kmc,div_method,secure_level,host_challenge,resp.response)
    if(resp.sw != 0x9000):
        sys.exit(1)
    return dek_session_key

# def modify_kmc(old_kmc,old_div_method,new_kmc,new_div_method):
#     auth_key = ''
#     mac_key = ''
#     enc_key = ''
#     div_key_left = ''
#     div_key_right = ''
#     if div_method == DIV_METHOD.NO_DIV:
#         auth_key = new_kmc
#         mac_key = new_kmc
#         enc_key = new_kmc
#     elif div_method == DIV_METHOD.DIV_CPG202:
        


