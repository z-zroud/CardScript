from perso_lib.file_handle import FileHandle
from perso_lib.rule_file import RuleFile
from perso_lib.xml_parse import XmlParser
from perso_lib.cps import Cps,Dgi
from perso_lib import data_parse
from perso_lib import utils
from perso_lib.rule import Rule
from perso_lib import des

class GoldpacDgi:
    def __init__(self):
        self.goldpac_dgi = ''
        self.data = ''
        self.data_len = ''

def parse_sddf_element(sddf_tag,value):
    sddf_dgis = []
    count = utils.hex_str_to_int(value[0 : 2])
    temp = value[2:]
    for i in range(count):
        sddf_dgis.append(sddf_tag[0 : 4] + temp[i * 4 : 4 + i * 4])
    return sddf_dgis

def is_need_delete_template(dgi):
    need_remove_prefix = False  #检查是否需要删除DGI及模板数据
    if utils.is_hex_str(dgi):
        if utils.hex_str_to_int(dgi) <= 0x0B01:
            need_remove_prefix = True
    return need_remove_prefix

def get_tag_link_attribute(xml,sddf_tag):
    tag_link_nodes = xml.get_nodes(xml.root_element,'TagLink')
    for node in tag_link_nodes:
        tag = xml.get_attribute(node,'SDDFTag')
        if sddf_tag[0:4] == tag[0:4] and sddf_tag[5:8] == tag[5:8]:
            node_dgi = xml.get_attribute(node,'EMVTag')
            value_format = xml.get_attribute(node,'ValueFormat')
            return node_dgi,value_format
    return ('','')

def get_sddf_tag(xml,emv_tag):
    tag_link_nodes = xml.get_nodes(xml.root_element,'TagLink')
    for node in tag_link_nodes:
        tag = xml.get_attribute(node,'EMVTag')
        if tag == emv_tag:
            return xml.get_attribute(node,'SDDFTag')
    return None

def parse_sddf_data(xml, sddf_tag, goldpac_dgi_list=[]):
    sddf_data = ''
    for item in goldpac_dgi_list:
        if item.goldpac_dgi == sddf_tag:
            sddf_data = item.data
    dgi = Dgi()
    node_dgi,value_format = get_tag_link_attribute(xml,sddf_tag)
    if node_dgi == '' or value_format == '':
        return None
    need_remove_template = is_need_delete_template(node_dgi)
    if sddf_tag[4] == '2':  #说明包含双应用
        dgi.dgi = node_dgi + '_2'
    else:
        dgi.dgi = node_dgi           
    if value_format == 'TLV':
        data = data_parse.remove_dgi(sddf_data,node_dgi)
        if need_remove_template:
            data = data_parse.remove_template70(data)
        tlvs = data_parse.parse_tlv(data)
        for tlv in tlvs:
            if tlv.len > 0x7F:
                value = tlv.tag + '81' + utils.int_to_hex_str(tlv.len) + tlv.value
            else:
                value = tlv.tag + utils.int_to_hex_str(tlv.len) + tlv.value
            dgi.add_tag_value(tlv.tag,value)
    elif value_format == 'V':
        dgi.add_tag_value(dgi,sddf_data)
    return dgi

def get_rsa_dgi_len(data):
    data_len = 0
    if data[0:2] == '82':
        data_len = 2 * utils.hex_str_to_int(data[2:6])
        data = data[6:]
    elif data[0:2] == '81':
        data_len = 2 * utils.hex_str_to_int(data[2:4])
        data = data[4:]
    else:
        data_len = 2 * utils.hex_str_to_int(data[0:2])
        data = data[2:]
    return data_len,data

def get_rsa_dgi_value(data, dgi_len):
    if dgi_len > 1 and data[0:2] == '00':
        return data[2:dgi_len]
    else:
        return data[0:dgi_len]

def split_rsa(xml,goldpac_dgi_list,is_second_app):
    rule_file_handle = RuleFile(xml)
    _,key = rule_file_handle.get_decrypted_attribute('RSA')
    _,sddf_tag,_ = rule_file_handle.get_tag_link_attribute('EMVTag','RSA')
    if is_second_app:
        sddf_tag = sddf_tag[0:4] + '2' + sddf_tag[5:8]
    else:
        sddf_tag = sddf_tag[0:4] + '1' + sddf_tag[5:8]
    encrypted_data = get_goldpac_data(goldpac_dgi_list,sddf_tag,is_second_app)
    decrypted_data = des.des3_ecb_decrypt(key,encrypted_data)
    if len(decrypted_data) <= 2 or decrypted_data[0:2] != '30':
        return None
    decrypted_data = decrypted_data[2:]
    _,decrypted_data = get_rsa_dgi_len(decrypted_data)
    dgi_list = []
    for i in range(9):
        decrypted_data = decrypted_data[2:] #remove flag '02'
        dgi_len,decrypted_data = get_rsa_dgi_len(decrypted_data)
        dgi_data = get_rsa_dgi_value(decrypted_data,dgi_len)
        decrypted_data = decrypted_data[dgi_len:]
        dgi = Dgi()
        if is_second_app:
            dgi.dgi = '_2'
        if i == 4:           
            dgi.dgi = '8201' + dgi.dgi
        elif i == 5:
            dgi.dgi = '8202' + dgi.dgi
        elif i == 6:
            dgi.dgi = '8203' + dgi.dgi
        elif i == 7:
            dgi.dgi = '8204' + dgi.dgi
        elif i == 8:
            dgi.dgi = '8205' + dgi.dgi          
        else:
            continue
        dgi.add_tag_value(dgi.dgi[0:4],dgi_data)
        dgi_list.append(dgi)
        print(dgi.dgi[0:4] + '=' + dgi_data)
    return dgi_list
        
#sddf_tag不需要区分是否为第二应用
def get_goldpac_data(goldpac_dgi_list,sddf_tag,is_second_app):
    for item in goldpac_dgi_list:      
        if is_second_app:
            sddf_dgi = sddf_tag[0:4] + '2' + sddf_tag[5:8]
        else:
            sddf_dgi = sddf_tag[0:4] + '1' + sddf_tag[5:8]
        if item.goldpac_dgi == sddf_dgi:
            return item.data
    return None

def parse_8000(xml,goldpac_dgi_list,is_second_app):
    sddf_8000_mac = get_sddf_tag(xml,'8000_MAC')
    sddf_8000_ac = get_sddf_tag(xml,'8000_AC')
    sddf_8000_enc = get_sddf_tag(xml,'8000_ENC')
    dgi = Dgi()
    if is_second_app:
        dgi.dgi = '8000_2'
    else:
        dgi.dgi = '8000'
    data = get_goldpac_data(goldpac_dgi_list,sddf_8000_ac,is_second_app)
    data += get_goldpac_data(goldpac_dgi_list,sddf_8000_mac,is_second_app)
    data += get_goldpac_data(goldpac_dgi_list,sddf_8000_enc,is_second_app)
    rule_file_handle = RuleFile(xml)
    _,key = rule_file_handle.get_decrypted_attribute('8000')    #顺带解密
    data = des.des3_ecb_decrypt(key,data)
    dgi.add_tag_value(dgi.dgi,data)
    return dgi


def parse_9000(xml,goldpac_dgi_list,is_second_app):
    sddf_9000_mac = get_sddf_tag(xml,'9000_MAC')
    sddf_9000_ac = get_sddf_tag(xml,'9000_AC')
    sddf_9000_enc = get_sddf_tag(xml,'9000_ENC')
    dgi = Dgi()
    if is_second_app:
        dgi.dgi = '9000_2'
    else:
        dgi.dgi = '9000'
    data = get_goldpac_data(goldpac_dgi_list,sddf_9000_ac,is_second_app)[0:6]
    data += get_goldpac_data(goldpac_dgi_list,sddf_9000_mac,is_second_app)[0:6]
    data += get_goldpac_data(goldpac_dgi_list,sddf_9000_enc,is_second_app)[0:6]
    dgi.add_tag_value(dgi.dgi,data)
    return dgi

def parse_pse_and_ppse(xml,goldpac_dgi_list):
    rule_file_handle = RuleFile(xml)
    _,sddf_tag_9102,_ = rule_file_handle.get_tag_link_attribute('EMVDataName','ADF1')
    _,sddf_tag_0101,_ = rule_file_handle.get_tag_link_attribute('EMVDataName','ADF2')
    _,sddf_tag_ppse,_ = rule_file_handle.get_tag_link_attribute('EMVDataName','ppse')
    dgi_pse = Dgi()
    dgi_ppse = Dgi()
    dgi_pse.dgi = 'PSE'
    sddf_tag_9102 = sddf_tag_9102[0:4] + '1' + sddf_tag_9102[5:8]
    sddf_tag_0101 = sddf_tag_0101[0:4] + '1' + sddf_tag_0101[5:8]       
    data_9102 = get_goldpac_data(goldpac_dgi_list,sddf_tag_9102,False)
    data_0101 = get_goldpac_data(goldpac_dgi_list,sddf_tag_0101,False)   
    dgi_pse.add_tag_value('9102',data_9102)
    dgi_pse.add_tag_value('0101',data_0101)
    
    if sddf_tag_ppse is not None:   #纯接触卡，不需要PPSE
        dgi_ppse.dgi = 'PPSE'
        sddf_tag_ppse = sddf_tag_ppse[0:4] + '1' + sddf_tag_ppse[5:8]
        data_ppse = get_goldpac_data(goldpac_dgi_list,sddf_tag_ppse,False)
        dgi_ppse.add_tag_value('9102',data_ppse)
    else:
        dgi_ppse = None

    return dgi_pse,dgi_ppse
   
#返回处理后的文件列表
def process_goldpac_dp(dp_file,rule_file):
    fh = FileHandle(dp_file,'rb+')
    dp_header = fh.read_binary(fh.current_offset, 26)
    dgi_count = fh.read_int(fh.current_offset)
    goldpac_dgi_list = []
    for i in range(dgi_count):  #获取sddf dgi个数及所包含数据的长度
        item = GoldpacDgi()
        item.goldpac_dgi = fh.read_binary(fh.current_offset,4)
        item.data_len = fh.read_int(fh.current_offset)
        goldpac_dgi_list.append(item)
    for item in goldpac_dgi_list:   #获取sddf dgi所包含的数据
        item.data = fh.read_binary(fh.current_offset,item.data_len)
    xml = XmlParser(rule_file)
    sddf_dgi_list = []
    sddf_element_nodes = xml.get_nodes(xml.root_element,'SDDFElement')
    has_second_app = False
    if len(sddf_element_nodes) >= 2:
        has_second_app = True
    for node in sddf_element_nodes:     
        sddf_tag = xml.get_attribute(node,'SDDFTag')
        sddf_value = xml.get_attribute(node,'Value')
        sddf_elements = parse_sddf_element(sddf_tag,sddf_value)
        sddf_dgi_list.extend(sddf_elements)   
    cps = Cps()
    for item in goldpac_dgi_list:
        print(item.goldpac_dgi + ":" + item.data)
    for sddf_tag in sddf_dgi_list:   #解析TagLink节点，并生成cps数据
        cps_dgi = parse_sddf_data(xml,sddf_tag,goldpac_dgi_list)
        if cps_dgi != None:
            cps.add_dgi(cps_dgi)
    cps.add_dgi(parse_8000(xml,goldpac_dgi_list,False))
    cps.add_dgi(parse_9000(xml,goldpac_dgi_list,False))
    rsa_dgi_list = split_rsa(xml,goldpac_dgi_list,False)
    for rsa_dgi in rsa_dgi_list:
        cps.add_dgi(rsa_dgi)
    dgi_pse,dgi_ppse = parse_pse_and_ppse(xml,goldpac_dgi_list)
    cps.add_dgi(dgi_pse)
    if dgi_ppse is not None:
        cps.add_dgi(dgi_ppse)
    if has_second_app:
        cps.add_dgi(parse_8000(xml,goldpac_dgi_list,True))
        cps.add_dgi(parse_9000(xml,goldpac_dgi_list,True))
        rsa_dgi_list = split_rsa(xml,goldpac_dgi_list,True)
        for rsa_dgi in rsa_dgi_list:
            cps.add_dgi(rsa_dgi)
    cps.save('D:\\goldpac.txt')
        



if __name__ == '__main__':
    process_goldpac_dp('goldpac.dp','金邦达测试.xml')
    