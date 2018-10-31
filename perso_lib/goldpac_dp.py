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

_aid_list_info = dict()

def get_pse_and_ppse_dgi_list(sddf_dgi_list):
    global _aid_list_info
    pse_dgi_list = []
    ppse_dgi_list = []
    pse_index,_ = _aid_list_info['315041592E5359532E4444463031']
    ppse_index,_ = _aid_list_info['325041592E5359532E4444463031']
    for dgi in sddf_dgi_list:
        if dgi[4] == pse_index:
            pse_dgi_list.append(dgi)
        elif dgi[4] == ppse_index:
            ppse_dgi_list.append(dgi)
    return pse_dgi_list,ppse_dgi_list


def has_second_app():
    """
    判断是否为双应用数据
    """
    global _aid_list_info
    count = 0
    if '325041592E5359532E4444463031' in _aid_list_info.keys():
        count += 1
    if '315041592E5359532E4444463031' in _aid_list_info.keys():
        count += 1
    if len(_aid_list_info) > count + 1:
        return True
    return False

def get_second_app_index():
    global _aid_list_info
    for _,aid_info in _aid_list_info.items():
        if aid_info[1] == True:
            return aid_info[0]
    return '-1' #没有找到第二应用索引

def get_first_app_index():
    global _aid_list_info
    for aid,aid_info in _aid_list_info.items():
        if aid_info[1] is False and aid != '325041592E5359532E4444463031' and aid != '315041592E5359532E4444463031':
            return aid_info[0]
    return '-1'

def parse_sddf_element(sddf_tag,value):
    """
    分析SDDFElement节点中Value所组成的金邦达DGI
    并返回金邦达DGI
    """
    sddf_dgis = []
    count = utils.hex_str_to_int(value[0 : 2])
    temp = value[2:]
    for i in range(count):
        sddf_dgis.append(sddf_tag[0 : 4] + temp[i * 4 : 4 + i * 4])
    return sddf_dgis

def is_need_delete_template(dgi):
    """
    通过DGI值判断数据中是否包含有模板信息
    """
    need_remove_prefix = False  #检查是否需要删除DGI及模板数据
    if utils.is_hex_str(dgi):
        if utils.hex_str_to_int(dgi) <= 0x0B01:
            need_remove_prefix = True
    return need_remove_prefix

def get_tag_link_attribute(xml,sddf_tag):
    """
    根据SDDF_Tag获取对应的TagLink节点
    获取金邦达DGI的TagLink节点属性，并返回
    对应的标准DGI分组和数据格式(TLV或者V)
    """
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

def get_aid_list_info(xml):
    """
    获取AID节点列表，并返回Aid=(Index,is_second_app)字典集合
    """
    global _aid_list_info
    aid_list_nodes = xml.get_nodes(xml.root_element,'AID')
    app_count = 0
    for node in aid_list_nodes:
        aid = xml.get_attribute(node,'Name')
        index = xml.get_attribute(node,'Index')
        if aid != '325041592E5359532E4444463031' and aid != '315041592E5359532E4444463031':
            app_count += 1
        if app_count > 1:
            _aid_list_info[aid] = (index,True)
            app_count -= 1  #防止将PSE,PPSE当作第二应用
        else:
            _aid_list_info[aid] = (index,False)
    return _aid_list_info

def process_jetco_special_dgi(xml,goldpac_dgi_list,cps):
    rule_file_handle = RuleFile(xml.file_name)
    add_tag_nodes = xml.get_nodes(xml.root_element,'AddTag')
    for node in add_tag_nodes:
        attrs = xml.get_attributes(node)
        dgi = Dgi()
        dgi.dgi = attrs['srcDGI']
        if 'srcTag' not in attrs:
            attrs['srcTag'] = attrs['dstTag']
        data = ''
        if attrs['dstDGI'] == 'DF20':
            _,sddf_tag_DF18,_ = rule_file_handle.get_tag_link_attribute('EMVTag','DF18')
            _,sddf_tag_DF19,_ = rule_file_handle.get_tag_link_attribute('EMVTag','DF19')
            data_DF18 = get_goldpac_data(goldpac_dgi_list,sddf_tag_DF18,True)
            data_DF19 = get_goldpac_data(goldpac_dgi_list,sddf_tag_DF19,True)
            data = data_DF18 + data_DF19
            data = data[0:data.find('20')]
            data = utils.bcd_to_str(data)
            if len(data) // 2 > 0x7F:
                data = attrs['dstDGI'] + '81' + utils.get_strlen(data) + data
            else:
                data = attrs['dstDGI'] + utils.get_strlen(data) + data
        elif attrs['dstDGI'] == 'DF27':
            _,sddf_tag_DF25,_ = rule_file_handle.get_tag_link_attribute('EMVTag','DF25')
            _,sddf_tag_DF26,_ = rule_file_handle.get_tag_link_attribute('EMVTag','DF26')
            data_DF25 = get_goldpac_data(goldpac_dgi_list,sddf_tag_DF25,True)
            data_DF26 = get_goldpac_data(goldpac_dgi_list,sddf_tag_DF26,True)
            data = data_DF25 + data_DF26 
        else:
            _,sddf_tag,_ = rule_file_handle.get_tag_link_attribute('EMVTag',attrs['dstTag'])
            data = get_goldpac_data(goldpac_dgi_list,sddf_tag,True)
        dgi.add_tag_value(attrs['srcTag'],data)
        cps.add_dgi(dgi)
    return cps

def parse_pse_and_ppse_data(xml,sddf_tag,goldpac_dgi_list):
    sddf_data = ''
    node_dgi,value_format = get_tag_link_attribute(xml,sddf_tag) 
    if node_dgi == '' or value_format == '':
        return None
    for item in goldpac_dgi_list:
        if item.goldpac_dgi == sddf_tag:
            sddf_data = item.data
    data = data_parse.remove_dgi(sddf_data,node_dgi)
    need_remove_template = is_need_delete_template(node_dgi)
    if need_remove_template:
        data = data_parse.remove_template70(data)
    return node_dgi,data

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
    global _aid_list_info
    is_second_app = False
    for _,aid_info in _aid_list_info.items():
        if sddf_tag[4] == aid_info[0]:
            is_second_app = aid_info[1]
            break
    if is_second_app:  #说明包含双应用
        dgi.dgi = node_dgi + '_2'
    else:
        dgi.dgi = node_dgi           
    if value_format == 'TLV':
        data = data_parse.remove_dgi(sddf_data,node_dgi)
        if need_remove_template:
            data = data_parse.remove_template70(data)
        tlvs = data_parse.parse_tlv(data)
        if len(tlvs) > 0 and tlvs[0].is_template is True:
            value = dgi.assemble_tlv(tlvs[0].tag,tlvs[0].value)
            dgi.add_tag_value(dgi.dgi,value)
        else:
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
    rule_file_handle = RuleFile(xml.file_name)
    _,key = rule_file_handle.get_decrypted_attribute('RSA')
    _,sddf_tag,_ = rule_file_handle.get_tag_link_attribute('EMVTag','DF70')
    if is_second_app:
        sddf_tag = sddf_tag[0:4] + get_second_app_index() + sddf_tag[5:8]
    else:
        sddf_tag = sddf_tag[0:4] + get_first_app_index() + sddf_tag[5:8]
    encrypted_data = get_goldpac_data(goldpac_dgi_list,sddf_tag,is_second_app)
    decrypted_data = des.des3_ecb_decrypt(key,encrypted_data)
    if len(decrypted_data) <= 2 or decrypted_data[0:2] != '30':
        print('RSA解密失败')
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
            dgi.dgi = '8205' + dgi.dgi
        elif i == 5:
            dgi.dgi = '8204' + dgi.dgi
        elif i == 6:
            dgi.dgi = '8203' + dgi.dgi
        elif i == 7:
            dgi.dgi = '8202' + dgi.dgi
        elif i == 8:
            dgi.dgi = '8201' + dgi.dgi          
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
            sddf_dgi = sddf_tag[0:4] + get_second_app_index() + sddf_tag[5:8]
        else:
            sddf_dgi = sddf_tag[0:4] + get_first_app_index() + sddf_tag[5:8]
        if item.goldpac_dgi == sddf_dgi:
            return item.data
    return None

def parse_8000(xml,goldpac_dgi_list,is_second_app):
    sddf_8000_ac = get_sddf_tag(xml,'DF60')
    sddf_8000_mac = get_sddf_tag(xml,'DF62')
    sddf_8000_enc = get_sddf_tag(xml,'DF64')
    dgi = Dgi()
    if is_second_app:
        dgi.dgi = '8000_2'
    else:
        dgi.dgi = '8000'
    data = get_goldpac_data(goldpac_dgi_list,sddf_8000_ac,is_second_app)
    data += get_goldpac_data(goldpac_dgi_list,sddf_8000_mac,is_second_app)
    data += get_goldpac_data(goldpac_dgi_list,sddf_8000_enc,is_second_app)
    rule_file_handle = RuleFile(xml.file_name)
    _,key = rule_file_handle.get_decrypted_attribute('8000')    #顺带解密
    data = des.des3_ecb_decrypt(key,data)
    dgi.add_tag_value(dgi.dgi,data)
    return dgi

def parse_9000(xml,goldpac_dgi_list,is_second_app):
    sddf_9000_ac = get_sddf_tag(xml,'DF61')
    sddf_9000_mac = get_sddf_tag(xml,'DF63')
    sddf_9000_enc = get_sddf_tag(xml,'DF65')
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

def parse_pse_and_ppse(xml,pse_dgi_list,ppse_dgi_list,goldpac_dgi_list):
    pse_dgi = Dgi()
    pse_dgi.dgi = 'PSE'
    ppse_dgi = Dgi()
    ppse_dgi.dgi = 'PPSE'
    for sddf_tag in pse_dgi_list:
        tag,value = parse_pse_and_ppse_data(xml,sddf_tag,goldpac_dgi_list)
        pse_dgi.add_tag_value(tag,value)
    for sddf_tag in ppse_dgi_list:
        tag,value = parse_pse_and_ppse_data(xml,sddf_tag,goldpac_dgi_list)
        ppse_dgi.add_tag_value(tag,value)
    return pse_dgi,ppse_dgi
   
#返回处理后的文件列表
def process_dp(dp_file,rule_file):
    cps_list = []
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
        print(item.goldpac_dgi + ' = ' + item.data)
    xml = XmlParser(rule_file)
    get_aid_list_info(xml)  #获取AID应用列表信息
    sddf_dgi_list = []
    sddf_element_nodes = xml.get_nodes(xml.root_element,'SDDFElement')
    constans_second_app = has_second_app()
    for node in sddf_element_nodes:     
        sddf_tag = xml.get_attribute(node,'SDDFTag')
        sddf_value = xml.get_attribute(node,'Value')
        sddf_elements = parse_sddf_element(sddf_tag,sddf_value)
        sddf_dgi_list.extend(sddf_elements)   
    cps = Cps()
    cps.dp_file_path = dp_file
    pse_dgi_list,ppse_dgi_list = get_pse_and_ppse_dgi_list(sddf_dgi_list)
    for sddf_tag in sddf_dgi_list:
        if sddf_tag not in pse_dgi_list and sddf_tag not in ppse_dgi_list:   #解析TagLink节点，并生成cps数据
            cps_dgi = parse_sddf_data(xml,sddf_tag,goldpac_dgi_list)
            if cps_dgi != None:
                cps.add_dgi(cps_dgi)
    cps.add_dgi(parse_8000(xml,goldpac_dgi_list,False))
    cps.add_dgi(parse_9000(xml,goldpac_dgi_list,False))
    rsa_dgi_list = split_rsa(xml,goldpac_dgi_list,False)
    for rsa_dgi in rsa_dgi_list:
        cps.add_dgi(rsa_dgi)
    pse_dgi,ppse_dgi = parse_pse_and_ppse(xml,pse_dgi_list,ppse_dgi_list,goldpac_dgi_list)
    cps.add_dgi(pse_dgi)
    if ppse_dgi is not None:
        cps.add_dgi(ppse_dgi)
    if constans_second_app:
        cps = process_jetco_special_dgi(xml,goldpac_dgi_list,cps)
        cps.add_dgi(parse_8000(xml,goldpac_dgi_list,True))
        cps.add_dgi(parse_9000(xml,goldpac_dgi_list,True))
        rsa_dgi_list = split_rsa(xml,goldpac_dgi_list,True)
        for rsa_dgi in rsa_dgi_list:
            cps.add_dgi(rsa_dgi)
    cps_list.append(cps)
    return cps_list
        



if __name__ == '__main__':
    process_dp('goldpac.dp','金邦达测试.xml')
    