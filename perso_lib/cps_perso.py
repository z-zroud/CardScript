#定义通用的个人化函数
from perso_lib.xml_parse import XmlParser
from perso_lib.ini_parse import IniParser
from perso_lib.pcsc import ApduResponse
from perso_lib import apdu
from perso_lib import des
from perso_lib import utils
from perso_lib.cps import Cps,Dgi

def _process_encrypted_data(dgi,data,key,config):
    xml = XmlParser(config)
    encrypted_nodes = xml.get_nodes(xml.root_element,'Encrypt')
    for encrypted_node in encrypted_nodes:
        attr = xml.get_attribute(encrypted_node,'DGI')
        if dgi == attr:
            padding80 = xml.get_attribute(encrypted_node,'padding80')
            if padding80 == 'true':
                data += '80'
                zero_count = len(data) % 16
                data += '0' * (16 - zero_count)
            return True, des.des3_ecb_encrypt(key,data)
    return False, data

def _process_template_and_dgi(dgi,data):
    int_dgi = utils.hex_str_to_int(dgi)
    if int_dgi <= 0x0B01:
        data_len = len(data)
        if data_len >= 0xFF * 2:
            data = '7082' + utils.get_strlen(data) + data
        elif data_len > 0x80 * 2:
            data = '7081' + utils.get_strlen(data) + data
        else:
            data = '70' + utils.get_strlen(data) + data
    # if dgi == '0201':
    #     dgi += 'FF00'
    data = dgi + utils.get_strlen(data) + data
    return data

def _assemble_options(ini,section):
    data = ''
    options = ini.get_options(section)
    for option in options:
        value = ini.get_value(section,option)
        data += value
    return data

def perso_no_cps_format(cps_file,config,session_key):
    '''
    个人化完整的数据，无需自己解析TLV及添加模板
    '''
    if len(cps_file) == 0 or len(config) == 0:
        return False
    ini = IniParser(cps_file)
    sections = ini.get_sections()
    section_count = len(sections)
    count = 0
    for section in sections:
        if section in ('PSE','PPSE'):
            continue
        resp = ApduResponse()
        count += 1
        data_type = '00'
        reset = True if count == 1 else False
        data = ini.get_first_option_value(section)
        is_encrypted_data, data = _process_encrypted_data(section,data,session_key,config)
        data = _process_template_and_dgi(section,data)
        if is_encrypted_data:
            data_type = '60'
        if count == section_count:
            data_type = '80'
        data_len = len(data)
        max_len = 0xFF * 2
        if data_len > max_len:
            block_count = data_len // max_len + 1
            for i in range(block_count):
                if i != 0:
                    reset = False
                data_block = data[i * max_len : (i + 1) * max_len]
                resp = apdu.store_data(data_block,data_type,reset)
        else:
            resp = apdu.store_data(data,data_type,reset)
        if resp.sw != 0x9000:
            return False
    return True

def perso_pse_mem(pse_dgi):
    data_list = []
    for key,value in pse_dgi.tag_value_dict.items():
        data = _process_template_and_dgi(key,value)
        data_list.append(data)
    count = 0
    data_count = len(data_list)
    for data in data_list:
        resp = ApduResponse()
        count += 1
        data_type = '00'
        reset = True if count == 1 else False
        if count == data_count:
            data_type = '80'
        resp = apdu.store_data(data,data_type,reset)
        if resp.sw != 0x9000:
            return False
    return True

def perso_ppse_mem(ppse_dgi):
    return perso_pse_mem(ppse_dgi)

def perso_cps_mem(dgi_list,config_file,session_key):
    '''个人化缓存中的数据'''
    count = 0
    dgi_count = len(dgi_list)
    for dgi in dgi_list:
        data = ''
        for _,value in dgi.tag_value_dict.items():
            data += value
        is_encrypted_data, data = _process_encrypted_data(dgi.dgi,data,session_key,config_file)
        data = _process_template_and_dgi(dgi.dgi,data)
        resp = ApduResponse()
        count += 1
        reset = True if count == 1 else False
        data_type = '00'
        if is_encrypted_data:
            data_type = '60'
        if count == dgi_count:
            data_type = '80'
        data_len = len(data)
        max_len = 0xFF * 2
        if data_len > max_len:
            block_count = data_len // max_len + 1
            for i in range(block_count):
                if i != 0:
                    reset = False
                data_block = data[i * max_len : (i + 1) * max_len]
                resp = apdu.store_data(data_block,data_type,reset)
        else:
            resp = apdu.store_data(data,data_type,reset)
        if resp.sw != 0x9000:
            return False
    return True

def get_cps(cps_file):
    cps = Cps()
    ini = IniParser(cps_file)
    sections = ini.get_sections()
    for section in sections:
        dgi = Dgi()
        dgi.dgi = section
        options = ini.get_options(section)
        for option in options:
            value = ini.get_value(section,option)
            dgi.add_tag_value(option,value)
        cps.add_dgi(dgi)
    return cps

def perso_pse(cps_file):
    cps = get_cps(cps_file)
    perso_pse_mem(cps.get_dgi('PSE'))

def perso_ppse(cps_file):
    cps = get_cps(cps_file)
    perso_ppse_mem(cps.get_dgi('PPSE'))

def perso_cps(cps_file,config,session_key):
    '''个人化标准的CPS格式数据'''
    if len(cps_file) == 0 or len(config) == 0:
        return False
    ini = IniParser(cps_file)
    sections = ini.get_sections()
    section_count = len(sections)
    count = 0
    for section in sections:
        if section in ('PSE','PPSE'):
            continue
        resp = ApduResponse()
        count += 1
        data_type = '00'
        reset = True if count == 1 else False
        data = _assemble_options(ini,section)
        is_encrypted_data, data = _process_encrypted_data(section,data,session_key,config)
        data = _process_template_and_dgi(section,data)
        if is_encrypted_data:
            data_type = '60'
        if count == section_count:
            data_type = '80'
        data_len = len(data)
        max_len = 0xFF * 2
        if data_len > max_len:
            block_count = data_len // max_len + 1
            for i in range(block_count):
                if i != 0:
                    reset = False
                data_block = data[i * max_len : (i + 1) * max_len]
                resp = apdu.store_data(data_block,data_type,reset)
        else:
            resp = apdu.store_data(data,data_type,reset)
        if resp.sw != 0x9000:
            return False
    return True