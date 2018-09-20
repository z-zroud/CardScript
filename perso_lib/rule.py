# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 请在DP处理模块中进行处理
from perso_lib.cps import Cps,Dgi
from perso_lib import des
from perso_lib import sm
from perso_lib import utils

class Rule:
    def __init__(self,cps):
        self.cps = cps

    def _get_tag_value(self,dgi,tag):
        value = ''
        for item in self.cps.dgi_list:
            if item.dgi == dgi:
                value = item.get_value(tag)
        return value

    def process_exchange(self,src_dgi,exchanged_dgi):
        '''交换两个DGI的值'''
        src_dgi_index = 0
        for item in self.cps.dgi_list:
            src_dgi_index += 1
            if item.dgi == src_dgi:
                item.dgi = exchanged_dgi
                value = item.get_value(src_dgi)
                if value is not None:
                    item.remove_tag(src_dgi)
                    item.add_tag_value(exchanged_dgi,value)
                break
        exchanged_dgi_index = 0        
        for item in self.cps.dgi_list:
            exchanged_dgi_index += 1
            if item.dgi == exchanged_dgi and src_dgi_index != exchanged_dgi_index:
                item.dgi = src_dgi
                value = item.get_value(exchanged_dgi)
                if value is not None:
                    item.remove_tag(exchanged_dgi)
                    item.add_tag_value(src_dgi,value)
                break
        return self.cps

    #处理DGI的映射
    def process_dgi_map(self,src_dgi,dst_dgi):
        for item in self.cps.dgi_list:
            if item.dgi == src_dgi:
                item.dgi = dst_dgi
                value = item.get_value(src_dgi)
                if value is not None:
                    item.remove_tag(src_dgi)
                    item.add_tag_value(dst_dgi,value)
                return self.cps
        return self.cps

    #解密数据
    def process_decrypt(self,dgi,key,key_type,isDelete80=False):
        for item in self.cps.dgi_list:
            if item.dgi == dgi:
                data = item.get_value(dgi)
                if key_type == 'DES':
                    data = des.des3_ecb_decrypt(key,data)     
                elif key_type == 'SM':
                    data = sm.sm4_ecb_decrypt(key,data)
                if isDelete80:
                    index = data.rfind('80')
                    data = data[0 : index]
                item.modify_value(dgi,data)
                return self.cps
        return self.cps

    #将目标tag添加到源tag(源tag不存在)
    def process_add_tag(self,src_dgi,src_tag,dst_dgi,dst_tag):
        dst_tag_value = self._get_tag_value(dst_dgi,dst_tag)
        dgi = Dgi()
        dgi.dgi = src_dgi
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
            dgi.dgi = src_dgi
            dgi.add_tag_value(src_tag,dst_tag_value)
            self.cps.add_dgi(dgi)
            return self.cps
        else:
            for item in self.cps.dgi_list:
                if item.dgi == src_dgi:
                    value = item.get_value(src_tag)
                    value += dst_tag_value
                    item.modify_value(src_tag,value)
                    return self.cps
        return self.cps

    #添加kcv
    def process_add_kcv(self,src_dgi,dst_dgi,key_type):
        item = self.cps.get_dgi(dst_dgi)
        key = item.get_value(item.dgi)
        key_len = len(key)
        kcv = ''
        if key_type == 'DES':
            for i in range(0,key_len,32):
                part_key = key[i : i + 32]
                kcv += des.des3_ecb_encrypt(part_key,'0000000000000000')[0:6]
        elif key_type == 'SM':
            for i in range(0,key_len,32):
                part_key = key[i : i + 32]
                kcv += sm.sm4_ecb_encrypt(part_key,'00000000000000000000000000000000')[0:6]
        dgi = Dgi()
        dgi.dgi = src_dgi
        dgi.add_tag_value(dgi.dgi,kcv)
        self.cps.add_dgi(dgi)
        return self.cps

    #向dgi中指定的tag添加固定值
    def process_add_fixed_tag(self,dgi,tag,value):
        dgis = self.cps.get_all_dgis()
        if dgi not in dgis:
            new_dgi = Dgi()
            new_dgi.dgi = dgi
            new_dgi.add_tag_value(tag,value)
            self.cps.add_dgi(new_dgi)
        else:
            for item in self.cps.dgi_list:
                if item.dgi == dgi:
                    if tag in item.tag_value_dict:
                        old_value = item.get_value(tag)
                        new_value = old_value[len(tag) + 2 :] + value
                        new_value = tag + utils.get_strlen(new_value) + new_value
                        item.modify_value(tag,new_value)
                    else:
                        item.add_tag_value(tag,value)
        return self.cps

    def process_assemble_tlv(self,dgi):
        for item in self.cps.dgi_list:
            if dgi == item.dgi:
                for key in item.tag_value_dict.keys():
                    data_len = int(len(item.tag_value_dict[key]) / 2)
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
            if item.dgi == dgi:
                item.remove_tag(tag)
                return self.cps
        return self.cps

    
