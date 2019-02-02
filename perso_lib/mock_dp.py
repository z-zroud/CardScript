# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 请在DP处理模块中进行处理
import importlib
import os
import shutil
from perso_lib.cps import Cps,Dgi
from perso_lib import algorithm
from perso_lib import utils
from perso_lib.kms import Kms
from perso_lib.xml_parse import XmlParser,XmlMode
from perso_lib.word import Docx
from perso_lib.file_handle import FileHandle
from perso_lib.excel import ExcelMode,ExcelOp
from enum import Enum
from xml.dom import Node
import logging


card_bin = '' #由于生成的模板无法获取具体的bin号，在此处需要手动设置

class CertConfig:
    rsa = ''
    expireDate = ''
    expireDateType = 'file'

cert_config = CertConfig()

alias_count = 0
def get_alias():
    global alias_count
    alias_count += 1
    return 'alias' + str(alias_count)


class DataType(Enum):
    FCI = 0
    SHARED = 1
    CONTACT = 2
    CONTACTLESS = 3
    MCA = 4
    MAGSTRIPE = 5

class DataItem:
    def __init__(self):
        self.name = ''      #按1156表定义，为tag的描述信息
        self.tag = ''
        self.len = ''
        self.value = ''
        self.data_type = None   #根据1156表分类
        self.used = False   #设置是否已被个人化

class VisaForm:
    def __init__(self,table_name):
        self.excel = ExcelOp(table_name)
        self.data_list = []
        
    def get_data(self,tag,data_type,desc=None):
        for item in self.data_list:
            if item.data_type == data_type and item.tag == tag:
                item.used = True
                return item.value
        return None

    def _get_data(self,data_type,start_row,start_col,ignore_list=None,end_flag=None):
        for row in range(start_row,200):
            text = self.excel.read_cell_value(row,start_col)
            if text and end_flag and text in end_flag:
                break
            item = DataItem()
            item.data_type = data_type
            item.name = self.excel.read_cell_value(row,start_col + 1)
            if not item.name:
                break
            item.tag = self.excel.read_cell_value(row,start_col + 2)
            if ignore_list and item.tag in ignore_list:
                continue    #模板直接忽略
            item.len = self.excel.read_cell_value(row,start_col + 3)
            item.value = self.excel.read_cell_value(row,start_col + 5)
            if item.value:
                item.tag = str(item.tag)
                print(str(item.data_type) + '||' + item.tag + '||' + item.name)
                self.data_list.append(item)
                if item.tag == '84':
                    item4F = item
                    item4F.tag = '4F'
                    self.data_list.append(item4F)
        return self.data_list

    def read_data(self,sheet_name='Visa(Paywave)',start_row=3,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Data Type':
                print('can not found form start position')
                return None
            start_row += 1
            self._get_data(DataType.CONTACT,start_row,start_col,None,'Visa payWave')
            for start_row in range(start_row,200):
                text = self.excel.read_cell_value(start_row,start_col)
                if text and 'Visa payWave' in text:
                    self._get_data(DataType.CONTACTLESS,start_row + 1,start_col)
                    break
        return self.data_list
            
class McForm:
    def __init__(self,tablename):
        self.excel = ExcelOp(tablename)
        self.data_list = []

    def _filter_data(self,data):
        if isinstance(data,int):
            return str(data)
        #过滤掉单引号，双引号和空格及None值
        if not data or data.strip() == 'NOT PRESENT' or data.strip() == 'N/A':
            return None 
        data = data.strip()
        if data[0] == '"' or data[0] == "'":
            data = data[1:len(data) - 1].strip()
        return data

    def _handle_tag_value(self,data):
        self_define_list = ['Determined by issuer','Data preparation']
        if data in self_define_list:
            return ''   #处理DP自定义数据
        if utils.is_hex_str(data):
            return data
        return utils.str_to_bcd(data)

    def print_unused_data(self):
        print('====================1156 form unused tag list====================')
        for item in self.data_list:
            if not item.used:
                #print(str(item.data_type) + '||' + item.tag + '||' + item.value + '||' + item.name)
                print("%-20s||%-10s||%-60s||%-100s" % (str(item.data_type),item.tag,item.value,item.name))

    def get_data(self,tag,data_type,desc=None):
        for item in self.data_list:
            if item.data_type == data_type and item.tag == tag:
                item.used = True
                return item.value
        return None
                
    def get_data_by_desc(self,desc,data_type):
        '''
        某些MCA数据没有标签一栏，可以通过desc描述找到对应的tag值，
        前提是模板中已经有对应的comment字符串
        '''
        for item in self.data_list:
            if item.data_type == data_type and item.name == desc:
                item.used = True
                return item.value
        return None

    def _get_data(self,data_type,start_row,start_col,ignore_list=None,end_flag=None):
        for row in range(start_row,200):
            item = DataItem()
            item.data_type = data_type
            item.name = self.excel.read_cell_value(row,start_col)
            item.name = self._filter_data(item.name)
            if not item.name:
                continue   
            if end_flag and end_flag in item.name:
                break
            else:
                if "All rights reserved" in item.name:
                    break   #说明已经遍历到了尽头

            item.tag = self.excel.read_cell_value(row,start_col + 1)
            if ignore_list and item.tag in ignore_list:
                continue    #模板直接忽略
            item.len = self.excel.read_cell_value(row,start_col + 2)
            item.value = self._filter_data(self.excel.read_cell_value(row,start_col + 3))
            if not item.value:
                continue    #过滤空值
            item.value = self._handle_tag_value(item.value)
            if item.name == 'Length Of ICC Public Key Modulus': #处理ICC公钥长度问题
                if item.value == '1152':
                    item.value = '90'
                elif item.value == '1024':
                    item.value = '80'
            if item.value:
                item.tag = str(item.tag)
                #print(str(item.data_type) + '||' + item.tag + '||' + item.value + '||' + item.name)
                print("%-20s||%-10s||%-60s||%-100s" % (str(item.data_type),item.tag,item.value,item.name))
                self.data_list.append(item)
                if item.tag == '84':
                    item4F = item
                    item4F.tag = '4F'
                    self.data_list.append(item4F)
        return self.data_list
    
    # 处理FCI数据
    def get_fci_data(self,sheet_name='FCI (1)',start_row=5,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Data object name':
                print('can not get fci header')
                return None
            start_row += 2
            ignore_template_list = ['6F','A5','BF0C']
            self.fci_data = self._get_data(DataType.FCI,start_row,start_col,ignore_template_list)
        return self.fci_data

    def get_mca_data(self,sheet_name='MCA data objects (1)',start_row=5,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Data object name':
                print('can not get fci header')
                return None
            start_row += 1
            self.mca_data = self._get_data(DataType.MCA,start_row,start_col)
        return self.mca_data

    def get_mag_data(self,sheet_name='Records (1)',start_row=5,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Contactless mag-stripe data':
                print('can not get mag header')
                return None
            start_row += 3
            self.mag_data = self._get_data(DataType.MAGSTRIPE,start_row,start_col + 2,None,'Data object name')
        return self.mag_data

    def get_contactless_data(self,sheet_name='Records (1)',start_row=18,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Contactless EMV data':
                print('can not get contactless header')
                return None
            start_row += 3
            self.contactless_data = self._get_data(DataType.CONTACTLESS,start_row,start_col + 2,None,'Data object name')
        return self.contactless_data

    def get_contact_data(self,sheet_name='Records (1)',start_row=43,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Contact EMV data':
                print('can not get contact header')
                return None
            start_row += 3
            self.contact_data = self._get_data(DataType.CONTACT,start_row,start_col + 2,None,'Data object name')
        return self.contact_data

    def get_shared_data(self,sheet_name='Records (1)',start_row=77,start_col=2):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Shared data':
                print('can not get fci header')
                return None
            start_row += 3
            self.shared_data = self._get_data(DataType.SHARED,start_row,start_col + 2)
        return self.shared_data
    
    def read_all_table_data(self):
        print('====================1156 form tag list====================')
        self.get_fci_data()
        self.get_mca_data()
        self.get_contact_data()
        self.get_contactless_data()
        self.get_mag_data()
        self.get_shared_data()
        return self.data_list


class GenDpDoc:
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

class EmbossItem:
    '''
    该类用于表示需要从emboss file文件中取值的tag结构
    tag 需要从文件中获取值的tag
    convert_to_ascii 是否需要转换为ASCII码
    value 一种描述取值方式的字符串,例如 "[10,20]001[12,33]"
    表示从emboss file中取位置10到20的字符串 + 固定字符串001 + 从emboss file取位置12到33的字符串
    '''
    def __init__(self,tag,convert_to_ascii,replace_equal_by_D,value):
        self.tag = tag
        self.convert_to_ascii = convert_to_ascii
        self.replace_equal_by_D = replace_equal_by_D
        self.value = value

class GenDpXml:
    def __init__(self,template_xml,data_items,emboss_items):
        self.template_xml = template_xml
        self.template_handle = XmlParser(template_xml)
        self.emboss_items = emboss_items
        self.data_items = data_items
        self.not_found_data = []

    def _get_emboss_item(self,tag):
        if self.emboss_items:
            for emboss_item in self.emboss_items:
                if emboss_item.tag == tag:
                    return emboss_item
        return None

    def _get_tag(self,tag='',source='',comment=''):
        '''
        从数据集data_items中查找对应的数据
        '''
        if tag and source:
            for item in self.data_items:
                if tag == item.tag and source == item.data_type.name.lower():
                    return item.value
        elif comment:
            for item in self.data_items:
                if item.name == comment:
                    return item.value
        else:
            return ""

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

    def _add_alias(self,xml_handle,tag_nodes):
        for index,tag_node in enumerate(tag_nodes):
            attr_tag = xml_handle.get_attribute(tag_node,'name')
            attr_value = xml_handle.get_attribute(tag_node,'value')
            attr_comment = xml_handle.get_attribute(tag_node,'comment') #将comment属性放到最后
            xml_handle.remove_attribute(tag_node,'comment')
            if attr_tag == '--':
                alias = get_alias()
                xml_handle.set_attribute(tag_node,'alias',alias)
                xml_handle.set_attribute(tag_node,'comment',attr_comment)
                continue
            for cur_index,cur_tag_node in enumerate(tag_nodes):
                if index != cur_index:
                    cur_tag = xml_handle.get_attribute(cur_tag_node,'name')
                    cur_attr_value = xml_handle.get_attribute(cur_tag_node,'value')
                    if cur_tag == attr_tag and attr_value != cur_attr_value:
                        alias = get_alias()
                        xml_handle.set_attribute(tag_node,'alias',alias)
                        xml_handle.set_attribute(tag_node,'comment',attr_comment)
                        break




    def gen_xml(self,new_xml,char_set='UTF-8'):
        tags_from_kms = ('8F','9F32','8000','8001','9000','9001','8400','8401','A006','A016','90','92','93','9F46','9F48','8201','8202','8203','8204','8205','DC','DD')
        fpath,_ = os.path.split(new_xml)    #分离文件名和路径
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        shutil.copyfile(self.template_xml,new_xml)      #复制文件
        new_xml_handle = XmlParser(new_xml, XmlMode.READ_WRITE)

        # 暂时只考虑一个应用
        app_node = new_xml_handle.get_first_node(new_xml_handle.root_element,'App')

        # 设置bin号
        global card_bin
        bin_node = new_xml_handle.get_first_node(new_xml_handle.root_element,'Bin')
        new_xml_handle.set_attribute(bin_node,'value',card_bin)

        #设置证书配置信息
        global cert_config
        cert_nodes = new_xml_handle.get_nodes(app_node,'Cert')
        for cert_node in cert_nodes:
            new_xml_handle.set_attribute(cert_node,'expireDate',cert_config.expireDate)
            new_xml_handle.set_attribute(cert_node,'expireDateType',cert_config.expireDateType)
            new_xml_handle.set_attribute(cert_node,'rsa',cert_config.rsa)

        # 生成数据
        tag_nodes = new_xml_handle.get_nodes(new_xml_handle.root_element,'Tag')
        for tag_node in tag_nodes:
            attr_tag = new_xml_handle.get_attribute(tag_node,'name')
            attr_source = new_xml_handle.get_attribute(tag_node,'source')
            attr_format = new_xml_handle.get_attribute(tag_node,'format')
            attr_comment = new_xml_handle.get_attribute(tag_node,'comment')
            attr_sig_id = new_xml_handle.get_attribute(tag_node,'sig_id')
            attr_value = new_xml_handle.get_attribute(tag_node,'value')
            # 删除之，重新给属性排序
            new_xml_handle.remove_attribute(tag_node,'name')
            new_xml_handle.remove_attribute(tag_node,'type')
            new_xml_handle.remove_attribute(tag_node,'comment')
            new_xml_handle.remove_attribute(tag_node,'format')
            new_xml_handle.remove_attribute(tag_node,'source')
            new_xml_handle.remove_attribute(tag_node,'sig_id')
            new_xml_handle.remove_attribute(tag_node,'value')
            
            value = ''
            if not attr_value:
                if attr_tag.strip() == '--':
                    value = self._get_tag(comment=attr_comment)
                else:
                    value = self._get_tag(tag=attr_tag, source=attr_source)
            else:
                value = attr_value
            # 重新排序
            new_xml_handle.set_attribute(tag_node,'name',attr_tag)

            if attr_tag in tags_from_kms:
                # 来自加密机, 优先处理从加密机里面的数据，不取来自客户表中数据
                new_xml_handle.set_attribute(tag_node,'type','kms')
            elif value and not self._get_emboss_item(attr_tag):
                #说明是固定值,并且不需要从文件中取
                new_xml_handle.set_attribute(tag_node,'type','fixed')
                new_xml_handle.set_attribute(tag_node,'value',value)
            else:
                # 来自文件
                new_xml_handle.set_attribute(tag_node,'type','file')
                item = self._get_emboss_item(attr_tag)
                if item:
                    new_xml_handle.set_attribute(tag_node,'value',item.value)
                    if item.convert_to_ascii:
                        new_xml_handle.set_attribute(tag_node,'convert_ascii','true')
                    if item.replace_equal_by_D:
                        new_xml_handle.set_attribute(tag_node,'replace_equal_by_D','true')
                else:
                    self.not_found_data.append((attr_tag,attr_source,attr_comment))
            if attr_sig_id:
                new_xml_handle.set_attribute(tag_node,'sig_id',attr_sig_id)
            new_xml_handle.set_attribute(tag_node,'format',attr_format)
            new_xml_handle.set_attribute(tag_node,'comment',attr_comment)
        self._add_alias(new_xml_handle,tag_nodes) #设置alias
        new_xml_handle.save(char_set)


class MockCps:
    '''
    根据xml配置文件及emboss file模拟生成CPS格式的测试卡数据
    '''
    def __init__(self,xml_file,emboss_file,process_emboss_file_module=None):
        self.cps = Cps()
        self.cps.dp_file_path = xml_file
        self.xml_handle = XmlParser(xml_file)
        self.process_emboss_file_module = process_emboss_file_module
        if emboss_file:
            self.emboss_file_handle = FileHandle(emboss_file,'r+')

    def _get_value(self,tag,data,vlaue_format):
        if vlaue_format == 'TLV':
            return utils.assemble_tlv(tag,data)
        else:
            return data

    def _get_date(self,date):
        if len(date) < 4:
            logging.info('len of date is too short')
            return None
        yy = date[0:2]
        mm = date[2:4]
        dd_flag = date[4:]
        if not yy.isdigit():
            logging.info('date of yy is incorrected format')
            return None
        if not mm.isdigit() or int(mm) > 12 or int(mm) == 0:
            logging.info('date of mm is incorrected format')
            return None
        if dd_flag == r'{FD}':
            return yy + mm + '01'
        if dd_flag == r'{LD}':
            if mm in ('01','03','05','07','08','10','12'):
                return yy + mm + '31'
            elif mm in ('04','06','09','11'):
                return yy + mm + '30'
            else:
                return yy + mm + '28'
        return None

    def _parse_pos_value(self,tag,value):
        data = ''
        index = 0
        while index < len(value):
            start_index = str(value).find('[',index)
            if start_index == -1:
                data += value[index:]
                break
            else:
                data += value[index:start_index]
            end_index = str(value).find(']',start_index)
            pos_str = value[start_index + 1:end_index]
            start_pos = int(pos_str.split(',')[0])
            end_pos = int(pos_str.split(',')[1])
            data += self.emboss_file_handle.read_pos(start_pos,end_pos)
            index = end_index + 1
        if tag in ('5F24','5F25') and (r'{FD}' in data or r'{LD}' in data):
            return self._get_date(data)
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
            value = self.xml_handle.get_attribute(tag_node,'value')
            if value:
                value = self._parse_pos_value(tag,value)
                replaceD = self.xml_handle.get_attribute(tag_node,'replace_equal_by_D')
                if replaceD:
                    value = value.replace('=','D')
                convert_ascii = self.xml_handle.get_attribute(tag_node,'convert_ascii')
                if convert_ascii and convert_ascii.lower() == 'true':
                    value = utils.str_to_bcd(value)
                if len(value) % 2 != 0:
                    value += 'F'
                value = self._get_value(tag,value,value_format)
            else:
                if self.process_emboss_file_module:
                    mod_obj = importlib.import_module(self.process_emboss_file_module)
                    if mod_obj:
                        if hasattr(mod_obj,'process_tag' + tag):
                            func = getattr(mod_obj,'process_tag' + tag)
                            value = self._get_value(tag,func(),value_format)
                        else:
                            print('can not process tag' + tag)
                else:
                    print('emboss file module can not process tag' + tag)
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
            tag_nodes = self.xml_handle.get_child_nodes(sig_node,'Tag')
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
        bin_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'Bin')
        if bin_node:
            issuer_bin = self.xml_handle.get_attribute(bin_node,'value')
            if not issuer_bin or issuer_bin == '':
                print('Please provide card Bin number, if not, card will use default Bin number:654321')
                issuer_bin = '654321'
            else:
                issuer_bin = issuer_bin.split(',')[0]    #取第一个bin号生成证书
        return issuer_bin

    def _get_rsa_len(self,app_node):
        rsa_len = 1024
        cert_node = self.xml_handle.get_first_node(app_node,'Cert')
        if cert_node:
            rsa_len_str = self.xml_handle.get_attribute(cert_node,'rsa')
            if not rsa_len_str or rsa_len_str == '':
                print('Please provide card ICC RSA length, if not, card will use default RSA len:1024')
            else:
                rsa_len = int(rsa_len_str)       
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
        if dgi.dgi == '0101' and dgi.is_existed('56') and dgi.is_existed('9F6B'):
            # 说明是MC应用，且支持MSD,这时需要生成对应的DC,DD
            tag56 = dgi.get_value('56')[4:] # 偷懒，不需要解析TLV
            tag9F6B = dgi.get_value('9F6B')[6:]
            kms.gen_mc_cvc3(tag56,tag9F6B)
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
            rsa_len = self._get_rsa_len(app_node)
            kms = Kms()
            kms.init(issuer_bin,rsa_len)
            self._process_signature(app_node,kms)
            dgi_nodes = self.xml_handle.get_child_nodes(app_node,"DGI")
            for dgi_node in dgi_nodes:
                dgi = self._process_dgi(dgi_node,kms)
                if count > 1:
                    dgi.dgi = dgi.dgi + '_' + str(count)
                self.cps.add_dgi(dgi)
            kms.close()
        # 处理PSE 和 PPSE
        pse_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'PSE')
        pse_dgi = self._process_pse(pse_node)
        self.cps.add_dgi(pse_dgi)
        ppse_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'PPSE')
        ppse_dgi = self._process_pse(ppse_node)
        self.cps.add_dgi(ppse_dgi)
        return self.cps

