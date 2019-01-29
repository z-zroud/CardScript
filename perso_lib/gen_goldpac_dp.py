# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 请在DP处理模块中进行处理
from perso_lib.cps import Cps,Dgi
from perso_lib import des
from perso_lib import sm
from perso_lib import utils
from perso_lib.kms import Kms
from perso_lib.xml_parse import XmlParser
from xml.dom import Node
import importlib

class GenGoldpacDpRule:
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

    def _get_bin(self):
        issuer_bin = ''
        bin_nodes = self.xml_handle.get_nodes(self.xml_handle.root_element,'Common')
        if len(bin_nodes) > 0:
            issuer_bin = self.xml_handle.get_attribute(bin_nodes[0],'bin')
            if issuer_bin is None or issuer_bin == '':
                print('Please provide card Bin number, if not, card will use default Bin number:654321')
                issuer_bin = '654321'
        return issuer_bin

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

    def parse(self):
        app_nodes = self.xml_handle.get_nodes(self.xml_handle.root_element,'App')
        count = 0
        for app_node in app_nodes:
            count += 1
            issuer_bin = self._get_bin()
            kms = Kms()
            kms.init(issuer_bin)
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
