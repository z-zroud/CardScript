from perso_lib.xml_parse import XmlParser
from perso_lib import utils
from perso_lib import data_parse
from perso_lib.cps import Dgi,Cps
from perso_lib.rule_file import RuleFile
from perso_lib.rule import Rule

def _parse_tlv(dgi_name,data):
    dgi = Dgi()
    data = data_parse.remove_dgi(data,dgi_name)
    int_dgi = utils.str_to_int(dgi_name)
    if int_dgi < 0x0B01:
        if data[0:2] != '70':
            print('数据有误，小于0B01的DGI应包含70模板')
            return None
        data = data_parse.remove_template70(data)
    if not data_parse.is_rsa(dgi_name) and data_parse.is_tlv(data):
        tlvs = data_parse.parse_tlv(data)
        if len(tlvs) > 0 and tlvs[0].is_template is True:
            value = dgi.assemble_tlv(tlvs[0].tag,tlvs[0].value)
            dgi.add_tag_value(dgi_name,value)
        else:
            for tlv in tlvs:
                value = dgi.assemble_tlv(tlv.tag,tlv.value)
                dgi.add_tag_value(tlv.tag,value)
    else:
        dgi.add_tag_value(dgi_name,data)
    return dgi

def _process_pse_and_ppse(dgi_name,data):
    dgi = Dgi()
    if dgi_name == 'Store_PSE_1':
        dgi.dgi = 'PSE'
        data = data_parse.remove_dgi(data,'0101')
        data = data_parse.remove_template70(data)
        dgi.add_tag_value('0101',data)
    elif dgi_name == 'Store_PSE_2':
        dgi.dgi = 'PSE'
        data = data_parse.remove_dgi(data,'9102')
        value = dgi.assemble_tlv('A5','880101' + data)
        dgi.add_tag_value('9102',value)
    elif dgi_name == 'Store_PPSE':
        dgi.dgi = 'PPSE'
        # value = dgi.assemble_tlv('BF0C',data)
        # value = dgi.assemble_tlv('A5',value)
        data = data_parse.remove_dgi(data,'9102')
        dgi.add_tag_value('9102',data)
    return dgi

def _pre_process_rule(rule_file_name,cps):
    rule_handle = RuleFile(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_decrypt()   
    return rule.cps

def _process_rule(rule_file_name,cps):    
    rule_handle = RuleFile(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_dgi_map()
    rule.wrap_process_exchange()
    rule.wrap_process_remove_dgi()
    rule.wrap_process_remove_tag()
    return rule.cps



def _process_rsa(cps):
    rsa_dgi_list = ['8201','8202','8203','8204','8205']
    for dgi in cps.dgi_list:
        if dgi.dgi in rsa_dgi_list:
            data = dgi.get_value(dgi.dgi)
            length = utils.str_to_int(data[0:2]) * 2
            data = data[2: 2 + length]
            dgi.modify_value(dgi.dgi,data)
    return cps

def _process_8000_and_8020(cps):
    append_80_and_len_dgi_list = ['8000','8020']
    for dgi in cps.dgi_list:
        if dgi.dgi in append_80_and_len_dgi_list:
            decrypted_data = ''
            data = dgi.get_value(dgi.dgi)
            for cur_pos in range(0,len(data),48):
                decrypted_data += data[cur_pos + 2: cur_pos + 34]
            dgi.modify_value(dgi.dgi,decrypted_data)
    return cps

def _process_8400(cps):
    for dgi in cps.dgi_list:
        if dgi.dgi == '8400':
            decrypted_data = ''
            data = dgi.get_value(dgi.dgi)
            for cur_pos in range(0,len(data),48):
                decrypted_data += data[cur_pos: cur_pos + 32]
            dgi.modify_value(dgi.dgi,decrypted_data)
    return cps   

def process_dp(dp_file,rule_file=None):
    cps_list = []
    xml = XmlParser(dp_file)
    batch_information_header_node = xml.get_first_node(xml.root_element,'batch_information_header')
    dgi_name_list_node = xml.get_first_node(batch_information_header_node,'dgi_name_list')
    dgi_name_list = xml.get_text(dgi_name_list_node)
    dgi_name_list = dgi_name_list.split(',')
    card_data_nodes = xml.get_child_nodes(xml.root_element,'card_data')
    for card_data_node in card_data_nodes:
        cps = Cps()
        cps.dp_file_path = dp_file
        # account_node = xml.get_first_node(card_data_node,'PAN')
        # account = xml.get_text(account_node).replace('F','')
        for dgi_name in dgi_name_list:
            dgi_node = xml.get_first_node(card_data_node,dgi_name)
            dgi_text = xml.get_text(dgi_node)
            if dgi_name == 'AID':
                cps.aid = dgi_text[4:]
                continue
            if dgi_name == 'B001' or dgi_name == 'PAN':
                continue
            elif dgi_name in ('Store_PSE_1','Store_PSE_2','Store_PPSE'):
                dgi = _process_pse_and_ppse(dgi_name,dgi_text)
            else:
                dgi_name = dgi_name[3:] #默认DGI为DGIXXXX形式
                dgi = _parse_tlv(dgi_name,dgi_text)
                dgi.dgi = dgi_name
            cps.add_dgi(dgi)
        if rule_file:
            cps = _pre_process_rule(rule_file,cps)
            cps = _process_rsa(cps)
            cps = _process_8000_and_8020(cps)
            cps = _process_8400(cps)
            cps = _process_rule(rule_file,cps)
        cps_list.append(cps)
    return cps_list
