from enum import Enum
import logging
from perso_lib import apdu
from perso_lib import utils
import importlib
from perso_lib.transaction import config

class PROCESS_STEP(Enum):
    SELECT = 0
    GPO = 1
    READ_RECORD = 2
    GET_DATA = 3

class TransTag:
    def __init__(self,step,tag,value):
        self.step = step
        self.tag = tag
        self.value = value

# 交易流程基础类，该类仅实现纯APDU交互，
# 仅涉及每个步骤的实现，并不对步骤直接的关联性做任何处理
class TransBase:
    def __init__(self):
        self.sig_data = ''
        self.tags_info = []

    def run_case(self,module_name,func_name,apdu_resp=None):
        module_name = 'perso_lib.transaction.cases.' + module_name
        mod = importlib.import_module(module_name)
        if mod:
            if hasattr(mod,func_name):
                func = getattr(mod,func_name)
                if apdu_resp:
                    func(self,apdu_resp)
                else:
                    func(self)

    def store_tag(self,step,tag,value):
        self.tags_info.append(TransTag(step,tag,value))

    def store_tag_group(self,step,tlvs):
        for tlv in tlvs:
            if not tlv.is_template:
                self.tags_info.append(TransTag(step,tlv.tag,tlv.value))

    def get_tag(self,step,tag):
        for tag_info in self.tags_info:
            if tag_info.step == step and tag_info.tag == tag:
                return tag_info.value
        return None
            
    def assemble_cdol(self,cdol):
        data = ''
        tls = utils.parse_tl(cdol)
        for tl in tls:
            data += config.get_terminal(tl.tag,tl.len)
        return data
        

    def output_contact_gpo_info(self,apdu_response):
        tab = '    ' #设置缩进为4个空格
        start_tab = '      ' #设置起始输出保留6个空格
        logging.info('send: %s %s %s',apdu_response.request[0:8],apdu_response.request[8:10],apdu_response.request[10:])
        logging.info('recv: %s',apdu_response.response)
        logging.info('sw  : %4X',apdu_response.sw)
        logging.info('tlv :')      
        logging.info("%s<%s>",start_tab,apdu_response.response[0:2])
        logging.info("%s[82]=%s",start_tab + tab,apdu_response.response[4:8])
        logging.info("%s[94]=%s",start_tab + tab,apdu_response.response[8:])

    def output_apdu_response(self,apdu_response):
        tab = '    ' #设置缩进为4个空格
        start_tab = '      ' #设置起始输出保留6个空格
        logging.info('send: %s %s %s',apdu_response.request[0:8],apdu_response.request[8:10],apdu_response.request[10:])
        logging.info('recv: %s',apdu_response.response)
        logging.info('sw  : %4X',apdu_response.sw)
        if apdu_response.response and utils.is_tlv(apdu_response.response):
            logging.info('tlv :')
            tlvs = utils.parse_tlv(apdu_response.response)
            for tlv in tlvs:
                prefix_padding = tab * tlv.level + start_tab
                if tlv.is_template:
                    info = prefix_padding + '<' + tlv.tag + '>'
                else:
                    info = prefix_padding + '[' + tlv.tag + ']=' + tlv.value
                logging.info(info)



    def application_selection(self,aid):
        return apdu.select(aid)

    def gpo(self,pdol):
        return apdu.gpo(pdol)


    def read_record(self,tag94):
        resps = []
        afls = utils.parse_afl(tag94)
        for afl in afls:
            resp = apdu.read_record(afl.sfi,afl.record_no)
            self.output_apdu_response(resp)
            resps.append(resp)
            if afl.is_static_sign_data and resp.sw == 0x9000:
                self.sig_data += utils.remove_template70(resp.response)
        return resps