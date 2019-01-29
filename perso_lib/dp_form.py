from perso_lib.excel import ExcelMode,ExcelOp
from perso_lib import utils
from perso_lib.file_handle import FileHandle
from enum import Enum

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

class TagPosItem:
    def __init__(self):
        self.name = ''
        self.tag = ''
        self.convert_ascii = False
        self.prefix = ''
        self.suffix = ''
        self.pos_list = []

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
            return "file"   #处理DP自定义数据
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

class PosForm:
    def __init__(self,table_name):
        self.excel = ExcelOp(table_name)
        self.data_list = []

    def read_form_data(self,sheet_name='pos_sheet',start_row=1,start_col=1):
        if self.excel.open_worksheet(sheet_name):
            header = self.excel.read_cell_value(start_row,start_col)
            if str(header).strip() != 'Name':
                print('can not get pos sheet header')
                return None
            for i in range(start_row + 1,20):
                item = TagPosItem()
                item.name = self.excel.read_cell_value(i,start_col)
                item.tag = self.excel.read_cell_value(i,start_col + 1)
                if item.tag:
                    item.tag = str(item.tag)
                item.convert_ascii = self.excel.read_cell_value(i,start_col + 2)
                item.prefix = self.excel.read_cell_value(i,start_col + 3)
                item.suffix = self.excel.read_cell_value(i,start_col + 4)
                if item.prefix and isinstance(item.prefix,int):
                    item.prefix = str(item.prefix)
                if item.suffix and isinstance(item.suffix,int):
                    item.suffix = str(item.suffix)
                for col_pos in range(start_col + 5,20):
                    pos = self.excel.read_cell_value(i,col_pos)
                    if not pos:
                        break
                    item.pos_list.append(str(pos))
                self.data_list.append(item)
        return self.data_list

    def get_dki(self):
        pass

    def get_tag_info(self,tag):
        for item in self.data_list:
            if tag == item.tag:
                return item
        return None

    # def get_value(self,tag):
    #     value = ''
    #     for item in self.data_list:
    #         if tag == item.tag:
    #             if item.prefix:
    #                 value = item.prefix + value
    #             for index in range(0,len(item.pos_list) - 2,2):
    #                 start_pos = int(item.pos_list[index])
    #                 end_pos = int(item.pos_list[index + 1])
    #                 value += self.emboss_file_handle.read_pos(start_pos,end_pos)
    #             if item.suffix

        
if __name__ == '__main__':
    import os
    cwd = os.path.dirname(os.path.abspath(__file__))
    pos_form = PosForm(cwd + '\\TagPosConfirm.xlsx')
    pos_form.read_form_data()