# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 请在DP处理模块中进行处理
from perso_lib.cps import Cps,Dgi
from perso_lib import algorithm
from perso_lib import utils
from perso_lib.xml_parse import XmlParser

class RuleXml(XmlParser):
    def __init__(self,rule_file):
        XmlParser.__init__(self,rule_file)

    def get_decrypted_attribute(self,dgi):
        '''<Decrypt DGI="8000" type="DES/SM" key="0123456789ABCDEF1111111111111111" />'''
        nodes = self.get_nodes(self.root_element,'Decrypt')
        for node in nodes:
            dgi_attr = self.get_attribute(node,'DGI')
            if dgi_attr == dgi:
                algrithm_type = self.get_attribute(node,'type')
                key = self.get_attribute(node,'key')
                return algrithm_type,key
        return None,None

    def get_tag_link_attribute(self,attr,value):
        '''
        根据属性=值匹配相应的TagLink节点
        <TagLink EMVTag="9206" SDDFTag="1010N103" EMVDataName="DGI9206" ValueFormat="TLV"/>
        '''
        nodes = self.get_nodes(self.root_element,'TagLink')
        for node in nodes:
            attr_value = self.get_attribute(node,attr)
            if attr_value == value:
                emv_tag = self.get_attribute(node,'EMVTag')
                sddf_tag = self.get_attribute(node,'SDDFTag')
                value_format = self.get_attribute(node,'ValueFormat')
                return emv_tag,sddf_tag,value_format
        return None,None,None

if __name__ == '__main__':
    rule = RuleXml('./test_data/rule2.xml')
    decrypt_nodes = rule.get_nodes(rule.root_element,'Decrypt')
    for node in decrypt_nodes:
        attr = rule.get_attribute(node,'DGI')
        rule.get_attributes(node)

class Rule:
    def __init__(self,cps, rule_handle):
        self.cps = cps
        self.rule_handle = rule_handle

    def _get_tag_value(self,name,tag):
        value = ''
        for item in self.cps.dgi_list:
            if item.name == name:
                value = item.get_value(tag)
        return value

    def process_exchange(self,src_dgi,exchanged_dgi):
        '''交换两个DGI的值'''
        src_dgi_index = 0
        for item in self.cps.dgi_list:
            src_dgi_index += 1
            if item.name == src_dgi:
                item.name = exchanged_dgi
                value = item.get_value(src_dgi)
                if value is not None:
                    item.remove_tag(src_dgi)
                    item.add_tag_value(exchanged_dgi,value)
                break
        exchanged_dgi_index = 0        
        for item in self.cps.dgi_list:
            exchanged_dgi_index += 1
            if item.name == exchanged_dgi and src_dgi_index != exchanged_dgi_index:
                item.name = src_dgi
                value = item.get_value(exchanged_dgi)
                if value is not None:
                    item.remove_tag(exchanged_dgi)
                    item.add_tag_value(src_dgi,value)
                break
        return self.cps

    #处理DGI的映射
    def process_dgi_map(self,src_dgi,dst_dgi):
        for item in self.cps.dgi_list:
            if item.name == src_dgi:
                item.name = dst_dgi
                value = item.get_value(src_dgi)
                if value is not None:
                    item.remove_tag(src_dgi)
                    item.add_tag_value(dst_dgi,value)
                return self.cps
        return self.cps

    def _process_decrypt(self,key,key_type,data,is_delete80):
        if key_type == 'DES':
            data = algorithm.des3_ecb_decrypt(key,data)     
        elif key_type == 'SM':
            data = algorithm.sm4_ecb_decrypt(key,data)
        elif key_type == 'BASE64':
            data = utils.base64_to_bcd(data)
        elif key_type == 'BCD':
            data = utils.str_to_bcd(data)
        if is_delete80:
            index = data.rfind('80')
            data = data[0 : index]
        return data

    #解密数据
    def process_decrypt(self,dgi,tag,key,key_type,is_delete80=False):
        if dgi == '':
            for item in self.cps.dgi_list:
                data = item.get_value(tag)
                if data is not None and data != '':
                    data = self._process_decrypt(key,key_type,data,is_delete80)
                    item.modify_value(tag,data)
        else:
            for item in self.cps.dgi_list:
                if item.name == dgi:
                    data = item.get_value(tag)
                    if data is None:    #说明DGI中不包含该数据，直接返回
                        return self.cps
                    data = self._process_decrypt(key,key_type,data,is_delete80)
                    item.modify_value(tag,data)
                    return self.cps
        return self.cps

    #将目标tag添加到源tag(源tag不存在)
    def process_add_tag(self,src_dgi,src_tag,dst_dgi,dst_tag):
        dst_tag_value = self._get_tag_value(dst_dgi,dst_tag)
        dgi = Dgi()
        dgi.name = src_dgi
        dgi.add_tag_value(src_tag,dst_tag_value)
        self.cps.add_dgi(dgi)
        return self.cps

    #合并目标tag到源tag(源tag必须存在)
    def process_merge_tag(self,src_dgi,src_tag,dst_dgi,dst_tag):
        dst_item = self.cps.get_dgi(dst_dgi)
        dst_tag_value = dst_item.get_value(dst_tag)
        src_item = self.cps.get_dgi(src_dgi)
        if src_item is None:
            dgi = Dgi()
            dgi.name = src_dgi
            dgi.add_tag_value(src_tag,dst_tag_value)
            self.cps.add_dgi(dgi)
            return self.cps
        else:
            for item in self.cps.dgi_list:
                if item.name == src_dgi:
                    value = item.get_value(src_tag)
                    value += dst_tag_value
                    item.modify_value(src_tag,value)
                    return self.cps
        return self.cps

    #添加kcv
    def process_add_kcv(self,src_dgi,dst_dgi,key_type):
        item = self.cps.get_dgi(dst_dgi)
        key = item.get_value(item.name)
        key_len = len(key)
        kcv = ''
        if key_type == 'DES':
            for i in range(0,key_len,32):
                part_key = key[i : i + 32]
                kcv += algorithm.des3_ecb_encrypt(part_key,'0000000000000000')[0:6]
        elif key_type == 'SM':
            for i in range(0,key_len,32):
                part_key = key[i : i + 32]
                kcv += algorithm.sm4_ecb_encrypt(part_key,'00000000000000000000000000000000')[0:6]
        dgi = Dgi()
        dgi.name = src_dgi
        dgi.add_tag_value(dgi.name,kcv)
        self.cps.add_dgi(dgi)
        return self.cps

    #向dgi中指定的tag添加固定值
    def process_add_fixed_tag(self,dgi_name,tag,value,before_tag,after_tag):
        dgis = self.cps.get_all_dgis()
        dgi_names = [dgi.name for dgi in dgis]
        if dgi_name not in dgi_names:
            new_dgi = Dgi()
            new_dgi.name = dgi_name
            new_dgi.add_tag_value(tag,value)
            self.cps.add_dgi(new_dgi)
        else:
            for item in self.cps.dgi_list:
                if item.name == dgi_name:
                    if tag in item.tag_value_dict:
                        old_value = item.get_value(tag)
                        new_value = old_value[len(tag) + 2 :] + value
                        new_value = tag + utils.get_strlen(new_value) + new_value
                        item.modify_value(tag,new_value)
                    else:
                        if before_tag is not '':
                            item.insert_before(before_tag,tag,value)
                        elif after_tag is not '':
                            item.insert_after(after_tag,tag,value)
                        else:
                            item.add_tag_value(tag,value)
        return self.cps

    #向dgi中指定的tag添加固定值
    def process_add_value(self,dgi,tag,value,before_tag,after_tag):
        return self.process_add_fixed_tag(dgi,tag,value,before_tag,after_tag)

    def process_assemble_tlv(self,dgi):
        for item in self.cps.dgi_list:
            if dgi == item.name:
                for key,value in item.tag_value_dict.items():
                    if not key:
                        print('dgi' + dgi + '存在非法的None Tag')
                    if not value:
                        print('dgi' + dgi + ' tag' + key + '值为None,请检查配置文件对该值是否配置正确')
                    data_len = int(len(value) / 2)
                    if data_len > 0x80:
                        item.tag_value_dict[key] = key + '81' + utils.int_to_hex_str(data_len) + item.tag_value_dict[key]
                    else:
                        item.tag_value_dict[key] = key + utils.int_to_hex_str(data_len) + item.tag_value_dict[key]
                return self.cps
        return self.cps
                    

    #删除dgi分组
    def process_remove_dgi(self,dgi):
        self.cps.remove_dgi(dgi)
        return self.cps

    #删除dgi指定的tag
    def process_remove_tag(self,dgi,tag):
        for item in self.cps.dgi_list:
            if item.name == dgi:
                item.remove_tag(tag)
                return self.cps
        return self.cps

    def process_assemble_dgi(self,src_dgi,src_tag,format_str):
        data = ""
        tag_list = format_str.split(',')
        for tag in tag_list[::-1]:
            if '.' not in tag:  #说明是模板
                data = tag + utils.get_strlen(data) + data
            else:
                dst_dgi = tag.split('.')[0]
                dst_tag = tag.split('.')[1]
                if dst_dgi == '':
                    data = dst_tag + data
                elif dst_dgi[len(dst_dgi) - 1] == 'v':
                    dst_dgi = dst_dgi[0: len(dst_dgi) - 1]
                    value = self.cps.get_tag_value(dst_dgi,dst_tag)
                    if not value:
                        print('dgi %s tag %s 不存在'%(dst_dgi,dst_tag))
                    data = value + data
                else:
                    value = ''
                    if dst_dgi in ('9102','9103'):  #对于9103,9102需要特殊处理
                        tlvs = utils.parse_tlv(self.cps.get_tag_value(dst_dgi,dst_dgi))
                        for tlv in tlvs:
                            if tlv.tag == dst_tag:
                                value = tlv.value
                                break
                    else:
                        value = self.cps.get_tag_value(dst_dgi,dst_tag)
                    if not value:
                        print('dgi %s tag %s 不存在'%(dst_dgi,dst_tag))
                    tag_len = utils.get_strlen(value)
                    data = dst_tag + tag_len + value + data
        dgi = Dgi()
        dgi.name = src_dgi
        dgi.add_tag_value(src_tag,data)
        self.cps.add_dgi(dgi)
        return self.cps

    # 以下接口为对上面函数的封装，若需要处理细节，请使用上面接口，否则
    # 请使用下面的接口函数
    def wrap_process_add_tag(self):
        add_tag_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'AddTag')
        for node in add_tag_nodes:
            attrs = self.rule_handle.get_attributes(node)
            if 'srcTag' not in attrs:
                attrs['srcTag'] = attrs['dstTag']
            self.process_add_tag(attrs['srcDGI'],attrs['srcTag'],attrs['dstDGI'],attrs['dstTag'])
        return self.cps
        
    def wrap_process_merge_tag(self):
        merge_tag_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'MergeTag')
        for node in merge_tag_nodes:
            attrs = self.rule_handle.get_attributes(node)
            self.process_merge_tag(attrs['srcDGI'],attrs['srcTag'],attrs['dstDGI'],attrs['dstTag']) 
        return self.cps

    def wrap_process_add_fixed_tag(self):
        fixed_tag_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'AddFixedTag')
        for node in fixed_tag_nodes:
            attrs = self.rule_handle.get_attributes(node)
            if 'afterTag' not in attrs:
                attrs['afterTag'] = ''
            if 'beforeTag' not in attrs:
                attrs['beforeTag'] = ''
            self.process_add_fixed_tag(attrs['srcDGI'],attrs['tag'],attrs['value'],attrs['beforeTag'],attrs['afterTag'])
        return self.cps
    
    def wrap_process_add_value(self):
        fixed_tag_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'AddValue')
        for node in fixed_tag_nodes:
            attrs = self.rule_handle.get_attributes(node)
            if 'afterTag' not in attrs:
                attrs['afterTag'] = ''
            if 'beforeTag' not in attrs:
                attrs['beforeTag'] = ''
            self.process_add_value(attrs['srcDGI'],attrs['tag'],attrs['value'],attrs['beforeTag'],attrs['afterTag'])
        return self.cps

    def wrap_process_decrypt(self):
        decrypt_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'Decrypt')
        for node in decrypt_nodes:
            attrs = self.rule_handle.get_attributes(node)
            delete80 = False
            if 'delete80' in attrs:
                delete80 = True if attrs['delete80'] == 'true' else False
            if 'key' not in attrs:
                attrs['key'] = ''
            if 'DGI' not in attrs:
                attrs['DGI'] = ''
            if 'tag' not in attrs:
                self.process_decrypt(attrs['DGI'],attrs['DGI'],attrs['key'],attrs['type'],delete80)
            else:
                self.process_decrypt(attrs['DGI'],attrs['tag'],attrs['key'],attrs['type'],delete80)
        return self.cps

    def wrap_process_add_kcv(self):
        kcv_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'AddKcv')
        for node in kcv_nodes:  #需放在解密之后执行
            attrs = self.rule_handle.get_attributes(node)
            self.process_add_kcv(attrs['srcDGI'],attrs['dstDGI'],attrs['type'])
        return self.cps

    def wrap_process_exchange(self):
        exchange_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'Exchange')
        for node in exchange_nodes:
            exchange_attrs = self.rule_handle.get_attributes(node)
            self.process_exchange(exchange_attrs['srcDGI'],exchange_attrs['exchangedDGI'])
        return self.cps

    def wrap_process_assemble_tlv(self):
        assmble_tlv_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'AssembleTlv')
        for node in assmble_tlv_nodes:
            attrs = self.rule_handle.get_attributes(node)
            self.process_assemble_tlv(attrs['DGI'])
        return self.cps

    def wrap_process_assemble_dgi(self):
        assmble_dgi_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'AssembleDgi')
        for node in assmble_dgi_nodes:
            attrs = self.rule_handle.get_attributes(node)
            self.process_assemble_dgi(attrs['srcDGI'],attrs['srcTag'],attrs['format'])
        return self.cps
    
    def wrap_process_remove_dgi(self):
        remove_dgi_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'RemoveDgi')
        for node in remove_dgi_nodes:
            attrs = self.rule_handle.get_attributes(node)
            self.process_remove_dgi(attrs['DGI'])
        return self.cps

    def wrap_process_remove_tag(self):
        remove_tag_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'RemoveTag')
        for node in remove_tag_nodes:
            attrs = self.rule_handle.get_attributes(node)
            self.process_remove_tag(attrs['DGI'],attrs['tag'])
        return self.cps

    def wrap_process_dgi_map(self):
        map_nodes = self.rule_handle.get_nodes(self.rule_handle.root_element,'Map')
        for node in map_nodes:  #需放在解密之前执行
            attrs = self.rule_handle.get_attributes(node)
            self.process_dgi_map(attrs['srcDGI'],attrs['dstDGI'])
    
    
