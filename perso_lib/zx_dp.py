from perso_lib.file_handle import FileHandle
from perso_lib.rule_file import RuleFile
from perso_lib.cps import Cps,Dgi
from perso_lib import data_parse
from perso_lib import utils
from perso_lib.rule import Rule

def get_len(fh):
    data_len = 0
    data_str_len = fh.read_binary(fh.current_offset,1)
    if data_str_len == '82':
        data_len = utils.hex_str_to_int(fh.read_binary(fh.current_offset,2))
    elif data_str_len == '81':
        data_len = utils.hex_str_to_int(fh.read_binary(fh.current_offset,1))
    else:
        data_len = utils.hex_str_to_int(data_str_len)
    return data_len

def process_pse_and_ppse(dgi_name,dgi_data,dgi_node):
    dgi = Dgi()
    dgi.dgi = dgi_node
    if dgi_name == '9102':
        index = dgi_data.find('A5')
        dgi_data = dgi_data[index : len(dgi_data)]
        dgi.add_tag_value(dgi_name,dgi_data)
    else:
        dgi.add_tag_value(dgi_name,dgi_data)
    return dgi

def process_rule(rule_file_name,cps):   
    rule_handle = RuleFile(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_decrypt()
    rule.wrap_process_add_fixed_tag()
    rule.wrap_process_remove_dgi()
    rule.wrap_process_remove_tag()
    return rule.cps

def process_zx_dp(dp_file,rule_file):
    cps_list = []
    fh = FileHandle(dp_file,'rb+')
    dp_flag = fh.read_binary(fh.current_offset,7)
    data_len = utils.hex_str_to_int(fh.read_binary(fh.current_offset,8))
    dgi_count = fh.read_int64(fh.current_offset)
    dgi_list = []
    for i in range(dgi_count):
        dgi_name_len = fh.read_int(fh.current_offset)
        dgi_name = fh.read_str(fh.current_offset,dgi_name_len)
        dgi_list.append(dgi_name)
    card_seq = fh.read_binary(fh.current_offset,4)
    card_data_len = fh.read_int(fh.current_offset)
    while data_len > fh.current_offset:
        cps = Cps()
        cps.dp_file_path = dp_file
        for item in dgi_list:
            dgi = Dgi()
            start_flag = fh.read_binary(fh.current_offset,1)
            if start_flag != '86':
                return cps_list
            dgi_len = get_len(fh)
            dgi_name = fh.read_binary(fh.current_offset,2)
            dgi.dgi = dgi_name
            dgi_data_len = utils.hex_str_to_int(fh.read_binary(fh.current_offset,1))
            n_dgi_seq = utils.hex_str_to_int(dgi_name)
            if n_dgi_seq <= 0x0B00: #认为是记录
                template70 = fh.read_binary(fh.current_offset,1)
                if template70 != '70':
                    return cps_list
                dgi_data_len = get_len(fh)
            dgi_data = fh.read_binary(fh.current_offset,dgi_data_len)
            if item[0:3] == 'PSE':
                dgi = process_pse_and_ppse(dgi_name,dgi_data,'PSE')
            elif item[0:4] == 'PPSE':
                dgi = process_pse_and_ppse(dgi_name,dgi_data,'PPSE')
            else:
                if n_dgi_seq <= 0x0B00 or (data_parse.is_rsa(dgi_name) is False and data_parse.is_tlv(dgi_data)):
                    tlvs = data_parse.parse_tlv(dgi_data)
                    if len(tlvs) > 0 and tlvs[0].is_template is True:
                        value = dgi.assemble_tlv(tlvs[0].tag,tlvs[0].value)
                        dgi.add_tag_value(dgi_name,value)
                    else:
                        for tlv in tlvs:
                            value = dgi.assemble_tlv(tlv.tag,tlv.value)
                            dgi.add_tag_value(tlv.tag,value)
                else:
                    dgi.add_tag_value(dgi_name,dgi_data)
            cps.add_dgi(dgi)
        if rule_file is not None:
            process_rule(rule_file,cps)
        cps_list.append(cps)
    return cps_list