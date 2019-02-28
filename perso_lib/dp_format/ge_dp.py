from perso_lib.file_handle import FileHandle
from perso_lib.cps import Cps,Dgi
from perso_lib import utils
from perso_lib.rule import Rule,RuleXml

def process_data(app_flag,card_data):
    dgi = Dgi()
    dgi.name = app_flag
    data = card_data.split('|')
    dgi.add_tag_value(data[0],data[2])
    return dgi

def process_rule(rule_file_name,cps):    
    rule_handle = RuleXml(rule_file_name)
    rule = Rule(cps,rule_handle)
    rule.wrap_process_decrypt()
    rule.wrap_process_add_tag()
    rule.wrap_process_merge_tag()
    rule.wrap_process_add_fixed_tag()
    rule.wrap_process_add_kcv()
    rule.wrap_process_exchange()
    rule.wrap_process_assemble_tlv()
    rule.wrap_process_add_value()
    rule.wrap_process_assemble_dgi()
    rule.wrap_process_remove_dgi()
    rule.wrap_process_remove_tag()
    return rule.cps

def process_dp(dp_file,rule_file):
    fh = FileHandle(dp_file,'r+')
    cps_list = []
    cps = Cps()
    cps.dp_file_path = dp_file
    app_flag = ''
    while True: 
        card_data = fh.read_line()
        if card_data == '': #数据处理完毕
            break
        elif card_data == '[01]':
            app_flag = '01'
            continue
        elif card_data == '[02]':
            app_flag = '02'
            continue
        elif card_data == '[03]':
            app_flag = '03'
            continue
        dgi = process_data(app_flag,card_data)
        cps.add_dgi(dgi)
    if rule_file is not None:
        cps = process_rule(rule_file,cps)
    cps_list.append(cps)
    return cps_list