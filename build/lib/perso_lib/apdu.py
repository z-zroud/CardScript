from perso_lib import pcsc
from perso_lib import utils

# Select Command
def select_aid(instance_id):
    aid_len = utils.get_bcd_len(instance_id)
    cmd = '00A40400' + aid_len + instance_id
    return pcsc.send(cmd) 

def select_file_id(file_id):
    file_id_len = utils.get_bcd_len(file_id)
    cmd = '00A40000' + file_id_len + file_id
    return pcsc.send(cmd)
