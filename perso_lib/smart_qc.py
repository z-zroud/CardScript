from perso_lib.xml_parse import XmlParser,XmlMode
from perso_lib import utils

no_contain_list = ['9F46','93','90','92','9F48','9F36','9F6C','8F','5F24','5F25','DF41']
warn_list = ['57','9F1F','5F20','5A']
no_must_contain_list = ['57','5F20','9F6C','5F34','9F36','DF41']

tag_desc = {
    '4F':'Application Identifier (AID)',
    '50':'Application Lable',
    '9F12':'Issuer Code Table Index',
    '87':'Application Priority Indicator (API)',
    '88':'Short File Identifier(FCI)',
    '5F2D':'Language Preference',
    '9F11':'Issuer Code Table Index',
    '9F38':'Processing Options Data Objiect List(PDOL)',
    '9F4D':'Log Entry',
    'DF4D':'UploadDownload Log Entry',
    '82':'Application Interchange Profile (AIP)',
    '94':'Application file locator (AFL)',
    '57':'Track 2 equivalent data',
    '9F1F':'Track 1 Discretionary Data',
    '8F':'Certification Authority Public Key Index (PKI)',
    '9F32':'Issuer public key exponent',
    '5F20':'Cardholder name',
    '9F62':'Cardholder ID type',
    '5F24':'Application Expiration Date',
    '5A':'Application Primary Account Number (PAN)',
    '5F34':'Application Primary Account Number Sequence Number (PAN SN)',
    '9F07':'Application Usage Control (AUC)',
    '8E':'Cardholder Verification Method (CVM) List',
    '9F0D':'Issuer Action Code-Default (IAC-Default)',
    '9F0E':'Issuer Action Code-Denial (IAC-Denial)',
    '9F0F':'Issuer Action Code-Online (IAC-Online)',
    '5F28':'Issuer Country Code',
    '9F47':'ICC Public Key Exponent',
    '5F25':'Application Effective Date',
    '9F4A':'Static Data Authentication Tag List',
    '9F63':'Identification Information Of The Card Products',
    '5F30':'Service Code',
    '8C':'Card Risk Management Data Object List 1 (CDOL1)',
    '8D':'Card Risk Management Data Object List 2 (CDOL2)',
    '9F08':'Application Version Number',
    '9F49':'DynamicDataAuthDOL (DDOL)',
    '9F14':'Lower Consecutive Offline Limit (LCOL)',
    '9F23':'Upper Consecutive Offline Limit (UCOL)',
    '9F56':'Issuer Authentication Indicator',
    '9F57':'Issuer Country Code',
    '9F58':'Lower Consecutive Offline Limit (LCOL)',
    '9F59':'Upper Consecutive Offline Limit',
    # '9F72':'Consecutive Transaction Limit (International-Country)',
    # '9F75':'Cumulative Total Transaction Amount Limit Dual Currency',
    '9F13':'Application Currency Code',
    'DF4F':'DF4F',
    'DF62':'DF62',
    'DF63':'DF63',
    '9F4F':'9F4F',
    '9F51':'Application Currency Code',
    '9F52':'Application Default Action (ADA)',
    '9F53':'Consecutive Transaction Limit (International)',
    '9F54':'Cumulative Total Transaction Amount Limit',
    '9F5C':'Cumulative Total Transaction Amount Upper Limit',
    '9F5D':'eCash/VLP Available Funds',
    '9F68':'9F68',
    '9F6B':'9F6B',
    '9F6D':'9F6D',
    '9F77':'eCash/VLP Funds Limit',
    '9F78':'eCash/VLP Single Transaction Limit',
    '9F79':'eCash/VLP Available Funds',
    #---------------------------------------------------------
    'DF55':'DKI',
    'DF54':'CVN',
    'C9':'Accumulator 1 Currency Code',
    'CA':'Lower Consecutive Offline Transaction Amount',
    'CB':'Upper Consecutive Offline Transaction Amount',
    'DF16':'Accumulator 2 Currency Code',
    'DF17':'Accumulator 2 Currency Conversion Table',
    'D1':'Accumulator 1 Currency Conversion Table',
    'DF18':'Accumulator 2 Lower Limit',
    'DF19':'Accumulator 2 Upper Limit',
    'D3':'Additional Check Table',
    'C7':'CDOL1 Related Data Length',
    'DF21':'Counter 2 Upper Limit',
    'C8':'CRM Country Code',
    'D6':'Default ARPC Response Code',
    'DF24':'MTA Currency Code',
    'DF27':'Number Of Days Off Line Limit',
    'DF11':'Accumulator 1 Control (Contact)',
    'DF28':'Accumulator 1 CVR Dependency Data (Contact)',
    'DF14':'Accumulator 2 Control (Contact)',
    'DF2A':'Accumulator 2 CVR Dependency Data (Contact)',
    'D5':'Application Control (Contact)',

    'C3':'CIAC (Contact)-Decline',
    'C4':'CIAC (Contact)-Default',
    'C5':'CIAC (Contact)-Online',
    'DF1A':'Counter 1 Control (Contact)',

    'DF2C':'Counter 1 CVR Dependency Data (Contact)',
    'DF1D':'Counter 2 Control (Contact)',
    'DF2E':'Counter 2 CVR Dependency Data (Contact)',
    'DF3C':'CVR Issuer Discretionary Data (Contact)',
    'DF22':'MTA CVM (Contact)',
    'DF25':'MTA NoCVM (Contact)',
    'DF3F':'Read Record Filter (Contact)',
    'DF12':'Accumulator 1 Control (Contactless)',
    'DF29':'Accumulator 1 CVR Dependency Data (Contactless)',
    'DF15':'Accumulator 2 Control (Contactless)',
    'DF2B':'Accumulator 2 CVR Dependency Data (Contactless)',
    'D7':'Application Control (Contactless)',
    'CF':'CIAC (Contactless) - Decline',
    'CD':'CIAC (Contactless) - Default',
    'CE':'CIAC (Contactless) - Online',
    'DF1B':'Counter 1 Control (Contactless)',
    'DF2D':'Counter 1 CVR Dependency Data (Contactless)',
    'DF1E':'Counter 2 Control (Contactless)',
    'DF2F':'Counter 2 CVR Dependency Data (Contactless)',
    'DF3D':'CVR Issuer Discretionary Data (Contactless)',
    'DF23':'MTA CVM (Contactless)',
    'DF26':'MTA NoCVM (Contactless)',
    'DF40':'Read Record Filter (Contactless)',
    'DE':'Log Data Table',
    '9F70':'Protected Data Envelope 1',
    '9F71':'Protected Data Envelope 2',
    '9F72':'Protected Data Envelope 3',
    '9F73':'Protected Data Envelope 4',
    '9F74':'Protected Data Envelope 5',
    '9F75':'Unprotected Data Envelope 1',
    '9F76':'Unprotected Data Envelope 2',
    # '9F77':'Unprotected Data Envelope 3',
    # '9F78':'Unprotected Data Envelope 4',
    # '9F79':'Unprotected Data Envelope 5',
    '9F17':'PIN Try Limit',
}

class SmartQC:
    def __init__(self,file_name):
        self.file_name = file_name
        self.xml = XmlParser(file_name,XmlMode.WRITE)
        self._create_project_node()
        self._create_case_list_node()
        self.current_case_id = 0

    def _create_project_node(self):
        self.project_node = self.xml.create_root_element('Project')
        return self.project_node

    def _create_case_list_node(self):
        self.case_list_node = self.xml.add_node(self.project_node,'QCaseList')
        return self.case_list_node

    def create_case_node(self,name,dll='UICSCheck.dll',class_type='pboc_test'):
        self.current_case_id += 1 #每创建一个case节点,case id需要自动加1
        attrs = dict()
        attrs['id'] = str(self.current_case_id)
        attrs['name'] = name
        attrs['dll'] = dll
        attrs['class'] = class_type
        return self.xml.add_node(self.case_list_node,'QCase',**attrs)

    def create_device_node(self,parent_node,name="PC Twin"):
        attrs = dict()
        attrs['name'] = name
        attrs['remark'] = ''
        return self.xml.add_node(parent_node,'Device',**attrs)

    def create_node(self,parent_node,node_name,**attrs):
        return self.xml.add_node(parent_node,node_name,**attrs)

    def create_text_node(self,parent_node,node_name,text,**attrs):
        node = self.xml.add_node(parent_node,node_name,**attrs)
        self.xml.add_text(node,text)

    def create_tag_node(self,parent_node,tag,text,desc,algorithm='BCD',err_level=None):
        attrs = dict()
        attrs['name'] = tag
        attrs['description'] = desc
        if algorithm is not None:
            attrs['algorithm'] = algorithm
        if err_level is not None:
            attrs['errLevel'] = err_level
        tag_node = self.xml.add_node(parent_node,'Tag',**attrs)
        self.xml.add_text(tag_node,text)
        return tag_node

    def save(self):
        self.xml.save()

class SmartQC_EMV:
    def __init__(self,dp_xml,project_name):
        self.dp_xml = dp_xml
        self.project_name = project_name
        self.smart_qc = SmartQC(project_name)
        self.dp_xml_handle = XmlParser(dp_xml, XmlMode.READ_WRITE)

    def _get_tags(self,node):
        tags = []
        child_nodes = self.dp_xml_handle.get_nodes(node,'Tag')
        for node in child_nodes:
            # value_format = self.dp_xml_handle.get_attribute(node,'type')
            tag = self.dp_xml_handle.get_attribute(node,'name')
            value = self.dp_xml_handle.get_attribute(node,'value')
            if tag != '--' and (value and len(value) > 0 and utils.is_hex_str(value)):
                tags.append((tag,value))
        return tags

    def _get_pse_tags(self):
        pse_node = self.dp_xml_handle.get_first_node(self.dp_xml_handle.root_element,'PSE')
        return self._get_tags(pse_node)

    def _get_ppse_tags(self):
        ppse_node = self.dp_xml_handle.get_first_node(self.dp_xml_handle.root_element,'PPSE')
        return self._get_tags(ppse_node)

    def _get_dgi_tags(self,aid,name):
        app_node = self.dp_xml_handle.get_node_by_attribute(self.dp_xml_handle.root_element,'App',aid=aid)
        node = self.dp_xml_handle.get_node_by_attribute(app_node,'DGI',name=name)
        return self._get_tags(node)


    def _get_dgis(self,tag94):
        dgi_list = []
        afls = utils.parse_afl(tag94)
        for afl in afls:
            sfi = utils.int_to_hex_str(afl.sfi)
            record = utils.int_to_hex_str(afl.record_no)
            dgi_list.append(sfi + record)
        return dgi_list
    
    def _get_description(self,tag):
        if tag[0:2] == '00':
            tag = tag[2:]
        return tag_desc.get(tag,'')
    
    def save(self):
        self.smart_qc.save()

    def _create_header(self,case_name,case_type,interface,check_dll):
        case_node = self.smart_qc.create_case_node(case_name,check_dll)
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        self.smart_qc.create_device_node(device_list_node,interface)
        if case_type == 'mc':
            # <Specification>
            specification_path = '..\\Config\\MCSpec.xml'
            self.smart_qc.create_text_node(case_node,'Specification',specification_path)
            # <SpecialInputData>
            special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
            self.smart_qc.create_tag_node(special_input_data_node,'DF01','A0000000041010','AID',None)
        elif case_type == 'visa':
            # <Specification>
            specification_path = '..\\Config\\VISASpec.xml'
            self.smart_qc.create_text_node(case_node,'Specification',specification_path)
            # <SpecialInputData>
            special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
            self.smart_qc.create_tag_node(special_input_data_node,'DF01','A0000000031010','AID',None)
        return case_node

    def create_magstrip_case(self):
        case_node = self.smart_qc.create_case_node('磁条检测','TrackCheck.dll')
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        device_node = self.smart_qc.create_device_node(device_list_node,'KDT4000')
        attrs = dict()
        attrs['id'] = '2'
        self.smart_qc.create_text_node(device_node,'Param','KDTM_MS',**attrs)
        # <Specification>
        self.smart_qc.create_text_node(case_node,'Specification','..\\Config\\TrackSpec.xml')
        # create cross_validation
        self.create_cross_validation('1',str(self.smart_qc.current_case_id))

    def create_cross_validation(self,case1_id,case2_id):
        self.smart_qc.create_node(self.smart_qc.case_list_node,'IgnoreCheckTag57Len')
        cross_node = self.smart_qc.create_node(self.smart_qc.project_node,'CrossValidation')
        attrs = dict()
        attrs['algo'] = 'MatchIC_MS'
        attrs['name'] = 'ic 与磁条数据比对'
        validation_node = self.smart_qc.create_node(cross_node,'Validation',**attrs)
        ic_attrs = dict()
        ic_attrs['name'] = 'IC'
        ic_attrs['QCase'] = case1_id
        ic_attrs['Tag'] = '57'
        ms_attrs = dict()
        ms_attrs['name'] = 'MS'
        ms_attrs['QCase'] = case2_id
        ms_attrs['Tag'] = 'DFA2'
        self.smart_qc.create_node(validation_node,'Param',**ic_attrs)
        self.smart_qc.create_node(validation_node,'Param',**ms_attrs)

    def create_visa_case(self):
        # 创建配置头部信息
        case_node = self._create_header('VISA_TEST','visa','PC Twin','PBOCCheck.dll')
        # <CompareData>
        visa_app_node = self.dp_xml_handle.get_node_by_attribute(self.dp_xml_handle.root_element,'App',aid='A0000000031010')
        node_9104 = self.dp_xml_handle.get_node_by_attribute(visa_app_node,'DGI',name='9104')
        node_tag94 = self.dp_xml_handle.get_node_by_attribute(node_9104,'Tag',name='94')
        tag94 = self.dp_xml_handle.get_attribute(node_tag94,'value')
        dgi_names = self._get_dgis(tag94)

        compared_data = []
        compared_data.extend(self._get_pse_tags())
        compared_data.extend(self._get_dgi_tags('A0000000031010','9102'))
        compared_data.extend(self._get_tags(node_9104))
        for dgi_name in dgi_names:
            node = self.dp_xml_handle.get_node_by_attribute(visa_app_node,'DGI',name=dgi_name)
            compared_data.extend(self._get_tags(node))

        # 获取风险管理数据等..
        dgis = ['3000','3001']
        risk_mgm_tags = []
        for dgi_name in dgis:
            node = self.dp_xml_handle.get_node_by_attribute(visa_app_node,'DGI',name=dgi_name)
            if node:
                risk_mgm_tags.extend(self._get_tags(node))
        compared_data.extend(risk_mgm_tags)
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        for data in compared_data:
            self.smart_qc.create_tag_node(compare_data_node,data[0],data[1],self._get_description(data[0]),'BCD','error')
        risk_tag_list = ''
        for item in risk_mgm_tags:
            tag = item[0]
            if tag not in no_must_contain_list:
                if len(tag) == 2:
                    tag = '00' + tag
                risk_tag_list += tag + ','
        risk_tag_list = risk_tag_list[0:-1] #去掉最后一个逗号
        self.smart_qc.create_text_node(case_node,'MustContain',risk_tag_list)
        # <ShowCardFace>
        self.smart_qc.create_node(case_node,'ShowCardFace')

        # 判断是否有非接数据，并生成非接case
        node_9103 = self.dp_xml_handle.get_node_by_attribute(visa_app_node,'DGI',name='9103')
        if node_9103:
            case_node = self._create_header('VISA非接芯片检测','visa','PC Twin2','PBOCCheck_CL.dll')
            compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
            compared_data = []
            compared_data.extend(self._get_ppse_tags())
            compared_data.extend(self._get_dgi_tags('A0000000031010','9103'))
            for data in compared_data:
                self.smart_qc.create_tag_node(compare_data_node,data[0],data[1],self._get_description(data[0]),'BCD','error')


    def create_mc_case(self):
        # 创建配置头部信息
        case_node = self._create_header('MasterCard检测(接触)','mc','PC Twin','MCCheck.dll')
        # <CompareData>
        mc_app_node = self.dp_xml_handle.get_node_by_attribute(self.dp_xml_handle.root_element,'App',aid='A0000000041010')
        node_A005 = self.dp_xml_handle.get_node_by_attribute(mc_app_node,'DGI',name='A005')
        # node_B005 = self.dp_xml_handle.get_node_by_attribute(mc_app_node,'DGI',name='B005')
        node_tag94 = self.dp_xml_handle.get_node_by_attribute(node_A005,'Tag',name='94')
        tag94 = self.dp_xml_handle.get_attribute(node_tag94,'value')
        dgi_names = self._get_dgis(tag94)

        compared_data = []
        compared_data.extend(self._get_pse_tags())
        compared_data.extend(self._get_dgi_tags('A0000000041010','9102'))
        compared_data.extend(self._get_tags(node_A005))
        # compared_data.extend(self._get_tags(node_B005)) #无法比较非接D8,D9
        for dgi_name in dgi_names:
            node = self.dp_xml_handle.get_node_by_attribute(mc_app_node,'DGI',name=dgi_name)
            compared_data.extend(self._get_tags(node))

        #脱机PIN特殊处理
        has_offline_pin = False
        offline_pin_node = self.dp_xml_handle.get_node_by_attribute(mc_app_node,'DGI',name='9010')
        if offline_pin_node:
            child_nodes = self.dp_xml_handle.get_child_nodes(offline_pin_node)
            if child_nodes and len(child_nodes) == 2:
                has_offline_pin = True
                tag9F17 = self.dp_xml_handle.get_attribute(child_nodes[0],'value')
                tagC6 = self.dp_xml_handle.get_attribute(child_nodes[1],'value')
                compared_data.append(('9F17',tag9F17))
                compared_data.append(('C6',tagC6))
        # 获取风险管理数据等..
        dgis = ['A002','A009','A00E','A012','A013','A014','A015','A022','A023','A024','A025','B002','B011','B012','B013','B014','B015','B016','B017','B018','B019','B01A','',]
        risk_mgm_tags = []
        for dgi_name in dgis:
            node = self.dp_xml_handle.get_node_by_attribute(mc_app_node,'DGI',name=dgi_name)
            if node:
                risk_mgm_tags.extend(self._get_tags(node))
        compared_data.extend(risk_mgm_tags)
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        for data in compared_data: #data为二元组，tag-value的形式
            if data[0] not in no_contain_list:
                if data[0] in warn_list:
                    self.smart_qc.create_tag_node(compare_data_node,data[0],data[1],self._get_description(data[0]),'BCD','warn')
                else:
                    self.smart_qc.create_tag_node(compare_data_node,data[0],data[1],self._get_description(data[0]),'BCD','error')
        risk_tag_list = ''
        for item in risk_mgm_tags:
            tag = item[0]
            if tag not in no_must_contain_list:
                if len(tag) == 2:
                    tag = '00' + tag
                risk_tag_list += tag + ','
        risk_tag_list = risk_tag_list[0:-1] #去掉最后一个逗号
        if has_offline_pin: #将脱机PIN验证加入GetData列表
            risk_tag_list += ',9F17,00C6'
        self.smart_qc.create_text_node(case_node,'MustContain',risk_tag_list)
        # <ShowCardFace>
        self.smart_qc.create_node(case_node,'ShowCardFace')

        # 创建配置头部信息
        case_node = self._create_header('MasterCard检测(非接)','mc','PC Twin2','PBOCCheck_CL.dll')
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        compared_data = []
        compared_data.extend(self._get_ppse_tags())
        compared_data.extend(self._get_dgi_tags('A0000000041010','9102'))
        for data in compared_data:
            self.smart_qc.create_tag_node(compare_data_node,data[0],data[1],self._get_description(data[0]),'BCD','error')


class SmartQC_UICS:
    def __init__(self,cps,project_name):
        self.cps = cps
        self.project_name = project_name
        self.smart_qc = SmartQC(project_name)

    def _get_aid(self):
        '''
        根据PSE中的DGI0101分组获取tag4F
        '''
        dgi = self.cps.get_dgi('PSE')
        dgi_0101_tags = utils.parse_tlv(dgi.get_value('0101'))
        for tag in dgi_0101_tags:
            if tag.tag == '4F':
                return tag.value

    def _get_pse_tag_list(self):
        '''
        获取PSE节点中包含的tag标签列表
        '''
        tlv_list = []
        dgi = self.cps.get_dgi('PSE')
        dgi_0101_tags = utils.parse_tlv(dgi.get_value('0101'))
        dgi_9102_tags = utils.parse_tlv(dgi.get_value('9102'))
        for tag in dgi_0101_tags:
            if tag.is_template is False and tag.len > 0:
                tlv_list.append(tag)
        for tag in dgi_9102_tags:
            if tag.is_template is False and tag.len > 0:
                tlv_list.append(tag)
        return tlv_list

    def _get_ppse_tag_list(self):
        '''
        获取PPSE节点中的tag标签列表
        '''
        tlv_list = []
        dgi = self.cps.get_dgi('PPSE')
        dgi_9102_tags = utils.parse_tlv(dgi.get_value('9102'))
        for tag in dgi_9102_tags:
            if tag.is_template is False and tag.len > 0:
                tlv_list.append(tag)
        return tlv_list

    def _get_dgi_list(self,tag94):
        '''
        根据tag94获取对应的DGI分组
        '''
        dgi_list = []
        dgi = self.cps.get_dgi(tag94)
        tag94 = utils.parse_tlv(dgi.get_value('94'))
        afls = utils.parse_afl(tag94[0].value)
        for afl in afls:
            sfi = utils.int_to_hex_str(afl.sfi)
            record = utils.int_to_hex_str(afl.record_no)
            dgi_list.append(sfi + record)
        return dgi_list

    def _get_dgi_tags(self,dgi):
        '''
        获取指定DGI节点下的tag标签列表
        '''
        tlv_list = []
        dgi_tags = self.cps.get_dgi(dgi)
        if dgi_tags is None:
            return tlv_list
        for _,value in dgi_tags.tag_value_dict.items():
            tags = utils.parse_tlv(value)
            for tag in tags:
                if tag.tag not in no_contain_list and tag.is_template is False:
                    tlv_list.append(tag)
        return tlv_list

    def create_contact_case(self,name,dll,algorithm,dgi_of_afl):       
        case_node = self.smart_qc.create_case_node(name,dll)
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        self.smart_qc.create_device_node(device_list_node)
        # <Specification>
        specification_path = '..\\Config\\UICSSpec.xml'
        if dll == 'PBOCCheck.dll' or dll == 'PBOCCheck_SM.dll':
            specification_path = '..\\Config\\PBOCSpec.xml'

        self.smart_qc.create_text_node(case_node,'Specification',specification_path)
        # <SpecialInputData>
        special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
        
        self.smart_qc.create_tag_node(special_input_data_node,'DF01',self._get_aid(),'AID',None)
        self.smart_qc.create_tag_node(special_input_data_node,'DF69',algorithm,'算法支持指示器',None)
        # <CompareData>
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        pse_tags = self._get_pse_tag_list()
        inter_tags = self._get_dgi_tags('0D01')
        inter_tags.extend(self._get_dgi_tags('0E01'))
        inter_tags.extend(self._get_dgi_tags('3000'))
        inter_tags.extend(self._get_dgi_tags('3001'))
        dgi_list = self._get_dgi_list(dgi_of_afl)
        record_tags = []
        for dgi in dgi_list:
            record_tags.extend(self._get_dgi_tags(dgi))
        tags = pse_tags + record_tags + inter_tags
        for tag in tags:
            desc = tag_desc.get(tag.tag,tag.tag)
            err_level = None
            if tag.tag in warn_list:
                err_level = 'warning'
            if tag.tag == '9F5D' and tag.value == '000000000001':   #9F5D需要特殊处理
                tag.value = '000000000000'
            self.smart_qc.create_tag_node(compare_data_node,tag.tag,tag.value,desc,'BCD',err_level)
        inter_tag_list = ''
        for inter_tag in inter_tags:
            if inter_tag.tag not in no_must_contain_list:
                inter_tag_list += inter_tag.tag + ','
        inter_tag_list = inter_tag_list[0:-1]
        self.smart_qc.create_text_node(case_node,'MustContain',inter_tag_list)
        # <ShowCardFace>
        self.smart_qc.create_node(case_node,'ShowCardFace')

    def create_uics_sm_case(self,sm_gpo_dgi):
        self.create_contact_case('UICS国密接触检测','UICSCheck_SM.dll','01',sm_gpo_dgi)

    def create_uics_des_case(self):
        self.create_contact_case('UICS接触检测','UICSCheck.dll','00','9104')

    def create_pboc_des_case(self):
        self.create_contact_case('PBOC接触检测','PBOCCheck.dll','00','9104')

    def create_pboc_sm_case(self,sm_gpo_dgi):
        self.create_contact_case('PBOC国密接触检测','PBOCCheck_SM.dll','01',sm_gpo_dgi)

    def create_pboc_contactless_case(self):
        self.create_contactless_case('PBOC非接检测','PBOCCheck_CL.dll')
    
    def create_uics_contactless_case(self):
        self.create_contactless_case('UICS非接检测','UICSCheck_CL.dll')

    def create_contactless_case(self,name,dll):
        case_node = self.smart_qc.create_case_node(name,dll)
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        self.smart_qc.create_device_node(device_list_node,'PC Twin2')
        # <Specification>
        specification_path = '..\\Config\\UICSSpec.xml'
        if dll == 'PBOCCheck.dll' or dll == 'PBOCCheck_SM.dll':
            specification_path = '..\\Config\\PBOCSpec.xml'
        self.smart_qc.create_text_node(case_node,'Specification',specification_path)
        # <SpecialInputData>
        special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
        
        self.smart_qc.create_tag_node(special_input_data_node,'DF01',self._get_aid(),'AID',None)
        # <CompareData>
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        ppse_tags = self._get_ppse_tag_list()
        fci_9103 = self._get_dgi_tags('9103')
        tags = ppse_tags + fci_9103
        for tag in tags:
            desc = tag_desc.get(tag.tag,tag.tag)
            self.smart_qc.create_tag_node(compare_data_node,tag.tag,tag.value,desc)

    def create_magstrip_case(self):
        case_node = self.smart_qc.create_case_node('磁条检测','TrackCheck.dll')
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        device_node = self.smart_qc.create_device_node(device_list_node,'KDT4000')
        attrs = dict()
        attrs['id'] = '2'
        self.smart_qc.create_text_node(device_node,'Param','KDTM_MS',**attrs)
        # <Specification>
        self.smart_qc.create_text_node(case_node,'Specification','..\\Config\\TrackSpec.xml')
        self._create_cross_validation()

    def _create_cross_validation(self):
        self.smart_qc.create_node(self.smart_qc.case_list_node,'IgnoreCheckTag57Len')
        cross_node = self.smart_qc.create_node(self.smart_qc.project_node,'CrossValidation')
        attrs = dict()
        attrs['algo'] = 'MatchIC_MS'
        attrs['name'] = 'ic 与磁条数据比对'
        validation_node = self.smart_qc.create_node(cross_node,'Validation',**attrs)
        ic_attrs = dict()
        ic_attrs['name'] = 'IC'
        ic_attrs['QCase'] = '1'
        ic_attrs['Tag'] = '57'
        ms_attrs = dict()
        ms_attrs['name'] = 'MS'
        ms_attrs['QCase'] = str(self.smart_qc.current_case_id) #默认最后一个为检测磁条的case id
        ms_attrs['Tag'] = 'DFA2'
        self.smart_qc.create_node(validation_node,'Param',**ic_attrs)
        self.smart_qc.create_node(validation_node,'Param',**ms_attrs)

    def save(self):
        self.smart_qc.save()


if __name__ == '__main__':
    dp_xml = 'dp_xml.xml'
    check_xml = 'check.xml'
    qc = SmartQC_EMV(dp_xml,check_xml)
    qc.create_mc_case()
    qc.create_magstrip_case()
    qc.save()


    