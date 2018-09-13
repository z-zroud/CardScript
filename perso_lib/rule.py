# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 需要在DP处理模块中进行处理
from perso_lib.cps import Cps

class Rule:
    def __init__(self):
        self.cps = Cps()


    #解密数据
    def process_decrypt(self,dgi,tag,key,key_type):
        pass

    #将目标tag添加到源tag(源tag不存在)
    def process_add_tag(self,src_dgi,src_tag,dst_dgi,dst_tag):
        pass

    #合并目标tag到源tag(源tag必须存在)
    def process_merge_tag(self,src_dgi,src_tag,dst_dgi,dst_tag):
        pass

    #添加kcv
    def process_add_kcv(self,src_dgi,dst_dgi,key_type):
        pass

    #向dgi中指定的tag添加固定值
    def process_add_fixed_tag(self,dgi,tag,value):
        for dgi in self.cps.dgi_list:
            dgi.add_tag_value(tag,value)

    #删除dgi分组
    def process_delete_dgi(self,dgi):
        self.cps.remove_dgi(dgi)

    #删除dgi指定的tag
    def process_delete_tag(self,dgi,tag):
        for dgi in self.cps.dgi_list:
            dgi.remove_tag(tag)

    
