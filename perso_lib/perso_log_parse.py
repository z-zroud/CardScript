from perso_lib.file_handle import FileHandle
from perso_lib.gen_kmc_session import gen_dek_session_key,DIV_METHOD
from perso_lib import utils
from perso_lib.cps import Dgi,Cps
from perso_lib.algorithm import des3_ecb_decrypt
from perso_lib import algorithm
from perso_lib import mock_dp
from perso_lib.log import Log
from perso_lib.xml_parse import XmlParser

Log.init()


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
            end_index = data.find(']',start_index)
            resp_start_index = data.find('[',end_index)
            resp_end_index = data.find(']',resp_start_index)
            req = data[start_index + 1:end_index] #取[]中间的APDU指令
            resp = data[resp_start_index + 1: resp_end_index]
            if req[0:4] in ('00A4','80E2','80E6','80D8','80F0'):
                if not req.endswith('00'):
                    Log.error('data error: %s not end with 00' % data)
                return req[0:-2],resp
        return '',''

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

    def gen_cps(self,session_key=None,second_session_key=None,delete80_list=[]):
        cps = Cps()
        start_perso = False # 个人化起始行
        app_type = None     # 个人化应用类型
        prevous_req = '' #保存上一次的数据，对于一条超长数据，需要使用两条store data指令
        prevous_req_len = 0 # 
        is_jetco_app = False    #判断是否有jetco应用
        parse_perso_complete = False #是否已经完成个人化
        has_check_status = False    #是否有检测卡片状态
        has_check_kmc = False   # 是否有检测修改过卡片KMC
        if not delete80_list:
            delete80_list = ['8201','8202','8203','8204','8205']
        while not self.log_handle.EOF:
            is_encrypted = False
            data = self.log_handle.read_line()  #每次读取一行数据进行分析
            req,resp = self._filter(data) #过滤非指定的APDU信息，返回请求和响应数据
            if req.startswith('80E60C00'): #解析安装参数信息
                Log.info('===================== Check Install Param =====================')
                self._parse_install_cmd(req,resp)
            if req.startswith('00A40400') and not req.startswith('00A4040008A000000003000000'):
                start_perso = True   #从此行开始认定个人化开始
            if start_perso:
                if req.startswith('00A404000E315041592E5359532E4444463031'):
                    app_type = 'PSE' #说明接下来是个人化PSE
                    continue
                elif req.startswith('00A404000E325041592E5359532E4444463031'):
                    app_type = 'PPSE' #接下来个人化PPSE
                    continue
                elif req.startswith('00A40400'): #应用
                    app_type = 'APP'
                    if req.startswith('00A4040009A00000047400000001'):
                        app_type = "JETCO"
                        is_jetco_app = True # 这里判断，是因为表示是双应用数据
                    continue
                if app_type:
                    if req.startswith('80E2') and req[4:6] in ('00','60','80','E0'): #处理store data 数据
                        if resp != '9000':
                            Log.error('perso error: [APDU: %s][%s]',req,resp)
                            continue
                        #判断是否为加密数据
                        if req[4:6] in ('60','E0'):    
                            is_encrypted = True
                        # 判断是否已经解析完个人化数据，接下来要判断卡片安全状态和修改KMC
                        if req[4:6] in ('80','E0') and app_type == 'APP':
                            parse_perso_complete = True
                        req = req[10:] # 去掉命令头及长度
                        # 处理仅一条APDU指令发送store data的情况
                        if not prevous_req:
                            dgi_name = req[0:4] # DGI名称
                            if is_jetco_app: #默认Jetco为第二应用
                                dgi_name += '_2'
                            req = req[4:] # 去掉DGI名称

                            # 去掉DGI后面跟随的长度
                            data_len = 0
                            if req[0:4] == 'FF00': 
                                data_len = int(req[4:6],16)
                                req = req[6:]
                            else:
                                data_len = int(req[0:2],16)
                                req = req[2:]

                            # 如果长度和后面的数据不一致，则说明分两条APDU发送
                            if data_len * 2 != len(req):
                                prevous_req = req
                                prevous_req_len = data_len
                                continue
                        else: # 处理需要两条APDU指令发送的情况
                            req = prevous_req + req
                            if prevous_req_len * 2 != len(req):
                                Log.error("data len error")
                                return None
                            prevous_req = ''
                            prevous_req_len = 0
                        dgi = None
                        if is_jetco_app:
                            dgi = self.parse_store_data(app_type,dgi_name,req,second_session_key,is_encrypted,delete80_list)
                        else:
                            dgi = self.parse_store_data(app_type,dgi_name,req,session_key,is_encrypted,delete80_list)
                        cps.add_dgi(dgi)
            if parse_perso_complete:
                if req.startswith('80F080'): # 检测卡片是否设置为安全状态
                    Log.info('===================== Check Card Status =====================')
                    has_check_status = True
                    self._parse_set_status_cmd(req,resp)
                if req.startswith('80D8'): # 检测卡片是否修改KMC
                    Log.info('===================== Check KMC =====================')
                    has_check_kmc = True
                    self._parse_modify_kmc(req,resp)
        if not has_check_status:
            Log.info('===================== Check Card Status =====================')
            Log.error('Not set card status during perso card.\n')
        if not has_check_kmc:
            Log.info('===================== Check KMC =====================')
            Log.error('Not modify kmc during perso card.\n')
        return cps

    def _get_install_param(self,data):
        param_len = utils.hex_str_to_int(data[0:2]) * 2
        param = data[2:2 + param_len]
        data = data[2 + param_len:]
        return data,param

    def _parse_install_cmd(self,data,resp):
        if data.startswith('80E60C00'):
            data = data[10:] # 去掉命令头及长度部分
            data,pkg = self._get_install_param(data)
            data,applet = self._get_install_param(data)
            data,inst = self._get_install_param(data)
            data,priviliage = self._get_install_param(data)
            token,param = self._get_install_param(data)
            if resp != '6101':
                Log.error('Install Instance:%s Failed.',inst)
            else:
                Log.info('Install Instance:%s',inst)
            Log.info('Package:%s',pkg)
            Log.info('Applet:%s',applet)
            Log.info('Priviliage:%s',priviliage)
            Log.info('Install param:%s',param)
            Log.info('Token:%s\n',token)

    def _parse_set_status_cmd(self,req,resp):
        if req[0:6] == '80F080':
            if req[6:8] == '07':
                Log.info('current card lifecycle: OP_INITIALIZE')
            elif req[6:8] == '0F':
                Log.info('current card lifecycle: SECURED')
            else:
                Log.error('Unknown card lifecycle')
            if resp != '9000':
                Log.error('set current lifecyle Failed.')
            
    def _parse_modify_kmc(self,req,resp):
        if req[0:4] == '80D8' and resp == '610A':
            Log.info('Check Modify KMC Sucess.')
        else:
            Log.error('Check Modify KMC Failed.')

    def _comapre_dgi_list(self,mock_cps,prod_cps):
        Log.info('===================== Check DGI List =====================')
        mock_cps_dgis = [item.name for item in mock_cps.dgi_list]
        prod_cps_dgis = [item.name for item in prod_cps.dgi_list]
        for mock_cps_dgi_name in mock_cps_dgis:
            if mock_cps_dgi_name not in prod_cps_dgis:
                Log.error('should perso DGI %s in product environment',mock_cps_dgi_name)
        for prod_cps_dgi_name in prod_cps_dgis:
            if prod_cps_dgi_name not in mock_cps_dgis:
                Log.error('should NOT perso DGI %s in product environment',prod_cps_dgi_name)
        Log.info("\nmock dgi list:%s\n",mock_cps_dgis)
        Log.info('prod dgi list:%s\n',str(prod_cps_dgis))

    def _display_emboss_data(self,cps,dp_xml):
        Log.info('===================== Show Dynamic Data =====================')
        tags = []
        xml_handle = XmlParser(dp_xml)
        tag_nodes = xml_handle.get_nodes(xml_handle.root_element,'Tag')
        for tag_node in tag_nodes:
            if xml_handle.get_attribute(tag_node,'type') == 'file':
                name = xml_handle.get_attribute(tag_node,'name')
                if name not in tags:
                    tags.append(name)
        dgis = cps.get_all_dgis()
        for dgi in dgis:
            for tag,value in dgi.get_all_tags().items():
                if value:
                    value = value[len(tag) + 2:]    #去掉tag及长度域
                if tag in tags:
                    Log.info('tag%-5s:       value:%s',tag,value)
        Log.info('\n')

    def _display_dki(self,cps):
        dgis = cps.get_all_dgis()
        Log.info('===================== First Application Key Info =====================')
        for dgi in dgis:
            for tag,value in dgi.get_all_tags().items():
                if tag in ('9F10') and '_2' not in dgi.name:
                    Log.info('tag9F10:%s       DKI:%s',value[6:],value[8:10])
        Log.info('\n===================== Second Application Key Info =====================')
        for dgi in dgis:
            for tag,value in dgi.get_all_tags().items():
                if tag in ('9F10') and '_2' in dgi.name:
                    Log.info('tag9F10:%s       DKI:%s',value[6:],value[8:10])
        Log.info('\n')

    def _display_key_info(self,cps):
        keys = ['8000','A006','8401','9000']
        dgis = cps.get_all_dgis()
        Log.info('===================== First Application Key Info =====================')
        for dgi in dgis:
            kcv = ''
            for tag,value in dgi.get_all_tags().items():
                if tag in keys:
                    if tag != '9000':
                        kcv = algorithm.gen_kcv(value)
                    Log.info('tag%-5s:       value:%s  kcv:%s',tag,value,kcv)
        second_keys = ['8000_2','9000_2']
        Log.info('\n===================== Second Application Key Info =====================')
        for dgi in dgis:
            kcv = ''
            for tag,value in dgi.get_all_tags().items():
                if dgi.name in second_keys:
                    Log.info('tag%-5s:       value:%s  kcv:%s',tag,value,kcv)
        Log.info('\n')
        



    def compare_cps(self,product_cps,mock_cps,ignore_list=[]):
        self._comapre_dgi_list(mock_cps,product_cps)
        mock_dgis = mock_cps.get_all_dgis()
        if not ignore_list:
            # 涉及KMS相关的值，不比较
            ignore_list = ['8F','90','92','9F32','9F46','9F48','93','8201','8202','8203','8204','8205','8000','9000','A006','A016','8400','8401','8001','9001','B010','B023']
        Log.info('===================== Compare Data =====================')
        for mock_dgi in mock_dgis:
            product_dgi = product_cps.get_dgi(mock_dgi.name)
            if not product_dgi:
                Log.error('cannot find DGI %s in product enviromnent' % mock_dgi.name)
                continue
            for tag,value in mock_dgi.get_all_tags().items():
                if tag in ignore_list:
                    continue
                product_value = product_dgi.get_value(tag)
                if product_value != value:
                    Log.error('compare tag %s failed.' % tag)
                    Log.error('Prod_value: %s' % product_value)
                    Log.error('Mock_value: %s\n' % value)

    def compare_xml(self,cps,dp_xml,emboss_file):
        mock_obj = mock_dp.MockCps(dp_xml,emboss_file)
        mock_cps = mock_obj.gen_cps()
        self._display_dki(cps)
        self._display_key_info(cps)
        self._display_emboss_data(cps,dp_xml)
        self.compare_cps(cps,mock_cps)
        