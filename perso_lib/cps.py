from perso_lib.ini_parse import IniParser
from perso_lib import utils
import os

class Dgi:
    def __init__(self):
        self.dgi = ''
        self.tag_value_dict = dict()

    def add_tag_value(self,tag,value):
        if tag not in self.tag_value_dict.keys():
            self.tag_value_dict[tag] = value

    def insert_after(self,after_tag,tag,value):
        if after_tag not in self.tag_value_dict.keys():
            self.add_tag_value(tag,value)
        else:
            temp_dict = self.tag_value_dict.copy()
            self.tag_value_dict.clear()
            for existed_tag,existed_value in temp_dict.items():
                self.add_tag_value(existed_tag,existed_value)
                if existed_tag == after_tag:
                    self.add_tag_value(tag,value)

    def insert_before(self,before_tag,tag,value):
        if before_tag not in self.tag_value_dict.keys():
            self.add_tag_value(tag,value)
        else:
            temp_dict = self.tag_value_dict.copy()
            self.tag_value_dict.clear()
            for existed_tag,existed_value in temp_dict.items():
                if existed_tag == before_tag:
                    self.add_tag_value(tag,value)
                self.add_tag_value(existed_tag,existed_value)
                    

    def modify_value(self,tag,value):
        if tag in self.tag_value_dict.keys():
            self.tag_value_dict[tag] = value

    def remove_tag(self,tag):
        if tag in self.tag_value_dict.keys():
            del self.tag_value_dict[tag]

    def get_value(self,tag):
        if tag in self.tag_value_dict.keys():
            return self.tag_value_dict[tag]
    
    def get_all_tags(self):
        return self.tag_value_dict
    
    def assemble_tlv(self,tag,data):
        '''拼接TLV格式，不考虑数据长度超过0xFF的情况'''
        data_len = len(data)
        if data_len >= 0x80 * 2:
            return tag + '81' + utils.get_strlen(data) + data
        else:
            return tag + utils.get_strlen(data) + data

#dgi only contains '_' and 'PSE','PPSE'
def _custom_sorted(dgi):
    number = 0
    if dgi.dgi == 'PSE':
        return 0x9FFFFF
    elif dgi.dgi == 'PPSE':
        return 0xAFFFFF
    elif dgi.dgi == 'A001': #扩展应用应放在8020应用秘钥之前
        return 0x8019
    elif dgi.dgi == '9010': #9010需放在8010前面个人化 自主产品 同方
        return 0x8009
    elif '_' in dgi.dgi:
        value = dgi.dgi.replace('_','0')
        number = utils.hex_str_to_int(value)
    else:
        number = utils.hex_str_to_int(dgi.dgi)
    return number

class Cps:
    def __init__(self):
        self.dgi_list = []
        self.dp_file_path = ''

    def add_dgi(self,dgi):
        '''添加DGI分组，若该DGI分组存在,则直接合并其中的tag'''
        for dgi_item in self.dgi_list:
            if dgi_item.dgi == dgi.dgi:
                tag_value_dict = dgi.get_all_tags()
                for tag,value in tag_value_dict.items():
                    dgi_item.add_tag_value(tag,value)
                break
        else:
            self.dgi_list.append(dgi)

    def remove_dgi(self,dgi):
        for item in self.dgi_list:
            if item.dgi == dgi:
                self.dgi_list.remove(item)
                return
    
    def get_dgi(self,dgi):
        for item in self.dgi_list:
            if dgi == item.dgi:
                return item

    def get_tag_value(self,dgi,tag):
        dgi_item = self.get_dgi(dgi)
        return dgi_item.get_value(tag)
    
    def _save(self,file_name,sort=_custom_sorted):
        open(file_name,'w+')    #make sure file is existed.
        ini = IniParser(file_name)
        self.dgi_list.sort(key=_custom_sorted)
        for item in self.dgi_list:
            ini.add_section(item.dgi)
            for key,value in item.tag_value_dict.items():
                ini.add_option(item.dgi,key,value)

    def save(self):
        # index = self.dp_file_path.rfind('.')
        # if index == -1:
        #     index = len(self.dp_file_path)
        dp_dir = self.dp_file_path[:self.dp_file_path.rfind('.')]
        print('dp_dir',dp_dir)
        if os.path.exists(dp_dir) is False:
            os.mkdir(dp_dir) 
        file_name = self.get_account() + '.txt'
        file_path = dp_dir + os.path.sep + file_name
        self._save(file_path)

    def get_account(self,tag='5A'):
        ret = ''
        for item in self.dgi_list:
            ret = item.get_value(tag)
            if ret is not None:
                if 'F' in ret:
                    return ret[4 : len(ret) - 1]
                else:
                    return ret[4 :]
        return ret

    def get_all_dgis(self):
        dgis = []
        for item in self.dgi_list:
            dgis.append(item.dgi)
        return dgis

    def get_first_app_dgi_list(self):
        """
        获取双应用中个人化第一个应用的DGI分组列表
        """
        dgis = []
        for item in self.dgi_list:
            if '_2' not in item.dgi and 'PSE' not in item.dgi and 'PPSE' not in item.dgi:
                dgis.append(item)
        return dgis

    def get_second_app_dgi_list(self):
        """
        获取双应用中个人化第二个应用的DGI分组列表
        """
        dgis = []
        for item in self.dgi_list:
            if '_2' in item.dgi:
                item.dgi = item.dgi[0:item.dgi.find('_2')]
                dgis.append(item)
        return dgis


if __name__ == '__main__':
    cps = Cps()
    dgi = Dgi()
    dgi.dgi = '0101'
    dgi.add_tag_value('9F1F','ABCD')
    dgi.add_tag_value('5F24','2018009')
    dgi.modify_value('9F1F','xxxx')
    dgi.remove_tag('5F24')
    cps.add_dgi(dgi)
    dgi = Dgi()
    dgi.dgi = '0201'
    dgi.add_tag_value('9F1F','YYYY')
    cps.add_dgi(dgi)
    cps.save()
