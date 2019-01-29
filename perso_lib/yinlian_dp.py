from perso_lib.file_handle import FileHandle
from perso_lib.rule_file import RuleFile
from perso_lib.cps import Cps,Dgi
from perso_lib import data_parse
from perso_lib import utils
from perso_lib.rule import Rule
from perso_lib import des
from perso_lib import algorithm

do_not_parse_tlv_list = ['8201','8202','8203','8204','8205','8000','9000','8202','8002','8302']

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
        #value = dgi.assemble_tlv('0101',data)
        dgi.add_tag_value('0101',data)
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
    rule_handle = RuleFile(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_decrypt()
    rule.wrap_process_dgi_map()
    rule.wrap_process_exchange()
    rule.wrap_process_remove_dgi()
    rule.wrap_process_remove_tag()
    return rule.cps

def process_rule_eps(rule_file_name,cps):
    key = '0123456789ABCDEF1111111111111111' #默认解密key
    rule_handle = RuleFile(rule_file_name)
    handle8020_node = rule_handle.get_first_node(rule_handle.root_element,'Handle8020')
    if not handle8020_node:
        return cps
    key = rule_handle.get_attribute(handle8020_node,'key')
    for dgi_item in cps.dgi_list:
        if dgi_item.dgi == '8020':
            tag8020 = ''
            tagA001 = ''
            value = dgi_item.get_value('8020')
            dgi_len = len(value)
            for i in range(0,dgi_len,34):
                tagA001 += value[i:i + 2] + '010000FF0000'
                data = des.des3_ecb_decrypt(key,value[i + 2: i + 34])
                tag8020 += data
            dgi_item.modify_value('8020',tag8020)
            dgiA001 = Dgi()
            dgiA001.dgi = 'A001'
            dgiA001.add_tag_value('A001',tagA001)
            cps.add_dgi(dgiA001)
        if dgi_item.dgi == '9020':
            tag9020 = ''
            value = dgi_item.get_value('9020')
            for i in range(0,len(value),8):
                tag9020 += value[i + 2:i + 8]
            dgi_item.modify_value('9020',tag9020)
    return cps    

def process_rule_A001(rule_file_name,cps):
    key = '0123456789ABCDEF1111111111111111' #默认解密key
    rule_handle = RuleFile(rule_file_name)
    handleA001_node = rule_handle.get_first_node(rule_handle.root_element,'HandleA001')
    if not handleA001_node:
        return cps
    key = rule_handle.get_attribute(handleA001_node,'key')
    for dgi_item in cps.dgi_list:
        if dgi_item.dgi == 'A001':
            tag8020 = ''
            tag9020 = ''
            tagA001 = ''
            value = dgi_item.get_value('A001')
            dgi_len = len(value)
            for i in range(0,dgi_len,34):
                tagA001 += value[i:i + 2] + '010000FF0000'
                data = des.des3_ecb_decrypt(key,value[i + 2: i + 34])
                tag8020 += data
                tag9020 += algorithm.gen_kcv(data)
            dgi_item.modify_value('A001',tagA001)
            dgi8020 = Dgi()
            dgi8020.dgi = '8020'
            dgi8020.add_tag_value('8020',tag8020)
            dgi9020 = Dgi()
            dgi9020.dgi = '9020'
            dgi9020.add_tag_value('8020',tag9020)
            cps.add_dgi(dgi8020)
            cps.add_dgi(dgi9020)
            break
    return cps

    
def process_dp(dp_file,rule_file):
    fh = FileHandle(dp_file,'rb+')
    fh.read(fh.current_offset,8596) #reserved
    dgi_list = get_dgi_list(fh)
    file_size = fh.get_file_size()
    cps_list = []
    while fh.current_offset < file_size:
        card_seq = fh.read_int64_reverse(fh.current_offset)
        card_data_total_len = fh.read_int_reverse(fh.current_offset)
        cps = Cps() #存储单个卡片数据
        cps.dp_file_path = dp_file
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
            #print('dgi=' + dgi_seq)
            if n_dgi_seq <= 0x0B00: #认为是记录
                template70 = fh.read_binary(fh.current_offset,1)
                if template70 != '70':
                    return
                next_len = get_next_len(fh)
            dgi_data = fh.read_binary(fh.current_offset,next_len)
            if n_dgi_seq <= 0x0B00 or (dgi_seq not in do_not_parse_tlv_list and data_parse.is_tlv(dgi_data)):
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
            process_rule_A001(rule_file,cps)
            process_rule_eps(rule_file,cps)
        cps_list.append(cps)
    return cps_list

if __name__ == '__main__':
    cps_list = process_dp('./test_data/yinlian.dp','./test_data/rule2.xml')
    for cps in cps_list:
        account = cps.get_account()
        path = 'D://' + account + 'txt'
        cps.save()