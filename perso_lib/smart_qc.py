from perso_lib.xml_parse import XmlParser,XmlMode
from perso_lib import data_parse
from perso_lib import utils

no_contain_list = ['9F46','93','90','92','9F48','9F36']
warn_list = ['57','9F1F','5F20','5A']

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
    '9F72':'Consecutive Transaction Limit (International-Country)',
    '9F75':'Cumulative Total Transaction Amount Limit Dual Currency',
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
}

class SmartQC:
    def __init__(self,file_name):
        self.file_name = file_name
        self.xml = XmlParser(file_name,XmlMode.WRITE)
        self._create_project_node()
        self._create_case_list_node()

    def _create_project_node(self):
        self.project_node = self.xml.create_root_element('Project')
        return self.project_node

    def _create_case_list_node(self):
        self.case_list_node = self.xml.add_node(self.project_node,'QCaseList')
        return self.case_list_node

    def create_case_node(self,id,name,dll='UICSCheck.dll',class_type='pboc_test'):
        attrs = dict()
        attrs['1'] = ('id',id)
        attrs['2'] = ('name',name)
        attrs['3'] = ('dll',dll)
        attrs['4'] = ('class',class_type)
        return self.xml.add_node(self.case_list_node,'QCase',**attrs)

    def create_device_node(self,parent_node,name="PC Twin"):
        attrs = dict()
        attrs['1'] = ('name',name)
        attrs['2'] = ('remark','')
        return self.xml.add_node(parent_node,'Device',**attrs)

    def create_node(self,parent_node,node_name,**attrs):
        return self.xml.add_node(parent_node,node_name,**attrs)

    def create_text_node(self,parent_node,node_name,text,**attrs):
        node = self.xml.add_node(parent_node,node_name,**attrs)
        self.xml.add_text(node,text)

    def create_tag_node(self,parent_node,tag,text,desc,algorithm='BCD',err_level=None):
        attrs = dict()
        attrs['1'] = ('name',tag)
        attrs['2'] = ('description',desc)
        if algorithm is not None:
            attrs['3'] = ('algorithm',algorithm)
        if err_level is not None:
            attrs['4'] = ('errLevel',err_level)
        tag_node = self.xml.add_node(parent_node,'Tag',**attrs)
        self.xml.add_text(tag_node,text)
        return tag_node

    def save(self):
        self.xml.save()


class SmartQC_UICS:
    def __init__(self,cps,project_name):
        self.cps = cps
        self.project_name = project_name
        self.smart_qc = SmartQC(project_name)

    def _get_aid(self):
        dgi = self.cps.get_dgi('PSE')
        dgi_0101_tags = data_parse.parse_tlv(dgi.get_value('0101'))
        for tag in dgi_0101_tags:
            if tag.tag == '4F':
                return tag.value

    def _get_pse_dgi_list(self):
        tlv_list = []
        dgi = self.cps.get_dgi('PSE')
        dgi_0101_tags = data_parse.parse_tlv(dgi.get_value('0101'))
        dgi_9102_tags = data_parse.parse_tlv(dgi.get_value('9102'))
        for tag in dgi_0101_tags:
            if tag.is_template is False and tag.len > 0:
                tlv_list.append(tag)
        for tag in dgi_9102_tags:
            if tag.is_template is False and tag.len > 0:
                tlv_list.append(tag)
        return tlv_list

    def _get_ppse_dgi_list(self):
        tlv_list = []
        dgi = self.cps.get_dgi('PPSE')
        dgi_9102_tags = data_parse.parse_tlv(dgi.get_value('9102'))
        for tag in dgi_9102_tags:
            if tag.is_template is False and tag.len > 0:
                tlv_list.append(tag)
        return tlv_list

    def _get_dgi_list(self,dgi_of_afl):
        dgi_list = []
        dgi = self.cps.get_dgi(dgi_of_afl)
        tag94 = data_parse.parse_tlv(dgi.get_value('94'))
        afls = data_parse.parse_afl(tag94[0].value)
        for afl in afls:
            sfi = utils.int_to_hex_str(afl.sfi)
            record = utils.int_to_hex_str(afl.record_no)
            dgi_list.append(sfi + record)
        return dgi_list

    def _get_dgi_tags(self,dgi):
        tlv_list = []
        dgi_tags = self.cps.get_dgi(dgi)
        for _,value in dgi_tags.tag_value_dict.items():
            tag = data_parse.parse_tlv(value)
            if tag[0].tag not in no_contain_list:
                tlv_list.append(tag[0])
        return tlv_list

    def create_contact_case(self,case_id,name,algorithm,dgi_of_afl):       
        case_node = self.smart_qc.create_case_node(case_id,name)
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        self.smart_qc.create_device_node(device_list_node)
        # <Specification>
        self.smart_qc.create_text_node(case_node,'Specification','..\\Config\\UICSSpec.xml')
        # <SpecialInputData>
        special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
        
        self.smart_qc.create_tag_node(special_input_data_node,'DF01',self._get_aid(),'AID',None)
        self.smart_qc.create_tag_node(special_input_data_node,'DF69',algorithm,'算法支持指示器',None)
        # <CompareData>
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        pse_tags = self._get_pse_dgi_list()
        inter_tags = self._get_dgi_tags('0D01')
        inter_tags.extend(self._get_dgi_tags('0E01'))
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
            self.smart_qc.create_tag_node(compare_data_node,tag.tag,tag.value,desc,'BCD',err_level)
        inter_tag_list = ''
        for inter_tag in inter_tags:
            inter_tag_list += inter_tag.tag + ','
        inter_tag_list = inter_tag_list[0:-1]
        self.smart_qc.create_text_node(case_node,'MustContain',inter_tag_list)
        # <ShowCardFace>
        self.smart_qc.create_node(case_node,'ShowCardFace')

    def create_uics_sm_case(self,case_id,dgi_of_afl):
        self.create_contact_case(case_id,'UICS国密接触检测','01',dgi_of_afl)

    def create_uics_des_case(self,case_id):
        self.create_contact_case(case_id,'UICS接触检测','00','9104')

    def create_contactless_case(self,case_id,name):
        case_node = self.smart_qc.create_case_node(case_id,name,'UICSCheck_CL.dll')
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        self.smart_qc.create_device_node(device_list_node,'PC Twin2')
        # <Specification>
        self.smart_qc.create_text_node(case_node,'Specification','..\\Config\\UICSSpec.xml')
        # <SpecialInputData>
        special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
        
        self.smart_qc.create_tag_node(special_input_data_node,'DF01',self._get_aid(),'AID',None)
        # <CompareData>
        compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
        ppse_tags = self._get_ppse_dgi_list()
        fci_9103 = self._get_dgi_tags('9103')
        tags = ppse_tags + fci_9103
        for tag in tags:
            desc = tag_desc.get(tag.tag,tag.tag)
            self.smart_qc.create_tag_node(compare_data_node,tag.tag,tag.value,desc)

    def create_magstrip_case(self,case_id):
        case_node = self.smart_qc.create_case_node(case_id,'磁条检测','TrackCheck.dll')
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        device_node = self.smart_qc.create_device_node(device_list_node,'KDT4000')
        attrs = dict()
        attrs['1'] = ('id','2')
        self.smart_qc.create_text_node(device_node,'Param','KDTM_MS',**attrs)
        # <Specification>
        self.smart_qc.create_text_node(case_node,'Specification','..\\Config\\TrackSpec.xml')

    def create_cross_validation(self,case1_id,case2_id):
        cross_node = self.smart_qc.create_node(self.smart_qc.project_node,'CrossValidation')
        attrs = dict()
        attrs['1'] = ('algo','MatchIC_MS')
        attrs['2'] = ('name','ic 与磁条数据比对')
        validation_node = self.smart_qc.create_node(cross_node,'Validation',**attrs)
        ic_attrs = dict()
        ic_attrs['1'] = ('name','IC')
        ic_attrs['2'] = ('QCase',case1_id)
        ic_attrs['3'] = ('Tag','57')
        ms_attrs = dict()
        ms_attrs['1'] = ('name','MS')
        ms_attrs['2'] = ('QCase',case2_id)
        ms_attrs['3'] = ('Tag','DFA2')
        self.smart_qc.create_node(validation_node,'Param',**ic_attrs)
        self.smart_qc.create_node(validation_node,'Param',**ms_attrs)

    def save(self):
        self.smart_qc.save()


    