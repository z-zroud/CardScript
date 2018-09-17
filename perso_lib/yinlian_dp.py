from perso_lib.file_handle import FileHandle
from perso_lib.rule_file import RuleFile
from perso_lib.cps import Cps,Dgi
from perso_lib import data_parse
from perso_lib import utils
from perso_lib.rule import Rule

def get_dgi_list(fh):
    dgi_list = []
    dgi_count = fh.read_int64_reverse(fh.current_offset)
    for i in range(dgi_count):
        dgi_len = fh.read_int_reverse(fh.current_offset)
        dgi = fh.read_str(fh.current_offset,dgi_len)
        dgi_list.append(dgi)
    return dgi_list

def get_next_len(fh):
    next_data_len = fh.read_binary(fh.current_offset,1)
    if next_data_len == '81':
        next_data_len = fh.read_binary(fh.current_offset,1)
    elif next_data_len == '82':
        next_data_len = fh.read_binary(fh.current_offset,2)
    return utils.hex_str_to_int(next_data_len)

def process_pse_and_ppse(fh,dgi_name,has_template):
    dgi = Dgi()
    data = ''
    dgi_mark = fh.read_binary(fh.current_offset,1) #DGI标识
    if dgi_mark != '86':
        return
    next_len = get_next_len(fh)
    if has_template:
        fh.read_binary(fh.current_offset,1) #读取70模板
        next_len = get_next_len(fh)
        data = fh.read_binary(fh.current_offset,next_len)
    else:
        data = fh.read_binary(fh.current_offset,next_len)
    if dgi_name == 'Store_PSE_1':
        dgi.dgi = 'PSE'
        value = dgi.assemble_tlv('0101',data)
        dgi.add_tag_value('0101',value)
    elif dgi_name == 'Store_PSE_2':
        dgi.dgi = 'PSE'
        value = dgi.assemble_tlv('A5','880101' + data)
        dgi.add_tag_value('9102',value)
    elif dgi_name == 'Store_PPSE':
        dgi.dgi = 'PPSE'
        value = dgi.assemble_tlv('BF0C',data)
        value = dgi.assemble_tlv('A5',value)
        dgi.add_tag_value('9102',value)
    else:
        dgi.dgi = 'F001'
        dgi.add_tag_value('F001',data)
    return dgi

def process_rule(rule_file_name,cps):
    rule = Rule(cps)
    rule_file = RuleFile(rule_file_name)
    decrypt_nodes = rule_file.get_nodes(rule_file.root_element,'Decrypt')
    for node in decrypt_nodes:
        decrypt_attrs = rule_file.get_attributes(node)
        rule.process_decrypt(decrypt_attrs['DGI'],decrypt_attrs['DGI'],decrypt_attrs['key'],decrypt_attrs['type'])
    exchange_nodes = rule_file.get_nodes(rule_file.root_element,'Exchange')
    for node in exchange_nodes:
        exchange_attrs = rule_file.get_attributes(node)
        rule.process_exchange(exchange_attrs['srcDGI'],exchange_attrs['exchangedDGI'])
    remove_dgi_nodes = rule_file.get_nodes(rule_file.root_element,'RemoveDGI')
    for node in remove_dgi_nodes:
        attrs = rule_file.get_attributes(node)
        rule.process_remove_dgi(attrs['DGI'])
    remove_tag_nodes = rule_file.get_nodes(rule_file.root_element,'RemoveTag')
    for node in remove_tag_nodes:
        attrs = rule_file.get_attributes(node)
        rule.process_remove_tag(attrs['DGI'],attrs['tag'])
    return rule.cps
    
def process_yinlian_dp(dp_file,rule_file):
    fh = FileHandle(dp_file,'rb+')
    fh.read(fh.current_offset,8596) #reserved
    dgi_list = get_dgi_list(fh)
    file_size = fh.get_file_size()
    cps_list = []
    while fh.current_offset < file_size:
        card_seq = fh.read_int64_reverse(fh.current_offset)
        card_data_total_len = fh.read_int_reverse(fh.current_offset)
        cps = Cps() #存储单个卡片数据
        pse_and_ppse_dgi = ['Store_PSE_1','Store_PSE_2','Store_PPSE','DGIF001']
        for dgi_name in dgi_list:
            dgi = Dgi() #存储单个DGI数据
            if dgi_name in pse_and_ppse_dgi:
                if dgi_name == 'Store_PSE_1':
                    dgi = process_pse_and_ppse(fh,dgi_name,True)
                else:
                    dgi = process_pse_and_ppse(fh,dgi_name,False)
                cps.add_dgi(dgi)
                continue           
            dgi_mark = fh.read_binary(fh.current_offset,1) #DGI标识
            if dgi_mark != '86':
                return
            next_len = get_next_len(fh)
            dgi_seq = fh.read_binary(fh.current_offset,2) #读取DGI序号
            dgi.dgi = dgi_seq
            next_len = get_next_len(fh)
            n_dgi_seq = utils.hex_str_to_int(dgi_seq)
            print('dgi=' + dgi_seq)
            if n_dgi_seq <= 0x0B00: #认为是记录
                template70 = fh.read_binary(fh.current_offset,1)
                if template70 != '70':
                    return
                next_len = get_next_len(fh)
            dgi_data = fh.read_binary(fh.current_offset,next_len)
            if n_dgi_seq <= 0x0B00 or data_parse.is_tlv(dgi_data):
                tlvs = data_parse.parse_tlv(dgi_data)
                if len(tlvs) > 0 and tlvs[0].is_template is True:
                    value = dgi.assemble_tlv(tlvs[0].tag,tlvs[0].value)
                    dgi.add_tag_value(dgi_seq,value)
                else:
                    for tlv in tlvs:
                        value = dgi.assemble_tlv(tlv.tag,tlv.value)
                        dgi.add_tag_value(tlv.tag,value)
            else:
                dgi.add_tag_value(dgi_seq,dgi_data)
            cps.add_dgi(dgi)
        if rule_file is not None:
            process_rule(rule_file,cps)
        cps_list.append(cps)
    return cps_list

if __name__ == '__main__':
    cps_list = process_yinlian_dp('./test_data/yinlian.dp','./test_data/rule2.xml')
    for cps in cps_list:
        account = cps.get_account()
        path = 'D://' + account + 'txt'
        cps.save(path)