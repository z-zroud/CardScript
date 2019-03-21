from perso_lib.file_handle import FileHandle
from perso_lib.gen_kmc_session import gen_dek_session_key,DIV_METHOD
from perso_lib import utils
from perso_lib.cps import Dgi,Cps
from perso_lib.algorithm import des3_ecb_decrypt
from perso_lib import mock_dp


class PersoLogParse:
    do_not_parse_tlv_list = ['9102','9103','8201','8202','8203','8204','8205','8000','9000','8202','8002','8302']
    def __init__(self,perso_log):
        self.log_handle = FileHandle(perso_log,'r+')

    def gen_dek_session_key(self,div_data,host_challenge='1122334455667788',kmc='5D685E2AAD0BA8F8F46804F4B0C41A92',div_method=DIV_METHOD.DIV_CPG202):
        session_key = gen_dek_session_key(kmc,div_method,host_challenge,div_data)
        return session_key

    def _filter(self,data):
        if data and data.startswith('APDU'):
            start_index = data.find('[')
            end_index = data.find(']')
            data = data[start_index + 1:end_index] #取[]中间的APDU指令
            if data.startswith('00A4') or data.startswith('80E2'):
                if not data.endswith('00'):
                    print('data error: %s not end with 00' % data)
                return data[0:-2]
        return ''

    def _assemble_dgi(self,dgi_name,tlvs):
        dgi = Dgi()
        dgi.name = dgi_name
        for tlv in tlvs:
            if not tlv.is_template:
                value = utils.assemble_tlv(tlv.tag,tlv.value) #组装为TLV结构
                dgi.add_tag_value(tlv.tag,value)
        return dgi

    def parse_store_data(self,app_type,dgi_name,data,session_key=None,is_encrypted=False,delete80_list=[]):
        int_dgi_name = int(dgi_name,16)
        if is_encrypted and session_key:
            data = des3_ecb_decrypt(session_key,data)
            if dgi_name in delete80_list:
                index = data.rfind('80')
                if index != -1:
                    data = data[0:index]
            
        #对于PSE和PPSE，不解析TLV格式
        if app_type in ('PSE','PPSE'):
            dgi = Dgi()
            dgi.name = app_type
            if data.startswith('70'):
                data = data[4:] #去掉70模板
            dgi.add_tag_value(dgi_name,data)
            return dgi
        else:
            #规则如下:
            #1. 小于0x0B00的记录数据需要解析TLV结构
            #2. 如果DGI大于0B00,并且该数据可以解析成TLV,则分如下情况
            #   a. 如果是8000,9000,9102,9103等不需要分析TLV结构的，则不分析
            #   b. 如果DGI以A,B字母开头(万事达应用),不用做TLV分析
            if int_dgi_name <= 0x0B00 \
                or (dgi_name not in self.do_not_parse_tlv_list \
                    and utils.is_tlv(data)\
                    and not (dgi_name.startswith('A') or dgi_name.startswith('B')) ):
                if utils.is_tlv(data):
                    tlvs = utils.parse_tlv(data)
                    return self._assemble_dgi(dgi_name,tlvs)
                else:
                    dgi = Dgi()
                    dgi.name = dgi_name
                    dgi.add_tag_value(dgi_name,data)
                    return dgi
            else:
                dgi = Dgi()
                dgi.name = dgi_name
                dgi.add_tag_value(dgi_name,data)
                return dgi

    def gen_cps(self,session_key=None,delete80_list=[]):
        start_line = False
        app_type = None
        cps = Cps()
        if not delete80_list:
            delete80_list = ['8201','8202','8203','8204','8205']
        prevous_data = '' #保存上一次的数据，对于一条超长数据，需要使用两条store data指令
        prevous_data_len = 0
        is_jetco_app = False
        while not self.log_handle.EOF:
            is_encrypted = False
            data = self.log_handle.read_line()
            data = self._filter(data)
            if data and data.startswith('00A40400') and not data.startswith('00A4040008A000000003000000'):
                start_line = True   #从此行开始认定个人化开始
            if start_line and data:
                if data.startswith('00A404000E315041592E5359532E4444463031'):
                    app_type = 'PSE'
                    continue
                elif data.startswith('00A404000E325041592E5359532E4444463031'):
                    app_type = 'PPSE'
                    continue
                elif data.startswith('00A40400'): #应用
                    app_type = 'APP'
                    if data.startswith('00A4040009A00000047400000001'):
                        is_jetco_app = True
                    continue
                if app_type:
                    if data.startswith('80E2') and data[4:6] in ('00','60','80','E0'): #处理store data 数据
                        if data[4:6] in ('60','E0'):
                            is_encrypted = True
                        data = data[10:] #去掉命令头及长度
                        if not prevous_data:
                            dgi_name = data[0:4] # DGI名称
                            if is_jetco_app: #默认Jetco为第二应用
                                dgi_name += '_2'
                            data = data[4:]
                            data_len = 0
                            if data[0:4] == 'FF00':
                                data_len = int(data[4:6],16)
                                data = data[6:]
                            else:
                                data_len = int(data[0:2],16)
                                data = data[2:]
                            if data_len * 2 != len(data):
                                prevous_data = data
                                prevous_data_len = data_len
                                continue
                        else:
                            data = prevous_data + data
                            if prevous_data_len * 2 != len(data):
                                print("data len error")
                                return None
                            prevous_data = ''
                            prevous_data_len = 0
                        dgi = self.parse_store_data(app_type,dgi_name,data,session_key,is_encrypted,delete80_list)
                        cps.add_dgi(dgi)
        return cps

    def compare_cps(self,product_cps,mock_cps,ignore_list=[]):
        mock_dgis = mock_cps.get_all_dgis()
        if not ignore_list:
            # 涉及KMS相关的值，不比较
            ignore_list = ['90','92','9F32','9F46','9F48','93','8201','8202','8203','8204','8205','8000','9000','A006','A016','8400','8401','8001','9001','B010','B023']
        for mock_dgi in mock_dgis:
            product_dgi = product_cps.get_dgi(mock_dgi.name)
            if not product_dgi:
                print('cannot find DGI %s in product enviromnent' % mock_dgi.name)
                continue
            for tag,value in mock_dgi.get_all_tags().items():
                if tag in ignore_list:
                    continue
                product_value = product_dgi.get_value(tag)
                if product_value != value:
                    print('compare tag %s value failed.' % tag)
                    print('P_value: %s' % product_value)
                    print('M_value: %s\n\n' % value)

    def compare_xml(self,cps,dp_xml,emboss_file):
        mock_obj = mock_dp.MockCps(dp_xml,emboss_file)
        mock_cps = mock_obj.gen_cps()
        self.compare_cps(cps,mock_cps)
        