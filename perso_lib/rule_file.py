
class RuleFile:
    def __init__(self,xml):
        self.xml = xml

    def get_decrypted_attribute(self,dgi):
        nodes = self.xml.get_nodes(self.xml.root_element,'Decrypt')
        for node in nodes:
            dgi_attr = self.xml.get_attribute(node,'DGI')
            if dgi_attr == dgi:
                algrithm_type = self.xml.get_attribute(node,'type')
                key = self.xml.get_attribute(node,'key')
                return algrithm_type,key
        return None,None

    def get_tag_link_attribute(self,attr,value):
        nodes = self.xml.get_nodes(self.xml.root_element,'TagLink')
        for node in nodes:
            attr_value = self.xml.get_attribute(node,attr)
            if attr_value == value:
                emv_tag = self.xml.get_attribute(node,'EMVTag')
                sddf_tag = self.xml.get_attribute(node,'SDDFTag')
                value_format = self.xml.get_attribute(node,'ValueFormat')
                return emv_tag,sddf_tag,value_format
        return None,None,None

    
                
            