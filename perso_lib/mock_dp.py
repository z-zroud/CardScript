# 该仅对通用的规则进行转换，对于DP中特殊的处理
# 请在DP处理模块中进行处理
import importlib
import os
import shutil
import logging
from perso_lib.cps import Cps,Dgi
from perso_lib import algorithm
from perso_lib import utils
from perso_lib.kms import Kms
from perso_lib.xml_parse import XmlParser,XmlMode
from perso_lib.word import Docx
from perso_lib.file_handle import FileHandle
from perso_lib.excel import ExcelMode,ExcelOp
from perso_lib import settings
from enum import Enum
from xml.dom import Node


alias_count = 0
def get_alias():
    global alias_count
    alias_count += 1
    return 'alias' + str(alias_count)


# 定义数据类型枚举
class DataType(Enum):
    FCI         = 0     #MC 专用
    SHARED      = 1     #MC 专用
    CONTACT     = 2
    CONTACTLESS = 3
    MCA         = 4     #MC 专用
    MAGSTRIPE   = 5     #MC 专用

class AppType(Enum):
    VISA_DEBIT  = 'VISA_DEBIT'  #VISA 借记
    VISA_CREDIT = 'VISA_CREDIT' #VISA 贷记
    MC_DEBIT    = 'MC_DEBIT'    #MC 借记
    MC_CREDIT   = 'MC_CREDIT'   #MC 贷记
    UICS_DEBIT  = 'UICS_DEBIT'  #UICS 借记
    UICS_CREDIT = 'UICS_CREDIT' #UICS 贷记
    JETCO       = 'JETCO'       #JETCO

# 该类描述了来源数据的结构呈现形式
class SourceItem:
    def __init__(self):
        self.name = ''      #tag的英文名称
        self.tag = ''       #tag标签
        self.len = ''       #tag长度
        self.value = ''     #tag值
        self.source_type = None   #标识数据值的来源,fixed,file,kms
        self.data_type = None #tag数据类型,由DataType定义
        self.used = False   #个人化时，是否被使用到

# 描述了从emboss file文件中获取的tag标签信息
class EmbossItem:
    '''
    该类用于表示需要从emboss file文件中取值的tag结构
    tag 需要从文件中获取值的tag
    convert_to_ascii 是否需要转换为ASCII码
    value 一种描述取值方式的字符串,例如 "[10,20]001[12,33]"
    表示从emboss file中取位置10到20的字符串 + 固定字符串001 + 从emboss file取位置12到33的字符串
    '''
    def __init__(self,convert_to_ascii,replace_equal_by_D,value):
        self.convert_to_ascii = convert_to_ascii
        self.replace_equal_by_D = replace_equal_by_D
        self.value = value

# 港澳地区专用的纯Jetco应用Excel表格
class JetcoForm:
    def __init__(self,ca_file,issuer_file,ic_pk_file,ic_private_file,excel_file):
        self.ca_file = ca_file
        self.issuer_file = issuer_file
        self.ic_pk_file = ic_pk_file
        self.ic_private_file = ic_private_file
        self.excel_file = excel_file
        self.ca_pk_len = 0
        self.excel = ExcelOp(excel_file)
        self.data_list = []

    def set_mdk(self,mdk_ac,mdk_mac,mdk_enc):
        self.mdk_ac = mdk_ac
        self.mdk_mac = mdk_mac
        self.mdk_enc = mdk_enc

    def read_data(self,title_list,card_no):
        self.read_excel_data(title_list,card_no)
        self.read_cert_data()
        app_key = self.gen_8000(self.mdk_ac,self.mdk_mac,self.mdk_enc)
        self.gen_9000(app_key)
        return self.data_list

    def gen_8000(self,mdk_ac,mdk_mac,mdk_enc):
        tag5A = ''
        tag5F34 = ''
        for item in self.data_list:
            if item.tag == '5A':
                tag5A = item.value
            if item.tag == '5F34':
                tag5F34 = item.value
        tag8000 = algorithm.gen_app_key(mdk_ac,mdk_mac,mdk_enc,tag5A,tag5F34)
        data_item = SourceItem()
        data_item.tag = '8000'
        data_item.value = tag8000
        data_item.data_type = DataType.CONTACT
        self.data_list.append(data_item)
        return tag8000

    def gen_9000(self,tag8000):
        tag9000 = algorithm.gen_app_key_kcv(tag8000)
        data_item = SourceItem()
        data_item.tag = '9000'
        data_item.value = tag9000
        data_item.data_type = DataType.CONTACT
        self.data_list.append(data_item)
        return tag9000

    def read_excel_data(self,title_list,card_no,sheet_name='Sheet1',start_row=4,start_col=1):
        if self.excel.open_worksheet(sheet_name):
            has_find = False
            for row in range(start_row,200):
                data = self.excel.read_cell_value(row,title_list[0][1])
                if data == card_no:
                        has_find = True
                        start_row = row
                        break
            if has_find:
                title_list = title_list[1:]
                for title in title_list:
                    data = self.excel.read_cell_value(start_row,title[1])
                    if data:
                        data = data.strip()
                        if data == 'Empty':
                            data = ''
                        if title[0] == '5A' and len(data) % 2 != 0:
                            data = data + 'F'
                        item = SourceItem()
                        item.data_type = DataType.CONTACT
                        item.tag = title[0]
                        item.value = data
                        self.data_list.append(item)
        return self.data_list
        
    def read_cert_data(self):
        tag_value_list = []
        tag_value_list += self._handle_ca_file()
        tag_value_list += self._handle_issuer_file()
        tag_value_list += self._handle_ic_private_file()
        tag_value_list += self._handle_ic_pk_file()
        for item in tag_value_list:
            data_item = SourceItem()
            data_item.data_type = DataType.CONTACT
            data_item.tag = item[0]
            data_item.value = item[1]
            self.data_list.append(data_item)

    
    def _handle_ic_private_file(self):
        fh = FileHandle(self.ic_private_file,'rb+')
        head = fh.read_binary(fh.current_offset, 33)
        data_list = []
        while not fh.EOF:
            flag = fh.read_binary(fh.current_offset,1)
            if flag != '02':
                print('read ic private file failed.')
                return
            data_len = fh.read_binary(fh.current_offset,1)
            if data_len == '81':
                data_len = fh.read_binary(fh.current_offset,1)
            data_len = utils.hex_str_to_int(data_len)
            data = fh.read_binary(fh.current_offset,data_len)
            if data[0:2] == '00': #凭经验，此处若为00，表示多余的一个字节
                data = data[2:]
            data_list.append(data)
        tag_values = []
        tag_values.append(('8201',data_list[7]))
        tag_values.append(('8202',data_list[6]))
        tag_values.append(('8203',data_list[5]))
        tag_values.append(('8204',data_list[4]))
        tag_values.append(('8205',data_list[3]))
        return tag_values

    def _handle_ic_pk_file(self):
        fh = FileHandle(self.ic_pk_file,'rb+')
        head = fh.read_binary(fh.current_offset, 1)
        pan = fh.read_binary(fh.current_offset, 10)  
        sn = fh.read_binary(fh.current_offset, 3)
        expirate_date = fh.read_binary(fh.current_offset, 2)
        icc_remainder_len = fh.read_short(fh.current_offset)
        icc_remainder = fh.read_binary(fh.current_offset,icc_remainder_len)
        exp_len = fh.read_short(fh.current_offset)
        exp = fh.read_binary(fh.current_offset,exp_len)
        icc_pk_len = fh.file_size - fh.current_offset
        icc_pk = fh.read_binary(fh.current_offset,icc_pk_len)
        tag_values = []
        tag_values.append(('9F46',icc_pk))
        tag_values.append(('9F47',exp))
        tag_values.append(('9F48',icc_remainder))
        logging.info("9F46:" + icc_pk)
        logging.info("9F47:" + exp)
        logging.info("9F48:" + icc_remainder)
        return tag_values

    def _handle_issuer_file(self):
        fh = FileHandle(self.issuer_file,'rb+')
        head = fh.read_binary(fh.current_offset, 1)
        service_ident = fh.read_binary(fh.current_offset,4)
        issuer_ident = fh.read_binary(fh.current_offset,4)
        sn = fh.read_binary(fh.current_offset,3)
        expirate_date = fh.read_binary(fh.current_offset, 2)
        issuer_remainder_len = fh.read_short(fh.current_offset)
        issuer_remainder = fh.read_binary(fh.current_offset,issuer_remainder_len)
        exp_len = fh.read_short(fh.current_offset)
        exp = fh.read_binary(fh.current_offset,exp_len)
        ca_pk_index = fh.read_binary(fh.current_offset,1)
        issuer_pk = fh.read_binary(fh.current_offset,self.ca_pk_len)
        other_len = fh.file_size - fh.current_offset
        other = fh.read_binary(fh.current_offset,other_len)
        tag_values = []
        tag_values.append(('90',issuer_pk))
        tag_values.append(('92',issuer_remainder))
        tag_values.append(('9F32',exp))
        logging.info("90:" + issuer_pk)
        logging.info("92:" + issuer_remainder)
        logging.info("9F32:" + exp)
        return tag_values       


    def _handle_ca_file(self):
        fh = FileHandle(self.ca_file,'rb+')
        head = fh.read_binary(fh.current_offset, 1)
        service_ident = fh.read_binary(fh.current_offset,4)
        self.ca_pk_len = fh.read_int(fh.current_offset)
        algo = fh.read_binary(fh.current_offset,1)
        exp_len = int(fh.read_binary(fh.current_offset,1))
        rid = fh.read_binary(fh.current_offset,5)
        ca_index = fh.read_binary(fh.current_offset,1)
        ca_pk_mod = fh.read_binary(fh.current_offset,self.ca_pk_len)
        exp = fh.read_binary(fh.current_offset,exp_len)
        tag_values = []
        # tag_values.append(('8F',ca_index))
        logging.info('ca_mod: ' + ca_pk_mod)
        logging.info('ca_exp: ' + exp)
        return tag_values

# 金邦达专用定义的Excel表格
class GoldpacForm:
    def __init__(self,form_name):
        self.excel = ExcelOp(form_name)
        self.source_items = []
        
    def get_data(self,tag,data_type,desc=None):
        for item in self.source_items:
            if item.data_type == data_type and item.tag == tag:
                item.used = True
                return item.value
        return None
    
    def _get_data(self,row,col,ignore_list=None):
        # 列名分别是:Data Type,Name,Tag,Length,recommended value,Issuer settings,data source,remarks
        source_item = SourceItem()
        source_item.name = self.excel.read_cell_value(row,col + 1)    #Name
        source_item.tag = self.excel.read_cell_value(row,col + 2)    #Tag
        # if ignore_list and source_item.tag in ignore_list:
        #     continue    #模板直接忽略
        source_item.len = self.excel.read_cell_value(row,col + 3)     # 长度(字符串)
        source_item.value = self.excel.read_cell_value(row,col + 5)   # Issuer settings
        source_item.source_type = self.excel.read_cell_value(row,col + 6) # file,kms,fixed
        if source_item.tag:
            source_item.tag = str(source_item.tag) #有些可能读表格时，默认是int类型，需要转str
            if 'Contactless' in source_item.tag:# Tag列可能是'Tag-Contactless'形式的字符串
                source_item.tag = source_item.tag.split('-')[0].strip()
                source_item.data_type = DataType.CONTACTLESS
            else:
                source_item.data_type = DataType.CONTACT #自主Excel表格，仅包含CONTACT和CONTACTLESS类型
        if source_item.value:
            # 过滤掉空格和换行符
            source_item.value = str(source_item.value)
            source_item.value = source_item.value.replace(' ','').replace('\n','')
            if source_item.value != 'N.A':
                if source_item.source_type == 'Fixed':
                    source_item.source_type = 'fixed'   #保持和模板xml中的type一致
                    if source_item.value.lower() == 'empty':
                        source_item.value = 'empty' #如果为empty,也需要个人化此tag
                    elif not utils.is_hex_str(source_item.value): #此时认为是不合规的值
                        logging.info('parse tag %s error: value is incorrect format',source_item.tag)
                        source_item.value = None
                elif source_item.source_type == 'Emboss File':
                    source_item.source_type = 'file'
                elif source_item.source_type == 'Kms':
                    source_item.source_type = 'kms'
                    source_item.value = 'kms'
        if source_item.value is not None and source_item.tag:   #确保tag和value都存在
            return source_item
        return None

    def read_data(self,sheet_name,start_row=5,start_col=2):
        self.source_items.clear() #读数据前，将旧数据清空
        if self.excel.open_worksheet(sheet_name):
            first_header = self.excel.read_cell_value(start_row,start_col)
            if str(first_header).strip() != 'Data Type':
                print('can not found form start position')
                return None
            start_row += 1 #默认标题行之后就是数据行
            for row in range(start_row,200):
                item = self._get_data(row,start_col)    #获取每行数据，组成一个SourceItem对象
                if item:
                    self.source_items.append(item)
        return self.source_items[:]


class McForm:
    def __init__(self,xml_name):
        self.source_items = []
        self.xml_handle = XmlParser(xml_name,XmlMode.READ)

    def read_data(self):
        worksheet_nodes = self.xml_handle.get_child_nodes(self.xml_handle.root_element,'WORKSHEET')
        for worksheet_node in worksheet_nodes:
            worksheet_name = self.xml_handle.get_attribute(worksheet_node,'NAME')
            ws_child_nodes = self.xml_handle.get_child_nodes(worksheet_node)
            for child_node in ws_child_nodes:
                item = SourceItem()
                item.name = self.xml_handle.get_attribute(child_node,'NAME')
                item.tag = self.xml_handle.get_attribute(child_node,'TAG')
                if item.tag == '':
                    item.tag = '--'
                item.value = self.xml_handle.get_attribute(child_node,'VALUE')
                if worksheet_name == 'fci':
                    item.data_type = DataType.FCI
                elif worksheet_name == 'internal':
                    item.data_type = DataType.MCA
                elif worksheet_name == 'recordcontact':
                    item.data_type = DataType.CONTACT
                elif worksheet_name == 'recordcontactless':
                    item.data_type = DataType.CONTACTLESS
                else:
                    logging.info('Unkonwn worksheet name.')
                self.source_items.append(item)
        return self.source_items

# 万事达1156表格专用类            
class Form1156:
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
                print("%-20s||%-10s||%-60s||%-100s" % (item.data_type.name,item.tag,item.value,item.name))

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
            item = SourceItem()
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
    
    def read_data(self):
        print('====================1156 form tag list====================')
        self.get_fci_data()
        self.get_mca_data()
        self.get_contact_data()
        self.get_contactless_data()
        self.get_mag_data()
        self.get_shared_data()
        return self.data_list

# 根据dp xml文件生成Word文档DP需求
class GenDpDoc:
    def __init__(self,dp_xml,dp_docx):
        self.dp_xml = dp_xml    #DP xml配置文件
        self.dp_docx = dp_docx
        cwd = os.path.dirname(__file__)
        dp_docx_template = os.path.join(cwd,'template','DpRequirement.docx')
        self.docx = Docx(dp_docx_template)
        self.xml_handle = XmlParser(dp_xml,XmlMode.READ)

    def _get_deep_template_count(self,dgi_node):
        '''
        获取DGI节点中最深模板的个数，用于确定表格需要创建多少列
        '''
        if not dgi_node:
            return 0
        children_nodes = self.xml_handle.get_child_nodes(dgi_node,'Template')
        if not children_nodes:
            return 0
        return 1 + max(self._get_deep_template_count(child) for child in children_nodes)

    def _get_template_child_tags_count(self,template_node):
        '''
        获取模板中Tag子节点的个数
        '''
        tag_nodes = self.xml_handle.get_child_nodes(template_node,'Tag')
        if tag_nodes:
            return len(tag_nodes)
        return 0

    def _get_node_level(self,root_node,child_node):
        level = 0
        parent = self.xml_handle.get_parent(child_node)
        while parent and parent != root_node:
            parent = self.xml_handle.get_parent(parent)
            level += 1
        return level

    def _get_children_nodes(self,parent_node):
        '''
        获取父节点下的所有子节点
        '''
        children_nodes = self.xml_handle.get_child_nodes(parent_node)
        for child_node in children_nodes[:]:
            # print(self.xml_handle.get_attribute(child_node,'name'))
            children_nodes.extend(self._get_children_nodes(child_node))
        return children_nodes

    def _create_table(self,dgi_node):
        # 若DGI包含70模板，则不将70模板包含到表格中(过滤70模板)
        dgi_child_nodes = self.xml_handle.get_child_nodes(dgi_node)
        if dgi_child_nodes and len(dgi_child_nodes) == 1:
            name = self.xml_handle.get_attribute(dgi_child_nodes[0],'name')
            if name and name == '70': 
                dgi_node = dgi_child_nodes[0]
        col_count = self._get_deep_template_count(dgi_node) + 4
        new_table = self.docx.add_table(1,col_count)
        # 设置表格标题栏
        title = ['' for empty in range(col_count - 4)] + ['标签','数据元','长度','值']
        for col in range(col_count): #设置表格头部栏
            cell = self.docx.get_cell(new_table,0,col)
            self.docx.set_cell_background(cell,'FFCA00')
            self.docx.set_cell_text(cell,title[col])
        # 如果包含非70模板，需要合并标题栏中的Tag列
        if col_count > 4:
            cells = []
            for col in range(col_count - 3):
                cells.append(self.docx.get_cell(new_table,0,col))
            self.docx.merge_cell(cells)
        # 设置表格中每个单元格的内容
        # 设置每个tag标签
        dgi_child_nodes = self._get_children_nodes(dgi_node)
        for tag_node in dgi_child_nodes:
            tag_name = self.xml_handle.get_attribute(tag_node,'name')
            tag_value = self.xml_handle.get_attribute(tag_node,'value')
            tag_type = self.xml_handle.get_attribute(tag_node,'type')
            if not tag_value:
                tag_value = ''
            if tag_type == 'kms':
                tag_value = 'From KMS'
            tag_comment = self.xml_handle.get_attribute(tag_node,'comment')
            if not tag_comment:
                tag_comment = ''
            new_row = new_table.add_row()
            level = self._get_node_level(dgi_node,tag_node)
            self.docx.set_cell_text(new_row.cells[level],tag_name)
            self.docx.set_cell_text(new_row.cells[-3],tag_comment) #数据元在倒数第3列描述
            if tag_value and utils.is_hex_str(tag_value):
                self.docx.set_cell_text(new_row.cells[-2],utils.get_strlen(tag_value))
            else:
                self.docx.set_cell_text(new_row.cells[-2],'var') #长度在倒数第2列描述
            self.docx.set_cell_text(new_row.cells[-1],tag_value) #值为最后一列

    def gen_dp_docx(self):
        app_maps = {
            'A0000000041010':'MC Advance 应用分组',
            '315041592E5359532E4444463031':'PSE应用分组',
            '325041592E5359532E4444463031':'PPSE应用分组',
            'A000000333010101':'UICS/PBOC 借记应用分组',
            'A000000333010102':'UICS/PBOC 贷记应用分组',
            'A0000000031010':'Visa 应用分组',
            'A00000047400000001':'Jetco 应用分组',
        }
        app_nodes = self.xml_handle.get_child_nodes(self.xml_handle.root_element,'App')
        pse_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'PSE')
        ppse_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'PPSE')
        if pse_node:
            app_nodes.append(pse_node)
        if ppse_node:
            app_nodes.append(ppse_node)
        for app_node in app_nodes:
            # 添加应用分组标题
            aid = self.xml_handle.get_attribute(app_node,'aid')
            self.docx.add_heading(2,app_maps.get(aid,'应用分组'))
            # 设置每个应用的DGI分组
            dgi_nodes = self.xml_handle.get_child_nodes(app_node,'DGI')
            for dgi_node in dgi_nodes:
                dgi_name = self.xml_handle.get_attribute(dgi_node,'name')
                dgi_comment = self.xml_handle.get_attribute(dgi_node,'comment')
                dgi_title = 'DGI-{0}:{1}'.format(dgi_name,dgi_comment)
                template70_node = self.xml_handle.get_first_node(dgi_node,'Template')
                if template70_node:
                    name = self.xml_handle.get_attribute(template70_node,'name')
                    if name == '70':
                        dgi_title = '[需添加70模板]' + dgi_title
                self.docx.add_heading(3,dgi_title)
                self._create_table(dgi_node)
            self.docx.save_as(self.dp_docx)


class DpTemplateXml():
    def __init__(self,app_type='',name=''):
        self.app_type = app_type
        self.name = name

# 根据xml模板、Excel表格中的数据、emboss file中的数据生成DP XML配置文件
class GenDpXml:
    config = dict() #一个类属性字典，用于自定义配置
    def __init__(self,template_xml,source_items,second_source_items=None,emboss_items=None):
        # 支持默认DP模板配置和自定义模板
        if isinstance(template_xml,DpTemplateXml):
            cwd = os.path.dirname(__file__)
            template_xml_path = os.path.join(cwd,'template',template_xml.app_type.lower(),template_xml.name)
            self.template_xml = template_xml_path
        else:
            self.template_xml = template_xml # 自定义模板
        self.template_handle = XmlParser(self.template_xml)
        if emboss_items:
            self.emboss_items = emboss_items # 文件中的数据集
        else:
            self.emboss_items = dict()
        self.source_items = source_items # 第一应用数据集
        self.second_source_items = second_source_items # 第二应用下的数据
        self.cur_source_items = self.source_items # 表示当前应用使用的数据集
        self.unused_data = []
        self.first_app_aid = ''
        self.second_app_aid = ''
        self._init_emboss_items()
        
    def _parse_file_value(self,value):
        emboss_item = EmbossItem(False,False,'')
        item = value.split('-')
        if not item:
            return None
        else:
            emboss_item.value = item[0]
            for data in item[1:]:
                if data.strip() == 'ASCII':
                    emboss_item.convert_to_ascii = True
                if data.strip() == 'EQ':
                    emboss_item.replace_equal_by_D = True
        return emboss_item
        
    def _init_emboss_items(self):
        app_items = self.source_items[:]
        if self.second_source_items:
            app_items.extend(self.second_source_items)
        for item in app_items:
            if item.source_type == 'file':
                emboss_item = self._parse_file_value(item.value)
                if emboss_item:
                    self.emboss_items.setdefault(item.tag,emboss_item)
                    item.value = ''


    def _set_app_info(self,xml_handle,app_nodes):
        '''
        存储双应用信息
        '''
        for index, app_node in enumerate(app_nodes):
            aid = xml_handle.get_attribute(app_node,'aid')
            if index == 0:
                self.first_app_aid = aid
            else:
                self.second_app_aid = aid

    def _is_second_app(self,xml_handle,app_node):
        '''
        判断当前应用是否为第二应用
        '''
        aid = xml_handle.get_attribute(app_node,'aid')
        return aid == self.second_app_aid

    def _get_source_item(self,tag='',source='',comment=''):
        '''
        从数据集cur_source_items中查找对应的数据
        '''
        if tag and source:  # 根据模板xml中的tag和type来查找数据
            for item in self.cur_source_items:
                if tag == item.tag and source == item.data_type.name.lower():
                    return item
        elif comment:   #有时候需要根据模板xml中的comment来查找tag数据
            for item in self.cur_source_items:
                if item.name == comment:
                    return item
        return None

    def _get_value(self,tag='',source='',comment=''):
        item = self._get_source_item(tag,source,comment)
        if item:
            item.used = True
            return item.value
        return None


    def print_template_unused(self):
        logging.info('no used tag list at first application----------------------------')
        for item in self.source_items:
            if not item.used:
                logging.info("tag:{0:6s} |value:{1:30s}|".format(item.tag,item.value))
        if self.second_source_items:
            logging.info('no used tag list at second application----------------------------')
            for item in self.second_source_items:
                if not item.used:
                    logging.info("tag:{0:6s} |value:{1:30s}|".format(item.tag,item.value))
        logging.info('no used tag list at template----------------------------')
        ignore_tag_list = ['8000','8001','9000','9001','A006','A016','8401','8400','8201','8202','8203','8204','8205']
        for data in self.unused_data:
            if data[0] not in ignore_tag_list:
                logging.info("tag:{0:6s} |source:{1:30s}|".format(data[0],data[1]))        

    def _add_alias(self,xml_handle,tag_nodes):
        '''
        给重复的tag添加别名(唯一的ID名称)，例如tag为--或其他重复tag
        '''
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
            has_diff_value_at_prev_section = False
            for cur_index,cur_tag_node in enumerate(tag_nodes):
                cur_tag = xml_handle.get_attribute(cur_tag_node,'name')
                cur_attr_value = xml_handle.get_attribute(cur_tag_node,'value')
                if has_diff_value_at_prev_section and index <= cur_index:
                    has_diff_value_at_prev_section = False # 重置该标记
                    # 如果上半区遍历完
                    alias = xml_handle.get_attribute(cur_tag_node,'alias')
                    if not alias: # 若不存在相同值的tag,才增加别名，若存在相同的值，这alias肯定已经赋值了
                        alias = get_alias()
                        xml_handle.set_attribute(tag_node,'alias',alias)
                        xml_handle.set_attribute(tag_node,'comment',attr_comment)
                        break
                if cur_tag == attr_tag:
                    if index > cur_index:  # 搜寻此tag上半区的Tag节点
                        if attr_value == cur_attr_value: #若发现有值相同的tag,若存在别名，取该别名
                            cur_attr_alias = xml_handle.get_attribute(cur_tag_node,'alias')
                            if cur_attr_alias:
                                xml_handle.set_attribute(tag_node,'alias',cur_attr_alias)
                                xml_handle.set_attribute(tag_node,'comment',attr_comment)
                                break
                        else: #若发现不同的值，需要先做个标记，等上半区遍历完再下结论
                            has_diff_value_at_prev_section = True
                        # xml_handle.set_attribute(tag_node,'comment',attr_comment)
                    elif index < cur_index: #搜寻此tag下半区的Tag节点
                        if attr_value != cur_attr_value: 
                            alias = get_alias()
                            xml_handle.set_attribute(tag_node,'alias',alias)
                            xml_handle.set_attribute(tag_node,'comment',attr_comment)
                            break 
                    else:
                        xml_handle.set_attribute(tag_node,'comment',attr_comment)

    def _delete_empty_template(self,new_xml_handle,parent_node):
        '''
        如果模板节点下面没有tag节点，则需要删除该模板节点
        '''
        child_template_nodes = new_xml_handle.get_child_nodes(parent_node,'Template')
        for child_template_node in child_template_nodes: #同级的template
            tag_nodes = new_xml_handle.get_child_nodes(child_template_node,'Tag')
            if not tag_nodes:
                new_xml_handle.remove(child_template_node)
            else:
                self._delete_empty_template(new_xml_handle,child_template_node)

    def remove_empty_node(self,new_xml_handle):
        app_nodes = new_xml_handle.get_child_nodes(new_xml_handle.root_element,'App')
        for app_node in app_nodes:
            dgi_nodes = new_xml_handle.get_child_nodes(app_node,'DGI')
            for dgi_node in dgi_nodes:
                self._delete_empty_template(new_xml_handle,dgi_node)
                dgi_child_nodes = new_xml_handle.get_child_nodes(dgi_node)
                if not dgi_child_nodes:
                    dgi_name = new_xml_handle.get_attribute(dgi_node,'name')
                    new_xml_handle.remove(dgi_node)
                    logging.info('Remove DGI: %s',dgi_name)

    def _handle_9F4B(self,new_xml_handle,app_node):
        dgi_for_tag9F4B = int(self.config.get('dgi_9F4B'),16)
        dgi_nodes = new_xml_handle.get_nodes(app_node,'DGI')
        before_node = None
        for dgi_node in dgi_nodes:
            dgi_name = new_xml_handle.get_attribute(dgi_node,'name')
            if dgi_name and utils.is_hex_str(dgi_name):
                int_dgi = int(dgi_name,16)
                if int_dgi < dgi_for_tag9F4B:
                    before_node = dgi_node
                else:
                    new_node = new_xml_handle.create_node('DGI')
                    new_xml_handle.set_attribute(new_node,'name',self.config.get('dgi_9F4B'))
                    attr = dict()
                    attr['name'] = 'FFFF'
                    attr['format'] = 'V'
                    attr['type'] = 'fixed'
                    rsa = int(self.config.get('rsa'))
                    str_rsa = utils.int_to_hex_str(rsa // 8)
                    str_rsa = '9F4B81' + str_rsa
                    str_tlv_len = utils.int_to_hex_str(rsa // 8 + 4)
                    value = '7081' + str_tlv_len + str_rsa
                    attr['value'] = value
                    new_xml_handle.add_node(new_node,'Tag',**attr)
                    new_xml_handle.insert_before(app_node,new_node,before_node)     
                    break  

    def gen_xml(self,new_xml,char_set='UTF-8'):
        tags_from_kms = ('8F','9F32','8000','8001','9000','9001','8400','8401','A006','A016','90','92','93','9F46','9F48','8201','8202','8203','8204','8205','DC','DD')
        fpath,_ = os.path.split(new_xml)    #分离文件名和路径
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        shutil.copyfile(self.template_xml,new_xml)      #复制文件
        new_xml_handle = XmlParser(new_xml, XmlMode.READ_WRITE)

        # 设置应用节点属性
        app_nodes = new_xml_handle.get_child_nodes(new_xml_handle.root_element,'App')
        self._set_app_info(new_xml_handle,app_nodes)
        if app_nodes:
            new_xml_handle.set_attribute(app_nodes[0],'type',self.config.get('app_type').name.lower())
            if len(app_nodes) == 2: #支持双应用
                new_xml_handle.set_attribute(app_nodes[1],'type',self.config.get('second_app_type').name.lower())

        # 设置bin号
        bin_node = new_xml_handle.get_first_node(new_xml_handle.root_element,'Bin')
        if bin_node:
            new_xml_handle.set_attribute(bin_node,'value',self.config.get('card_bin','123456'))

        # 将pse,ppse节点也加入到app节点集合中，设置tag属性
        pse_node = new_xml_handle.get_first_node(new_xml_handle.root_element,'PSE')
        ppse_node = new_xml_handle.get_first_node(new_xml_handle.root_element,'PPSE')
        if pse_node: #防止特殊应用,没有pse或ppse节点的情况
            app_nodes.append(pse_node)
        if ppse_node:
            app_nodes.append(ppse_node)

        # 设置Tag节点
        for index, app_node in enumerate(app_nodes):
            aid = new_xml_handle.get_attribute(app_node,'aid')
            if aid not in ('315041592E5359532E4444463031','325041592E5359532E4444463031'):
                #设置证书配置信息
                cert_nodes = new_xml_handle.get_nodes(app_node,'Cert')
                if cert_nodes:
                    for cert_node in cert_nodes:
                        # 双应用公用失效日期
                        new_xml_handle.set_attribute(cert_node,'expireDate',self.config.get('expireDate'))
                        new_xml_handle.set_attribute(cert_node,'expireDateType',self.config.get('expireDateType'))
                        if index == 1: #第二应用,若双应用RSA长度一致，则只需设置一个RSA，默认长度为1152位
                            new_xml_handle.set_attribute(cert_node,'rsa',self.config.get('second_rsa',self.config.get('rsa','1152')))
                        else:
                            new_xml_handle.set_attribute(cert_node,'rsa',self.config.get('rsa','1152'))
                
                #对于VISA应用，如果RSA长度大于1024,需要新增DGI存储tag9F4B
                if self.config.get('app_type') in (AppType.VISA_CREDIT,AppType.VISA_DEBIT):
                    self._handle_9F4B(new_xml_handle,app_node)

            tag_nodes = new_xml_handle.get_nodes(app_node,'Tag') #取应用下面的Tag节点
            for tag_node in tag_nodes:
                attr_tag = new_xml_handle.get_attribute(tag_node,'name')        # Tag标签
                attr_type = new_xml_handle.get_attribute(tag_node,'type')       # Tag值类型,fixed,file,kms
                attr_source = new_xml_handle.get_attribute(tag_node,'source')   # Tag来源 contact,contactless,fci...
                attr_format = new_xml_handle.get_attribute(tag_node,'format')   # Tag 形式,TLV,V结构
                attr_comment = new_xml_handle.get_attribute(tag_node,'comment') # Tag描述信息
                attr_sig_id = new_xml_handle.get_attribute(tag_node,'sig_id')   # Tag使用的签名数据
                attr_value = new_xml_handle.get_attribute(tag_node,'value')     # Tag值
                second_app = new_xml_handle.get_attribute(tag_node,'second_app') # 指定是否使用第二应用数据

                # 生成数据,需要设置当前使用的数据集合
                if self._is_second_app(new_xml_handle,app_node) or (second_app and second_app == 'true'):
                    self.cur_source_items = self.second_source_items
                else:
                    self.cur_source_items = self.source_items

                # 删除之，重新给属性排序
                # new_xml_handle.remove_attribute(tag_node,'name') # name总是为第一个属性
                new_xml_handle.remove_attribute(tag_node,'type')
                new_xml_handle.remove_attribute(tag_node,'comment')
                new_xml_handle.remove_attribute(tag_node,'format')
                new_xml_handle.remove_attribute(tag_node,'source')
                new_xml_handle.remove_attribute(tag_node,'sig_id')
                new_xml_handle.remove_attribute(tag_node,'value')
                
                
                # 重新排序,依次设置Tag节点属性
                # new_xml_handle.set_attribute(tag_node,'name',attr_tag)

                # value属性获取规则如下:
                # 1. 若模板中有值，则优先从模板中取值
                # 2. 若模板无value属性，则根据模板中的name和source属性从source_items集合中获取
                # 3. 若模板无value属性，且name属性为--,则根据comment属性从source_items集合中获取
                # 注意，这里的value还只是固定值,value属性放置在type属性之后设置
                if not attr_value:
                    if not attr_tag or attr_tag.strip() == '--':
                        attr_value = self._get_value(comment=attr_comment)
                    else:
                        attr_value = self._get_value(tag=attr_tag, source=attr_source)

                # 对于visa项目,如果RSA长度小于等于1024,需要在9115,9116,9117中添加9F4B81XX
                # 注意,这里默认visa为第一应用,若出现visa为第二应用的情况，则不适用。
                if self.config.get('app_type') in (AppType.VISA_CREDIT,AppType.VISA_DEBIT):
                    rsa = int(self.config.get('rsa','1152'))
                    if  rsa <= 1024 and attr_tag == 'FFFF': #这里使用特殊的tagFFFF表示DGI9115,9116,9117中的TL结构
                        attr_value += '9F4B81' + utils.int_to_hex_str(rsa // 8)

                # 处理Tag节点中的type属性
                if attr_type:
                    # 优先从模板中获取type属性
                    if attr_type == 'kms':
                        # 来自加密机, 优先处理从加密机里面的数据，不取来自客户表中数据
                        new_xml_handle.set_attribute(tag_node,'type','kms')
                    elif attr_type == 'fixed':
                        #说明是固定值,并且不需要从文件中取
                        new_xml_handle.set_attribute(tag_node,'type','fixed')
                        new_xml_handle.set_attribute(tag_node,'value',attr_value)
                    elif attr_type == 'file':
                        # 来自文件
                        new_xml_handle.set_attribute(tag_node,'type','file')
                        item = self.emboss_items.get(attr_tag)
                        if item:
                            new_xml_handle.set_attribute(tag_node,'value',item.value)
                            if item.convert_to_ascii:
                                new_xml_handle.set_attribute(tag_node,'convert_ascii','true')
                            if item.replace_equal_by_D:
                                new_xml_handle.set_attribute(tag_node,'replace_equal_by_D','true')
                        else:
                            # 若无法找到该tag节点，则删除之，并加入not found列表中
                            new_xml_handle.remove(tag_node)
                            self.unused_data.append((attr_tag,attr_source,attr_comment))
                else:
                    if attr_tag in tags_from_kms:
                        # 来自加密机, 优先处理从加密机里面的数据，不取来自客户表中数据
                        new_xml_handle.set_attribute(tag_node,'type','kms')
                    elif attr_value:# and not self.emboss_items.get(attr_tag):
                        #说明是固定值,并且不需要从文件中取
                        new_xml_handle.set_attribute(tag_node,'type','fixed')
                        if attr_value == 'empty':
                            new_xml_handle.set_attribute(tag_node,'value','')
                        elif attr_value == 'N.A':
                            new_xml_handle.remove(tag_node)
                            self.unused_data.append((attr_tag,attr_source,attr_comment))
                        else:
                            new_xml_handle.set_attribute(tag_node,'value',attr_value)
                    else:
                        item = self.emboss_items.get(attr_tag)
                        if item:
                            if item.value and utils.is_hex_str(item.value):
                                # 说明是来自emboss item中的固定值,此时忽略转码规则
                                new_xml_handle.set_attribute(tag_node,'type','fixed')
                                new_xml_handle.set_attribute(tag_node,'value',item.value)
                            else:
                                # 说明emboss item中的元素是从文件中取值
                                new_xml_handle.set_attribute(tag_node,'type','file')
                                new_xml_handle.set_attribute(tag_node,'value',item.value)
                                if item.convert_to_ascii:
                                    new_xml_handle.set_attribute(tag_node,'convert_ascii','true')
                                if item.replace_equal_by_D:
                                    new_xml_handle.set_attribute(tag_node,'replace_equal_by_D','true')
                        else:   #说明无法从数据来源中获取该Tag的相关信息
                            new_xml_handle.remove(tag_node)
                            self.unused_data.append((attr_tag,attr_source,attr_comment))
                
                # 设置签名,直接复制模板中的值
                if attr_sig_id:
                    new_xml_handle.set_attribute(tag_node,'sig_id',attr_sig_id)

                #设置编码格式和描述，若模板中没有comment属性，则取至settings.py
                new_xml_handle.set_attribute(tag_node,'format',attr_format)
                if not attr_comment:
                    aid = new_xml_handle.get_attribute(app_node,'aid')
                    if aid == 'A0000000041010':
                        attr_comment = settings.mc_tag_desc_mappings.get(attr_tag)
                    elif aid == 'A0000000031010':
                        attr_comment = settings.visa_tag_desc_mappings.get(attr_tag)
                    elif aid == 'A00000047400000001':
                        attr_comment = settings.jetco_tag_desc_mappings.get(attr_tag)
                    elif aid in ('A000000333010101','A000000333010102'):
                        attr_comment = settings.uics_tag_desc_mappings.get(attr_tag)
                new_xml_handle.set_attribute(tag_node,'comment',attr_comment)

            #最后设置alias
            self._add_alias(new_xml_handle,tag_nodes) 
            # 删除 空模板节点
            self.remove_empty_node(new_xml_handle)
        # 设置完毕后，保存
        new_xml_handle.save(char_set)

#根据DP xml文件和emboss file模拟一条制卡数据，用于制作测试卡
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

    def _assemble_value(self,tag,data,data_format):
        '''
        根据data_format组装TLV数据
        '''
        if data_format == 'TLV':
            return utils.assemble_tlv(tag,data)
        else:
            return data

    def _get_date_value(self,date):
        '''
        解析tag5F24/5F25格式
        '''
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

    def _get_value_from_file(self,value):
        '''
        解析emboss items中数据数据
        '''
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
        if r'{FD}' in data or r'{LD}' in data:
            return self._get_date_value(data)
        return data

    def _parse_tag_value(self,tag_node,kms=None):
        attrs = self.xml_handle.get_attributes(tag_node)
        tag = attrs['name']
        value = ''
        value_type = attrs['type']
        value_format = attrs['format']
        if value_type == 'fixed': #处理固定值
            value = self._assemble_value(tag,attrs['value'],value_format)
        elif value_type == 'kms':   #处理KMS生成的数据
            if not kms:
                logging.info('kms is not inited. can not process tag %s with kms type',tag)
            else:
                kms_tag = tag
                if 'sig_id' in attrs:
                    kms_tag = kms_tag + '_' + attrs['sig_id']
                value = self._assemble_value(tag,kms.get_value(kms_tag),value_format)
        elif value_type == 'file': # 处理文件数据
            value = self.xml_handle.get_attribute(tag_node,'value')
            if value:
                value = self._get_value_from_file(value)
                replaceD = self.xml_handle.get_attribute(tag_node,'replace_equal_by_D')
                if replaceD:
                    value = value.replace('=','D')
                convert_ascii = self.xml_handle.get_attribute(tag_node,'convert_ascii')
                if convert_ascii and convert_ascii.lower() == 'true':
                    value = utils.str_to_bcd(value)
                if len(value) % 2 != 0:
                    value += 'F'
                value = self._assemble_value(tag,value,value_format)
            else: #如果类型为file的Tag,没有value属性，则通过emboss file模块处理值
                if self.process_emboss_file_module:
                    mod_obj = importlib.import_module(self.process_emboss_file_module)
                    if mod_obj:
                        if hasattr(mod_obj,'process_tag' + tag):
                            func = getattr(mod_obj,'process_tag' + tag)
                            value = self._assemble_value(tag,func(),value_format)
                        else:
                            print('can not process tag' + tag)
                else:
                    print('emboss file module can not process tag' + tag)
        return tag,value
        
    def _parse_template(self,template_node,kms=None):
        template_value = ''
        template = self.xml_handle.get_attribute(template_node,'name')
        child_nodes = self.xml_handle.get_child_nodes(template_node)
        for child_node in child_nodes:
            if child_node.nodeName == 'Tag':
                _,value = self._parse_tag_value(child_node,kms)
                template_value += value
            elif child_node.nodeName == 'Template':
                template_value += self._parse_template(child_node,kms)
        return utils.assemble_tlv(template,template_value)

    def _gen_sig_data(self,app_node,kms):
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
            kms.gen_new_icc_cert(tag5A,sig_data,sig_id)
            kms.gen_new_ssda(kms.issuer_bin,sig_data,sig_id)

    def _get_first_bin(self):
        '''
        从DP xml文件中的Bin节点，取第一个Bin号生成测试数据
        '''
        issuer_bin = ''
        bin_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'Bin')
        if bin_node:
            issuer_bin = self.xml_handle.get_attribute(bin_node,'value')
            if not issuer_bin or issuer_bin == '':
                logging.info('Please provide card Bin number, if not, card will use default Bin number:654321')
                issuer_bin = '654321'
            else:
                issuer_bin = issuer_bin.split(',')[0]    #取第一个bin号生成证书
        return issuer_bin

    def _get_rsa_len(self,app_node):
        '''
        从DP xml文件中的指定App节点中的Cert节点获取RSA长度
        '''
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
        dgi.name = self.xml_handle.get_attribute(dgi_node,'name')
        child_nodes = self.xml_handle.get_child_nodes(dgi_node)
        if child_nodes and len(child_nodes) == 1:   #判断是否为70模板开头，若是，则忽略掉70模板
            attr_name = self.xml_handle.get_attribute(child_nodes[0],'name')
            if attr_name == '70':
                child_nodes = self.xml_handle.get_child_nodes(child_nodes[0])
        for child_node in child_nodes:
            if child_node.nodeName == 'Tag':
                tag,value = self._parse_tag_value(child_node,kms)
                value = value.replace(' ','') #过滤掉value中的空格
                data_format = self.xml_handle.get_attribute(child_node,'format')
                if data_format == 'V':  #对于value数据，取dgi作为tag
                    dgi.append_tag_value(dgi.name,value)
                else:
                    dgi.add_tag_value(tag,value)
            elif child_node.nodeName == 'Template':
                # 对于非70模板，直接拼接该值，不做TLV解析处理
                template_value = self._parse_template(child_node,kms)
                dgi.append_tag_value(dgi.name,template_value)
            else:
                print('unrecognize node' + child_node.nodeName)
        if dgi.name == '0101' and dgi.is_existed('56') and dgi.is_existed('9F6B'):
            # 说明是MC应用，且支持MSD,这时需要生成对应的DC,DD
            tag56 = dgi.get_value('56')[4:] # 偷懒，不需要解析TLV
            tag9F6B = dgi.get_value('9F6B')[6:]
            kms.gen_mc_cvc3(tag56,tag9F6B)
        return dgi

    def _process_pse(self,pse_node):
        pse = Dgi()
        pse.name = pse_node.nodeName
        dgi_nodes = self.xml_handle.get_child_nodes(pse_node)
        for dgi_node in dgi_nodes:
            dgi = self._process_dgi(dgi_node)
            for key,value in dgi.tag_value_dict.items():
                pse.add_tag_value(key,value)
        return pse

    def gen_cps(self):
        app_nodes = self.xml_handle.get_nodes(self.xml_handle.root_element,'App')
        app_count = 0
        for app_node in app_nodes:
            app_count += 1
            issuer_bin = self._get_first_bin()
            rsa_len = self._get_rsa_len(app_node)
            kms = Kms()
            kms.init(issuer_bin,rsa_len)
            self._gen_sig_data(app_node,kms)    #根据sig节点生成与证书相关的数据
            dgi_nodes = self.xml_handle.get_child_nodes(app_node,"DGI") #获取app节点下所有的DGI节点
            for dgi_node in dgi_nodes:
                dgi = self._process_dgi(dgi_node,kms)
                if app_count > 1:   # 说明是双应用，DGI形式为[0101_2]
                    dgi.name = dgi.name + '_' + str(app_count)
                self.cps.add_dgi(dgi)
            kms.close()
        # 处理PSE 和 PPSE
        pse_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'PSE')
        if pse_node:
            pse_dgi = self._process_pse(pse_node)
            self.cps.add_dgi(pse_dgi)
        ppse_node = self.xml_handle.get_first_node(self.xml_handle.root_element,'PPSE')
        if ppse_node:
            ppse_dgi = self._process_pse(ppse_node)
            self.cps.add_dgi(ppse_dgi)
        return self.cps

if __name__ == '__main__':
    docx = GenDpDoc('D://DP.xml','D://DP需求.docx')
    docx.gen_dp_docx()
