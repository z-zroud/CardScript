import logging
import importlib
from enum import Enum
from perso_lib import apdu
from perso_lib import utils
from perso_lib.transaction import config
from perso_lib.transaction import auth

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

    def get_tag(self,step,tag=None):
        if tag:
            for tag_info in self.tags_info:
                if tag_info.step == step and tag_info.tag == tag:
                    return tag_info.value
        else:   #若只传递一个参数，则忽略步骤，则不判断取值哪个交易步骤
            tag = step
            for tag_info in self.tags_info:
                if tag_info.tag == tag:
                    return tag_info.value
        return ''

            
    def assemble_dol(self,dol):
        data = ''
        tls = utils.parse_tl(dol)
        for tl in tls:
            data += config.get_terminal(tl.tag,tl.len)
        return data

    def gen_9F4B(self,ddol):
        resp = apdu.internal_auth(ddol)
        if resp.sw != 0x9000:
            logging.info('send internal authentication failed whereby dda failed')
        tlvs = utils.parse_tlv(resp.response)
        if not tlvs:
            logging.info('internal authentication response data can not be break up to tlv format')
            return ''
        if resp.response.startswith('77'):
            if len(tlvs) != 2:
                logging.info('internal authentication response data is not correct')
                return ''
            return tlvs[1].value
        else:
            return tlvs[0].value
            

        

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

    def get_data(self,tags):
        for tag in tags:
            resp = apdu.get_data(tag)
            if resp.sw == 0x9000:
                tlvs = utils.parse_tlv(resp.response)
                self.store_tag_group(PROCESS_STEP.GET_DATA,tlvs)

    def do_dda(self):
        # 获取DDA必须的数据项
        tag84 = self.get_tag(PROCESS_STEP.SELECT,'84')
        tag8F = self.get_tag(PROCESS_STEP.READ_RECORD,'8F')
        tag90 = self.get_tag(PROCESS_STEP.READ_RECORD,'90')
        tag92 = self.get_tag(PROCESS_STEP.READ_RECORD,'92')
        tag9F32 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F32')
        tag9F46 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F46')
        tag9F48 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F48')
        tag9F47 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F47')
        tag9F49 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F49')
        tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
        tag5F24 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F24')
        if not tag84 or len(tag84) < 10:
            logging.info('tag84 is empty or length less than 10 bytes whereby dda failed')
            return False
        if not tag8F:
            logging.info('require tag8F failed whereby dda failed')
            return False
        if not tag90:
            logging.info('require tag90 failed whereby dda failed')
            return False
        if not tag9F32:
            logging.info('require tag9F32 failed whereby dda failed')
            return False
        if not tag9F46:
            logging.info('require tag9F46 failed whereby dda failed')
            return False
        if not tag9F47:
            logging.info('require tag9F47 failed whereby dda failed')
            return False
        if not tag9F49:
            logging.info('require tag9F49 failed whereby dda failed')
            return False
        if not tag5A:
            logging.info('require tag5A failed whereby dda failed')
            return False
        if not tag5F24:
            logging.info('require tag5F24 failed whereby dda failed')
            return False
        # 获取CA 公钥及CA指数
        ca_pub_key,ca_exp = auth.get_ca_pub_key(tag84[0:10],tag8F)
        if not ca_pub_key or not ca_exp:
            logging.info('can not get ca public key')
            return False
        # 验证tag90,获取发卡行公钥
        issuer_pub_key = auth.get_issuer_pub_key(ca_pub_key,ca_exp,tag90,tag92,tag9F32,tag5A,tag5F24)
        if not issuer_pub_key:
            logging.info('can not get issuer public key whereby dda failed')
            return False
        ddol = self.assemble_dol(tag9F49)
        if not ddol:
            logging.info('can not get terminal ddol data whereby dda failed')
            return False
        tag9F4B = self.gen_9F4B(ddol)
        tag9F4A = self.get_tag(PROCESS_STEP.READ_RECORD,'9F4A')
        if tag9F4A:
            tag82 = self.get_tag(PROCESS_STEP.GPO,'82')
            if not tag82:
                logging.info('require tag82 failed whereby dda failed')
                return False
            self.sig_data += tag82
        icc_pub_key = auth.get_icc_pub_key(issuer_pub_key,tag9F32,tag9F46,tag9F48,tag9F47,self.sig_data,tag5A,tag5F24)
        if not icc_pub_key:
            logging.info('can not get icc public key whereby dda failed')
            return False
        if not auth.validate_9F4B(icc_pub_key,tag9F47,ddol,tag9F4B):
            logging.info('validate tag9F4B failed whereby dda failed')
            return False
        return True

    def gac(self,crypto_type,data):
        return apdu.gac(crypto_type,data)

        

