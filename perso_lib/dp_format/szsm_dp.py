from perso_lib.file_handle import FileHandle
from perso_lib.cps import Cps,Dgi
from perso_lib import utils
from perso_lib.rule import Rule,RuleXml

def process_tlv(data):
    item_list = []
    items = data.split('|')
    items_count = len(items)
    for index in range(0,items_count,3):
        if index + 3 > items_count:
            break
        tag = items[index]
        length = items[index + 1]
        value = items[index + 2]
        item_list.append((tag,length,value))
    return item_list

def process_data(data,data_type):
    dgi = Dgi()
    dgi.name = data_type
    item_list = process_tlv(data)
    for item in item_list:
        dgi.add_tag_value(item[0],item[2])
    return dgi

def process_EF02(cps):
    data_ef02 = ''
    for item in cps.dgi_list:
        if item.name == '01':
            data_ef02 = item.get_value('EF02')
    data_ef02 = data_ef02[8:]   #EF02总长度
    for i in range(8):
        bcd_item_len = data_ef02[0 : 8]
        n_item_len = int(utils.bcd_to_str(bcd_item_len)) * 2
        value = data_ef02[8 : 8 + n_item_len]
        data_ef02 = data_ef02[8 + n_item_len :]
        dgi = Dgi()
        if i == 3:
            dgi.name = '8205'
            dgi.add_tag_value(dgi.name,value)
            cps.add_dgi(dgi)
        elif i == 4:
            dgi.name = '8204'
            dgi.add_tag_value(dgi.name,value)
            cps.add_dgi(dgi)
        elif i == 5:
            dgi.name = '8203'
            dgi.add_tag_value(dgi.name,value)
            cps.add_dgi(dgi)
        elif i == 6:
            dgi.name = '8202'
            dgi.add_tag_value(dgi.name,value)
            cps.add_dgi(dgi)
        elif i == 7:
            dgi.name = '8201'
            dgi.add_tag_value(dgi.name,value)
            cps.add_dgi(dgi)
    return cps

def process_rule(rule_file_name,cps):    
    rule_handle = RuleXml(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_add_tag()
    rule.wrap_process_merge_tag()
    rule.wrap_process_add_fixed_tag()
    rule.wrap_process_decrypt()
    rule.wrap_process_add_kcv()
    rule.wrap_process_exchange()
    rule.wrap_process_assemble_tlv()
    rule.wrap_process_remove_dgi()
    rule.wrap_process_remove_tag()
    return rule.cps

def process_dp(dp_file,rule_file):
    fh = FileHandle(dp_file,'r+')
    flag_dc = '[01]'
    flag_ec = '[02]'
    flag_q = '[03]'
    cps_list = []
    while True:
        cps = Cps()
        cps.dp_file_path = dp_file
        card_data = fh.read_line()
        if card_data == '': #数据处理完毕
            break
        index_dc = card_data.find(flag_dc)
        index_ec = card_data.find(flag_ec)
        index_q = card_data.find(flag_q)
        data_dc = card_data[index_dc + len(flag_dc) : index_ec]
        data_ec = card_data[index_ec + len(flag_ec) : index_q]
        data_q = card_data[index_q + len(flag_q) :]
        dgi_dc = process_data(data_dc,'01')
        dgi_ec = process_data(data_ec,'02')
        dgi_q = process_data(data_q,'03')
        cps.add_dgi(dgi_dc)
        cps.add_dgi(dgi_ec)
        cps.add_dgi(dgi_q)
        cps = process_EF02(cps)
        if rule_file is not None:
            cps = process_rule(rule_file,cps)
        cps_list.append(cps)
    return cps_list



if __name__ == '__main__':
    cps_list = process_dp('./test_data/szsm.dp','./test_data/rule1.xml')
    for cps in cps_list:
        account = cps.get_account()
        path = 'D://' + account + 'txt'
        cps.save(path)