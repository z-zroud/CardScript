from perso_lib.file_handle import FileHandle
from perso_lib.cps import Cps,Dgi
from perso_lib import utils
from perso_lib.rule import Rule,RuleXml
from perso_lib import algorithm
import os

def move_to_flag(fh,flag):   
    bcd_flag = utils.str_to_bcd(flag)
    flag_len = len(bcd_flag)
    index = 0
    while True:
        bcd = fh.read_binary(fh.current_offset,1)
        if bcd_flag[index : index + 2] == bcd:
            index += 2
        else:
            index = 0
        if index == flag_len:
            return
    return

def process_prn_data(fh):
    prn_data_len = fh.read_int64(fh.current_offset)
    fh.read_binary(fh.current_offset,prn_data_len) #暂时无需不对数据做处理
    return True

def process_mag_data(fh,rule_file_name):
    rule_file = RuleXml(rule_file_name)
    mag_node = rule_file.get_first_node(rule_file.root_element,'Magstrip')
    
    mag_flag = fh.read_str(fh.current_offset,6)
    if mag_flag != '000MAG':
        return False
    mag_data_len = fh.read_int64(fh.current_offset)
    track_flag_list = []
    track_flag_list.append(fh.read(fh.current_offset,1))
    track_flag_list.append(fh.read(fh.current_offset + 1,1))
    track_flag_list.append(fh.read(fh.current_offset + 1,1))
    mag_data = fh.read_binary(fh.current_offset,mag_data_len - 5)
    mag_data_list = [x for x in mag_data.split('7C') if len(x) > 0]
    print('decrypt mag data: ',end='')
    print(mag_data_list)
    dgi = Dgi()
    dgi.dgi = 'Magstrip'
    if mag_node is not None:
        mag_key = rule_file.get_attribute(mag_node,'key')
        decrypt_mag_list = []
        for data in mag_data_list:
            data = utils.bcd_to_str(data)
            data = algorithm.des3_ecb_decrypt(mag_key,data)
            data = utils.bcd_to_str(data)
            data_len = int(data[0:4])
            data = data[4:data_len + 4].rstrip()
            decrypt_mag_list.append(data)
        pos = 1
        for mag in decrypt_mag_list:
            for index in range(pos,4):
                pos += 1
                option = 'mag' + str(pos)
                if track_flag_list[index - 1] == '0':
                    dgi.add_tag_value(option,'')
                    continue
                dgi.add_tag_value(option,mag)
                break
        print('decrypt mag data: ',end='')
        print(decrypt_mag_list)
    return dgi

def process_pse(dgi,data):
    pse_dgi = Dgi()
    if dgi == '0098':
        pse_dgi.dgi = '0101'
        pse_dgi.add_tag_value(pse_dgi.dgi,data[4:])
    elif dgi == '0099':
        pse_dgi.dgi = '9102'
        pse_dgi.add_tag_value(pse_dgi.dgi,data)
    return pse_dgi

def process_ppse(dgi,data):
    ppse_dgi = Dgi()
    if dgi == '0100':
        ppse_dgi.dgi = '9102'
        ppse_dgi.add_tag_value(ppse_dgi.dgi,data)
    return ppse_dgi

def process_rule(rule_file_name,cps):
    rule_handle = RuleXml(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_decrypt()
    rule.wrap_process_add_tag() 
    rule.wrap_process_add_fixed_tag()
    rule.wrap_process_dgi_map()
    rule.wrap_process_exchange()
    rule.wrap_process_assemble_dgi()
    rule.wrap_process_remove_dgi()
    rule.wrap_process_remove_tag()
    return rule.cps

def process_tag_decrypt(rule_file_name,tag,data):
    rule_file = RuleXml(rule_file_name)
    tag_decrypt_nodes = rule_file.get_nodes(rule_file.root_element,'TagDecrypt')
    for node in tag_decrypt_nodes:
        attrs = rule_file.get_attributes(node)
        if attrs['tag'] == tag:
            data = algorithm.des3_ecb_decrypt(attrs['key'],data)
            if 'startPos' in attrs:
                start_pos = int(attrs['startPos'])
            else:
                start_pos = 0
            if 'len' in attrs:
                data_len = int(attrs['len'])
            else:
                data_len = len(data)
            data = data[start_pos : start_pos + data_len]
            return data
    return data

def get_dgi_list(fh):
    dgi_list_len = fh.read_int(fh.current_offset)
    dgi_list_str = fh.read_binary(fh.current_offset,dgi_list_len)
    dgi_list = []
    for i in range(0,dgi_list_len * 2,4):
        dgi_list.append(dgi_list_str[i : i + 4])
    encrypt_dgi_list_len = fh.read_int(fh.current_offset)
    encrypt_dgi_list_str = fh.read_binary(fh.current_offset,encrypt_dgi_list_len)
    encrypt_dgi_list = []
    for i in range(0,encrypt_dgi_list_len * 2,4):
        encrypt_dgi_list.append(encrypt_dgi_list_str[i : i + 4])
    log_dgi_list_len = fh.read_int(fh.current_offset)
    fh.read_binary(fh.current_offset,log_dgi_list_len) #暂时不需要log DGI记录
    return dgi_list,encrypt_dgi_list
    
def process_card_data(fh,rule_file):
    cps = Cps()
    flag = fh.read_str(fh.current_offset,6)
    if flag != '000EMV':
        return False,cps
    card_data_len = fh.read_int64(fh.current_offset)
    app_count = utils.hex_str_to_int(fh.read_binary(fh.current_offset,1))
    for app in range(app_count):
        aid_len = utils.hex_str_to_int(fh.read_binary(fh.current_offset,1))
        aid = fh.read_binary(fh.current_offset,aid_len)
        app_data_len = fh.read_int64(fh.current_offset)
        dgi_list, encrypt_dgi_list = get_dgi_list(fh)
        print('encrypt dgi list :', encrypt_dgi_list)
        for item in dgi_list:
            card_dgi = Dgi()
            dgi = fh.read_binary(fh.current_offset,2)
            dgi_len = utils.hex_str_to_int(fh.read_binary(fh.current_offset,1))
            dgi_data = fh.read_binary(fh.current_offset,dgi_len)
            n_dgi = utils.hex_str_to_int(dgi)
            card_dgi.dgi = dgi
            if dgi == '0098' or dgi == '0099':
                dgi = process_pse(dgi,dgi_data)
            elif dgi == '0100':
                dgi = process_ppse(dgi,dgi_data)
            else:
                if n_dgi < 0x0B01:
                    if dgi_data[0:2] != '70':
                        return False,cps
                    if dgi_data[2:4] == '81':
                        dgi_data = dgi_data[6:]
                    else:
                        dgi_data = dgi_data[4:]
                if utils.is_rsa(dgi) is False and utils.is_tlv(dgi_data):
                    tlvs = utils.parse_tlv(dgi_data)
                    if len(tlvs) > 0 and tlvs[0].is_template is True:
                        value = card_dgi.assemble_tlv(tlvs[0].tag,tlvs[0].value)
                        card_dgi.add_tag_value(dgi,value)
                    else:
                        for tlv in tlvs:
                            value = process_tag_decrypt(rule_file,tlv.tag,tlv.value)
                            value = card_dgi.assemble_tlv(tlv.tag,value)
                            card_dgi.add_tag_value(tlv.tag,value)
                else:
                    card_dgi.add_tag_value(dgi,dgi_data)
            cps.add_dgi(card_dgi)
    return True,cps

def process_dp(dp_file,rule_file):
    cps_list = []
    fh = FileHandle(dp_file,'rb+')
    move_to_flag(fh,'000PRN')   #直接移到卡片数据位置处理，前面的数据直接忽略
    process_prn_data(fh)
    mag_dgi = process_mag_data(fh,rule_file)
    ret,cps = process_card_data(fh,rule_file)
    if ret is False:
        return None
    cps.dp_file_path = dp_file
    if rule_file is not None:
        cps = process_rule(rule_file,cps)
    if not mag_dgi.is_empty():
        cps.add_dgi(mag_dgi)
    cps_list.append(cps)
    return cps_list
