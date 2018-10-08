# 该类用于解析配置规则文件
from perso_lib.xml_parse import XmlParser
class RuleFile(XmlParser):
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
    rule = RuleFile('./test_data/rule2.xml')
    decrypt_nodes = rule.get_nodes(rule.root_element,'Decrypt')
    for node in decrypt_nodes:
        attr = rule.get_attribute(node,'DGI')
        rule.get_attributes(node)