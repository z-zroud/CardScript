from perso_lib.xml_parse import XmlParser,XmlMode
from perso_lib import utils
from perso_lib import settings
from perso_lib.mock_dp import MockCps
from perso_lib.log import Log

Log.init()

no_contain_list = ['9F46','93','90','92','9F48','9F36','9F6C','8F']
warn_list = ['57','9F1F','5F20','5A']
no_must_contain_list = ['57','5F20','9F6C','5F34','9F36','DF41']

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

    def create_comment_node(self,parent_node,comment):
        self.xml.add_comment(parent_node,comment)


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
    def __init__(self,dp_xml,emboss_file,project_name):
        self.dp_xml = dp_xml
        self.project_name = project_name
        self.smart_qc = SmartQC(project_name)
        self.dp_xml_handle = XmlParser(dp_xml, XmlMode.READ_WRITE)
        self.mock_cps = MockCps(dp_xml,emboss_file)

    def _get_tags(self,node):
        tags = []
        child_nodes = self.dp_xml_handle.get_nodes(node,'Tag')
        for node in child_nodes:
            # value_format = self.dp_xml_handle.get_attribute(node,'type')
            tag = self.dp_xml_handle.get_attribute(node,'name')
            value = self.dp_xml_handle.get_attribute(node,'value')
            if tag == '9F5D' and value == '000000000001':   #9F5D需要特殊处理
                tag.value = '000000000000'
            elif tag != '--' and (value and len(value) > 0 and utils.is_hex_str(value)):
                tags.append((tag,value))
        return tags

    def _get_pse_nodes(self):
        '''
        Get all pse child nodes in dp xml
        '''
        pse_node = self.dp_xml_handle.get_first_node(self.dp_xml_handle.root_element,'PSE')
        return self.dp_xml_handle.get_child_nodes(pse_node,'DGI')

    def _get_ppse_node(self):
        '''
        Get all ppse child nodes in dp xml
        '''
        ppse_node = self.dp_xml_handle.get_first_node(self.dp_xml_handle.root_element,'PPSE')
        return self.dp_xml_handle.get_first_node(ppse_node,'DGI')

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
    
    def _get_desc(self,desc_map,tag):
        if tag in desc_map:
            return desc_map.get(tag)[0]

    def save(self):
        self.smart_qc.save()

    def _create_header(self,case_name,aid,device_name,check_dll,specification_path):
        # <QCase>
        case_node = self.smart_qc.create_case_node(case_name,check_dll)
        # <DeviceList>
        device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
        self.smart_qc.create_device_node(device_list_node,device_name)
        # <Specification>
        self.smart_qc.create_text_node(case_node,'Specification',specification_path)
        # <SpecialInputData>
        special_input_data_node = self.smart_qc.create_node(case_node,'SpecialInputData')
        self.smart_qc.create_tag_node(special_input_data_node,'DF01',aid,'AID',None)
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

    def create_check_aid_case(self,check_aid_list):
            case_node = self.smart_qc.create_case_node('AID检测-非接','SSQCaseEx3.dll')
            # <DeviceList>
            device_list_node = self.smart_qc.create_node(case_node,'DeviceList')
            self.smart_qc.create_device_node(device_list_node,'PC Twin2')
            # <SpecialInput>
            special_input_node = self.smart_qc.create_node(case_node,'SpecialInput')
            # <CardStruct>
            card_struct_node = self.smart_qc.create_node(special_input_node,'CardSturct')
            # <MF>
            self.smart_qc.create_node(card_struct_node,'MF',fid='3F00')
            # <ApduList>
            app_nodes = self.dp_xml_handle.get_child_nodes(self.dp_xml_handle.root_element,'App')
            cur_aids = []
            for app_node in app_nodes:
                aid = self.dp_xml_handle.get_attribute(app_node,'aid')
                if not aid:
                    Log.error('can not get aid from dp xml, check wether the dp xml is correct.')
                    return
                cur_aids.append(aid)
            need_check_aids = []
            for aid in check_aid_list:
                if aid not in cur_aids:
                    need_check_aids.append(aid)
            apdu_list_node = self.smart_qc.create_node(card_struct_node,'ApduList')
            for aid in need_check_aids:
                apdu = '00A40400' + utils.get_strlen(aid) + aid
                self.smart_qc.create_node(apdu_list_node,'Apdu ',value=apdu, sw12="6A82")
            test_process_list_node = self.smart_qc.create_node(case_node,'TestProcessList')
            self.smart_qc.create_node(test_process_list_node,'Card_sturct_test',enable='false')
            self.smart_qc.create_node(test_process_list_node,'Compare_IC_info',enable='false')
            self.smart_qc.create_node(test_process_list_node,'Special_file_test',enable='false')
            self.smart_qc.create_node(test_process_list_node,'Transaction_test',enable='false')
            self.smart_qc.create_node(test_process_list_node,'Check_atr',enable='false')
            self.smart_qc.create_node(test_process_list_node,'ApduList_test',enable='true')

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

    def create_tag_node(self,app_name,dp_dgi_node,compare_node,aid,super_tag_list=[]):
        comment = app_name
        comment += '_' + self.dp_xml_handle.get_attribute(dp_dgi_node,'name') + ' tag '
        tag_nodes = self.dp_xml_handle.get_nodes(dp_dgi_node,'Tag')
        for tag_node in tag_nodes:
            name = self.dp_xml_handle.get_attribute(tag_node,'name')
            if name != '--':
                comment += name + '/'
        # comment node
        self.smart_qc.create_comment_node(compare_node,comment)
        # tag node
        for tag_node in tag_nodes:
            name = self.dp_xml_handle.get_attribute(tag_node,'name')
            value = self.dp_xml_handle.get_attribute(tag_node,'value')
            source = self.dp_xml_handle.get_attribute(tag_node,'type')
            if source == 'kms':
                continue
            if super_tag_list:
                existed = False
                for item in super_tag_list:
                    if item[0] == name:
                        existed = True
                        item[1] = True
                        break
                if not existed:
                    Log.warn('tag %s not be checked in smartQC xml, maybe you need config this tag in your "get_data_list" configration',name)
                    continue
            if source == 'fixed':
                self.smart_qc.create_tag_node(compare_node,name,value,settings.get_mappings_info(aid,name).desc,'BCD','error')
            elif source == 'file':
                _,value = self.mock_cps._parse_tag_value(tag_node)
                self.smart_qc.create_tag_node(compare_node,name,value,settings.get_mappings_info(aid,name).desc,'BCD','warn')

    def create_case(self,configs,check_aid_list=None):
        app_nodes = self.dp_xml_handle.get_child_nodes(self.dp_xml_handle.root_element,'App')
        # handle contact case
        for app_node in app_nodes:
            aid = self.dp_xml_handle.get_attribute(app_node,'aid')
            if not aid:
                Log.error('can not get aid from dp xml, check wether the dp xml is correct.')
                return
            app_type = self.dp_xml_handle.get_attribute(app_node,'type')
            if not app_type:
                Log.warn('can not recognize app type')
                app_type = ''
            app_type += '_conatct_test'
            if aid[:10] not in configs:
                Log.error('can not get configuration of aid %s',aid)
                return
            config = configs[aid[:10]] # get this aid's configuration
            # create header
            case_node = self._create_header(app_type,aid,config['contact_device'],config['contact_dll'],config['contact_spec'])
            if 'dki_cvn' in config:
                self.smart_qc.create_node(case_node,'VerifyTag9F10',pattern=config['dki_cvn'])
            # <CompareData>
            compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
            gpo_node = self.dp_xml_handle.get_node_by_attribute(app_node,'DGI',name=config['gpo_dgi'])
            if not gpo_node:
                Log.error('can not found dgi %s in app node,aid=%s',config['gpo_dgi'],aid)
                return
            afl_node = self.dp_xml_handle.get_node_by_attribute(gpo_node,'Tag',name=config['afl_tag'])
            if not afl_node:
                Log.error('can not found tag %s in dgi %s',config['afl_tag'],config['gpo_dgi'])
                return
            afl_tag = self.dp_xml_handle.get_attribute(afl_node,'value')
            if not afl_tag:
                Log.error('tag %s is empty',config['afl_tag'])
                return
            dgi_names = self._get_dgis(afl_tag)

            # pse tags
            pse_nodes = self._get_pse_nodes()
            for node in pse_nodes:
                self.create_tag_node('pse',node,compare_data_node,'315041592E5359532E4444463031')
            fci_node = self.dp_xml_handle.get_node_by_attribute(app_node,'DGI',name=config['contact_fci_dgi'])
            if not fci_node:
                Log.error('can not found dgi %s in app node',config['contact_fci_dgi'])
                return
            # app fci tags
            self.create_tag_node(app_type,fci_node,compare_data_node,aid)
            # app gpo tags
            self.create_tag_node(app_type,gpo_node,compare_data_node,aid)
            # app record tags
            for dgi_name in dgi_names:
                node = self.dp_xml_handle.get_node_by_attribute(app_node,'DGI',name=dgi_name)
                self.create_tag_node(app_type,node,compare_data_node,aid)
            # risk management tags
            internal_dgis = config['risk_dgi_list']
            get_data_tags = [[tag,False] for tag in config['get_data_tags']]

            risk_tags = ''
            for dgi_name in internal_dgis:
                node = self.dp_xml_handle.get_node_by_attribute(app_node,'DGI',name=dgi_name)
                if node:
                    self.create_tag_node(app_type,node,compare_data_node,aid,get_data_tags)
            for item in get_data_tags:
                tag = item[0]
                has_check = item[1]
                if not has_check:
                    Log.error('can not get tag %s in dp xml,check the "get_data_tags" configuration',tag)
                else:
                    if len(tag) == 2:
                        tag = '00' + tag
                    risk_tags += tag + ','
            if not risk_tags:
                Log.error('MustContain node is empty')
                return
            risk_tags = risk_tags[0:-1]
            # <MustConatin>
            self.smart_qc.create_text_node(case_node,'MustContain',risk_tags)
            # <ShowCardFace>
            self.smart_qc.create_node(case_node,'ShowCardFace')
        # handle contactless case
        for app_node in app_nodes:
            aid = self.dp_xml_handle.get_attribute(app_node,'aid')
            if not aid:
                Log.error('can not get aid from dp xml, check wether the dp xml is correct.')
                return
            if aid in ('315041592E5359532E4444463031','325041592E5359532E4444463031'):
                continue
            app_type = self.dp_xml_handle.get_attribute(app_node,'type')
            if not app_type:
                Log.warn('can not recognize app type')
                app_type = ''
            app_type += '_conatctless_test'
            if aid[:10] not in configs:
                Log.error('can not configuration of aid %s',aid)
                return
            config = configs[aid[:10]] # get this aid's configuration

            # 判断是否有非接数据，并生成非接case
            fci_dgi_node = self.dp_xml_handle.get_node_by_attribute(app_node,'DGI',name=config['contactless_fci_dgi'])
            if fci_dgi_node:
                case_node = self._create_header(app_type,aid,config['contactless_device'],config['contactless_dll'],config['contactless_spec'])
                compare_data_node = self.smart_qc.create_node(case_node,'CompareData')
                ppse_child_node = self._get_ppse_node()
                self.create_tag_node('ppse',ppse_child_node,compare_data_node,'325041592E5359532E4444463031')
                self.create_tag_node(app_type,fci_dgi_node,compare_data_node,aid)

        # check aid list
        if check_aid_list:
            self.create_check_aid_case(check_aid_list)


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
            # desc = tag_desc.get(tag.tag,tag.tag)
            desc = ''
            if tag.tag in settings.uics_tag_desc_mappings:
                desc = settings.uics_tag_desc_mappings.get(tag.tag)[0]
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
            # desc = tag_desc.get(tag.tag,tag.tag)
            desc = ''
            if tag.tag in settings.uics_tag_desc_mappings:
                desc = settings.uics_tag_desc_mappings.get(tag.tag)[0]
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