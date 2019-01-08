# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 请在DP处理模块中进行处理
from perso_lib.cps import Cps,Dgi
from perso_lib import des
from perso_lib import sm
from perso_lib import utils
from perso_lib.kms import Kms
from perso_lib.xml_parse import XmlParser,XmlMode
from perso_lib.tempalte_form import McTable,DataItem,DataType
from perso_lib.word import Docx
from xml.dom import Node
import importlib
import os
import shutil

class GenDpRequirementDoc:
    def __init__(self,config_file,doc_file):
        self.config_file = config_file
        self.doc_file = doc_file
        self.xml_handle = XmlParser(config_file,XmlMode.READ)
        

    def _create_table(self,dgi_node):
        dgi_name = self.xml_handle.get_attribute(dgi_node,'name')
        dgi_comment = self.xml_handle.get_attribute(dgi_node,'comment')
        self.doc.add_heading(3,dgi_name + dgi_comment)
        new_table = self.doc.add_table(1,4)
        for col in range(4):
            cell = self.doc.get_cell(new_table,0,col)
            self.doc.set_cell_property(cell,'FFCA00')
        # for row in range(1,3):
        #     for col in range(4):
        #         cell = self.doc.get_cell(new_table,row,col)
        #         self.doc.set_cell_text(cell,'AA')
        # self.doc.save_as('demo.docx')
        tag_nodes = self.xml_handle.get_child_nodes(dgi_node)
        for tag_node in tag_nodes:
            tag_name = self.xml_handle.get_attribute(tag_node,'name')
            tag_value = self.xml_handle.get_attribute(tag_node,'value')
            if not tag_value:
                tag_value = ''
            tag_comment = self.xml_handle.get_attribute(tag_node,'comment')
            if not tag_comment:
                tag_comment = ''
            new_row = new_table.add_row()
            self.doc.set_cell_text(new_row.cells[0],tag_name)
            self.doc.set_cell_text(new_row.cells[1],tag_value)
            self.doc.set_cell_text(new_row.cells[2],tag_comment)



    def gen_dp_doc(self):
        self.doc = Docx(self.doc_file)
        app_nodes = self.xml_handle.get_child_nodes(self.xml_handle.root_element,'App')
        for app_node in app_nodes:
            dgi_nodes = self.xml_handle.get_child_nodes(app_node,'DGI')
            for dgi_node in dgi_nodes:
                self._create_table(dgi_node)
            self.doc.save_as('demo.docx')


class GenVisaConfig:
    def __init__(self,template_config,visa_table_obj):
        self.visa_table_obj = visa_table_obj
        self.template_config = template_config
        self.template_handle = XmlParser(template_config)
        self.not_found_data = []

    def _get_data(self,tag,source_type,desc=None):
        data_type = None
        data = None
        if source_type == 'contact':
            data_type = DataType.CONTACT
        elif source_type == 'contactless':
            data_type = DataType.CONTACTLESS
        if utils.is_hex_str(tag):
            data = self.visa_table_obj.get_data(tag,data_type,desc)
        return data
    
    def print_template_not_found_data(self):
        print('====================template not found tag list====================')
        ignore_tag_list = ['8000','8001','9000','9001','A006','A016','8401','8400','8201','8202','8203','8204','8205']
        for data in self.not_found_data:
            if data[0] not in ignore_tag_list:
                print(data[0] + '||',end=' ')
                if data[1]:
                    print(data[1] + '||', end=' ')
                if data[2]:
                    print(data[2] + '||',end='')
                print('')


    def save(self,dp_config,char_set='UTF-8'):
        fpath,fname = os.path.split(dp_config)    #分离文件名和路径
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        shutil.copyfile(self.template_config,dp_config)      #复制文件
        new_xml_handle = XmlParser(dp_config,XmlMode.READ)
        tag_nodes = new_xml_handle.get_nodes(new_xml_handle.root_element,'Tag')
        for tag_node in tag_nodes:
            attr_type = new_xml_handle.get_attribute(tag_node,'type')
            attr_tag = new_xml_handle.get_attribute(tag_node,'name')
            attr_source = new_xml_handle.get_attribute(tag_node,'source')
            attr_desc = new_xml_handle.get_attribute(tag_node,'comment')
            attr_format = new_xml_handle.get_attribute(tag_node,'format')
            if attr_type == 'fixed':
                value = new_xml_handle.get_attribute(tag_node,'value') #如果模板中fixed类型的tag已经有固定值，直接使用该值
                if not value:
                    data = self._get_data(attr_tag,attr_source,attr_desc)
                    if data:
                        #为了按指定属性顺序写入xml,需要重新添加fixed类型的tag属性
                        new_xml_handle.remove_attribute(tag_node,'name')
                        new_xml_handle.remove_attribute(tag_node,'type')
                        new_xml_handle.remove_attribute(tag_node,'comment')
                        new_xml_handle.remove_attribute(tag_node,'format')
                        new_xml_handle.set_attribute(tag_node,'name',attr_tag)
                        new_xml_handle.set_attribute(tag_node,'type','fixed')
                        new_xml_handle.set_attribute(tag_node,'value',data)
                        new_xml_handle.set_attribute(tag_node,'format',attr_format)
                        new_xml_handle.set_attribute(tag_node,'comment',attr_desc)
                    else:
                        self.not_found_data.append((attr_tag,attr_source,attr_desc))
            else:
                data = self._get_data(attr_tag,attr_source,attr_desc)
                if not data:
                    self.not_found_data.append((attr_tag,attr_source,attr_desc))
            new_xml_handle.remove_attribute(tag_node,'source')
        new_xml_handle.save(char_set)
        return None

class GenMcDpConfig:
    def __init__(self,template_config,mc_table_obj):
        self.mc_table_obj = mc_table_obj
        self.template_config = template_config
        self.template_handle = XmlParser(template_config)
        self.not_found_data = []

    def _get_data(self,tag,source_type,desc=None):
        data_type = None
        data = None
        if source_type == 'contact':
            data_type = DataType.CONTACT
        elif source_type == 'contactless':
            data_type = DataType.CONTACTLESS
        elif source_type == 'mca':
            data_type = DataType.MCA
        elif source_type == 'magstripe':
            data_type = DataType.MAGSTRIPE
        elif source_type == 'fci':
            data_type = DataType.FCI
        elif source_type == 'shared':
            data_type = DataType.SHARED
        if utils.is_hex_str(tag):
            data = self.mc_table_obj.get_data(tag,data_type,desc)
        else:
            data = self.mc_table_obj.get_data_by_desc(desc,data_type)
        return data
    
    def print_template_not_found_data(self):
        print('====================template not found tag list====================')
        ignore_tag_list = ['8000','8001','9000','9001','A006','A016','8401','8400','8201','8202','8203','8204','8205']
        for data in self.not_found_data:
            if data[0] not in ignore_tag_list:
                print(data[0] + '||',end=' ')
                if data[1]:
                    print(data[1] + '||', end=' ')
                if data[2]:
                    print(data[2] + '||',end='')
                print('')


    def save(self,dp_config,char_set='UTF-8'):
        fpath,fname = os.path.split(dp_config)    #分离文件名和路径
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        shutil.copyfile(self.template_config,dp_config)      #复制文件
        new_xml_handle = XmlParser(dp_config,XmlMode.READ)
        tag_nodes = new_xml_handle.get_nodes(new_xml_handle.root_element,'Tag')
        comm_node = new_xml_handle.get_first_node(new_xml_handle.root_element,'Common')
        for tag_node in tag_nodes:
            attr_type = new_xml_handle.get_attribute(tag_node,'type')
            attr_tag = new_xml_handle.get_attribute(tag_node,'name')
            attr_source = new_xml_handle.get_attribute(tag_node,'source')
            attr_desc = new_xml_handle.get_attribute(tag_node,'comment')
            attr_format = new_xml_handle.get_attribute(tag_node,'format')
            if attr_type == 'fixed':
                value = new_xml_handle.get_attribute(tag_node,'value') #如果模板中fixed类型的tag已经有固定值，直接使用该值
                if not value:
                    data = self._get_data(attr_tag,attr_source,attr_desc)
                    if data:
                        #为了按指定属性顺序写入xml,需要重新添加fixed类型的tag属性
                        new_xml_handle.remove_attribute(tag_node,'name')
                        new_xml_handle.remove_attribute(tag_node,'type')
                        new_xml_handle.remove_attribute(tag_node,'comment')
                        new_xml_handle.remove_attribute(tag_node,'format')
                        new_xml_handle.set_attribute(tag_node,'name',attr_tag)
                        new_xml_handle.set_attribute(tag_node,'type','fixed')
                        new_xml_handle.set_attribute(tag_node,'value',data)
                        new_xml_handle.set_attribute(tag_node,'format',attr_format)
                        new_xml_handle.set_attribute(tag_node,'comment',attr_desc)
                        if attr_desc and attr_desc == 'Length Of ICC Public Key Modulus':
                            if data == '90':
                                data = '1152'
                            else:
                                data = '1024'
                            new_xml_handle.set_attribute(comm_node,'rsa',data)
                    else:
                        self.not_found_data.append((attr_tag,attr_source,attr_desc))
            else:
                data = self._get_data(attr_tag,attr_source,attr_desc)
                if not data:
                    self.not_found_data.append((attr_tag,attr_source,attr_desc))
            new_xml_handle.remove_attribute(tag_node,'source')
        new_xml_handle.save(char_set)
        return None

class MockCps:
    def __init__(self,xml_file,process_dp_file_module):
        self.cps = Cps()
        self.cps.dp_file_path = xml_file
        self.xml_handle = XmlParser(xml_file)
        self.process_dp_file_module = process_dp_file_module

    def _get_value(self,tag,data,vlaue_format):
        if vlaue_format == 'TLV':
            return utils.assemble_tlv(tag,data)
        else:
            return data

    def _parse_tag_value(self,tag_node,kms=None):
        attrs = self.xml_handle.get_attributes(tag_node)
        tag = attrs['name']
        value = ''
        value_type = attrs['type']
        value_format = attrs['format']
        if value_type == 'fixed':
            value = self._get_value(tag,attrs['value'],value_format)
        elif value_type == 'kms':
            if not kms:
                print('kms is None')
            else:
                tmp = tag
                if 'sig_id' in attrs:
                    tmp = tmp + '_' + attrs['sig_id']
                value = self._get_value(tag,kms.get_value(tmp),value_format)
        elif value_type == 'file':
            mod_obj = importlib.import_module(self.process_dp_file_module)
            if mod_obj:
                if hasattr(mod_obj,'process_tag' + tag):
                    func = getattr(mod_obj,'process_tag' + tag)
                    value = self._get_value(tag,func(),value_format)
                else:
                    print('can not process tag' + tag)
        return tag,value
        
    def _parse_template(self,template_node):
        template_value = ''
        template = self.xml_handle.get_attribute(template_node,'name')
        child_nodes = self.xml_handle.get_child_nodes(template_node)
        for child_node in child_nodes:
            if child_node.nodeName == 'Tag':
                _,value = self._parse_tag_value(child_node)
                template_value += value
            elif child_node.nodeName == 'Template':
                template_value += self._parse_template(child_node)
        return utils.assemble_tlv(template,template_value)

    def _process_signature(self,app_node,kms):
        sig_nodes = self.xml_handle.get_nodes(app_node,'Sig')
        for sig_node in sig_nodes:
            sig_data = ''
            sig_id = self.xml_handle.get_attribute(sig_node,'id')
            tag_nodes = self.xml_handle.get_child_nodes(sig_node)
            tag5A = ''
            for tag_node in tag_nodes:
                    tag,value = self._parse_tag_value(tag_node,kms)
                    sig_data += value
                    if tag == '5A':
                        tag5A = value[4:]
            if tag5A == '':
                print('sig data must contains card no')
                tag5A = kms.issuer_bin + '0000000001'
            kms.gen_new_icc_cert(tag5A,sig_id,sig_data)
            kms.gen_new_ssda(kms.issuer_bin,sig_id,sig_data)

    def _get_common_node(self):
        issuer_bin = ''
        rsa_len = 1024
        Common_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'Common')
        if Common_node:
            issuer_bin = self.xml_handle.get_attribute(Common_node,'bin')
            if not issuer_bin or issuer_bin == '':
                print('Please provide card Bin number, if not, card will use default Bin number:654321')
                issuer_bin = '654321'
            rsa_len_str = self.xml_handle.get_attribute(Common_node,'rsa')
            if not rsa_len_str or rsa_len_str == '':
                print('Please provide card ICC RSA length, if not, card will use default RSA len:1024')
            else:
                rsa_len = int(rsa_len_str)       
        return issuer_bin,rsa_len

    def _get_bin(self):
        card_bin,_ = self._get_common_node()
        return card_bin

    def _get_rsa_len(self):
        _,rsa_len = self._get_common_node()
        return rsa_len

    def _process_dgi(self,dgi_node,kms=None):
        dgi = Dgi()
        dgi.dgi = self.xml_handle.get_attribute(dgi_node,'name')
        child_nodes = self.xml_handle.get_child_nodes(dgi_node)
        for child_node in child_nodes:
            if child_node.nodeName == 'Tag':
                tag,value = self._parse_tag_value(child_node,kms)
                data_format = self.xml_handle.get_attribute(child_node,'format')
                if data_format == 'V':  #对于value数据，取dgi作为tag
                    dgi.append_tag_value(dgi.dgi,value)
                else:
                    dgi.add_tag_value(tag,value)
            elif child_node.nodeName == 'Template':
                template_value = self._parse_template(child_node)
                dgi.append_tag_value(dgi.dgi,template_value)
            else:
                print('unrecognize node' + child_node.nodeName)
        return dgi

    def _process_pse(self,pse_node):
        pse = Dgi()
        pse.dgi = pse_node.nodeName
        dgi_nodes = self.xml_handle.get_child_nodes(pse_node)
        for dgi_node in dgi_nodes:
            dgi = self._process_dgi(dgi_node)
            for key,value in dgi.tag_value_dict.items():
                pse.add_tag_value(key,value)
        return pse

    def gen_cps(self):
        app_nodes = self.xml_handle.get_nodes(self.xml_handle.root_element,'App')
        count = 0
        for app_node in app_nodes:
            count += 1
            issuer_bin = self._get_bin()
            rsa_len = self._get_rsa_len()
            kms = Kms()
            kms.init(issuer_bin,rsa_len)
            self._process_signature(app_node,kms)
            dgi_nodes = self.xml_handle.get_child_nodes(app_node,"DGI")
            for dgi_node in dgi_nodes:
                dgi = self._process_dgi(dgi_node,kms)
                if count > 1:
                    dgi.dgi = dgi.dgi + '_' + str(count)
                self.cps.add_dgi(dgi)
            pse_node = self.xml_handle.get_first_node(app_node,'PSE')
            pse_dgi = self._process_pse(pse_node)
            self.cps.add_dgi(pse_dgi)
            ppse_node = self.xml_handle.get_first_node(app_node,'PPSE')
            ppse_dgi = self._process_pse(ppse_node)
            self.cps.add_dgi(ppse_dgi)
            kms.close()
        return self.cps


if __name__ == '__main__':
    import os
    cwd = os.path.dirname(os.path.abspath(__file__))
    gen_doc_obj = GenDpRequirementDoc(cwd + '\\mc_config.xml',cwd + '\\DP.docx')
    gen_doc_obj.gen_dp_doc()
    # mc_table_obj = McTable(cwd + '\\1156.xlsm')
    # mc_table_obj.read_all_table_data()
    # dp_config = GenMcDpConfig(cwd + '\\mc_THD88_双界面_without_MSD.xml',mc_table_obj)
    # dp_config.save(cwd + '\\mc_THD88_双界面_without_MSD_copy.xml')
    # mc_table_obj.print_unused_data()