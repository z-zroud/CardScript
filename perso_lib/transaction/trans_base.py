import importlib
from enum import Enum
from perso_lib import apdu
from perso_lib import utils
from perso_lib.log import Log
from perso_lib.transaction.utils import terminal,auth,tools
from perso_lib.transaction.utils.property import App_Master_Key,PROCESS_STEP,TransTag

# 交易流程基础类，该类仅实现纯APDU交互，
# 仅涉及每个步骤的实现，并不对步骤直接的关联性做任何处理
class TransBase:
    def __init__(self):
        self.pse = None     # 将PSE/PPSE对象作为主应用的一部分，用于检测PSE与主应用之间的关联性
        self.ppse = None
        self.sig_data = ''  #读记录中的签名数据，包含tag82
        self.tags_info = [] #存储每个交易步骤中的tag信息
        self.cvn = ''       # CVN
        self.dki = ''       # DKI
        self.key_ac = ''    # AC Master Key
        self.key_mac = ''   # MAC Master Key
        self.key_enc = ''   # ENC Master Key
        self.key_flag = App_Master_Key.UDK # Master Key Type
        self.unpredicatble_number = '' # CDA时，需要缓存该数据
        key = terminal.get_terminal(App_Master_Key.UDK)
        if key:
            self.key_ac = key[0:32]
            self.key_mac = key[32:64]
            self.key_enc = key[64:96]
            self.key_flag = App_Master_Key.UDK
        else:
            key = terminal.get_terminal(App_Master_Key.MDK)
            if key:
                self.key_ac = key[0:32]
                self.key_mac = key[32:64]
                self.key_enc = key[64:96]
                self.key_flag = App_Master_Key.MDK
        self.session_key_mac = ''   # First GAC后进行分散处理
        self.session_key_enc = ''
        self.session_key_ac = ''

    def run_case(self,module_name,func_name,apdu_resp=None):
        '''
        执行case函数
        '''
        names = func_name.split('_')    # 这里约定执行case的主函数名称为run_xxx, xxx为特定应用的文件夹名称
        module_name = 'perso_lib.transaction.cases.' + names[1] + '.' + module_name
        mod = importlib.import_module(module_name)
        if mod:
            if hasattr(mod,func_name):
                func = getattr(mod,func_name)
                if apdu_resp:
                    func(self,apdu_resp)
                else:
                    func(self)

    def store_tag(self,step,tag,value):
        '''
        存储交易中的tag信息
        '''
        self.tags_info.append(TransTag(step,tag,value))

    def store_tag_group(self,step,tlvs):
        '''
        存储交易中的一组tag信息
        '''
        for tlv in tlvs:
            if not tlv.is_template:
                self.tags_info.append(TransTag(step,tlv.tag,tlv.value))

    def get_tag(self,step,tag=None):
        '''
        获取tag,若仅传递一个参数，则那个参数就是tag,历史原因，这里不将参数tag和step互调
        '''
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
       
    def gen_9F4B(self,ddol):
        '''
        发送内部认证命令，卡片生成tag9F4B动态签名数据
        '''
        resp = apdu.internal_auth(ddol)
        if resp.sw != 0x9000:
            Log.error('SW: %0X',resp.sw)
            Log.error('send internal authentication apdu command failed whereby dda/cda failed')
            return ''
        tlvs = utils.parse_tlv(resp.response)
        if not tlvs:
            Log.error('response: %s',resp.response)
            Log.error('internal authentication response data can not be breaked up to tlv format')
            return ''
        # 返回的APDU可能是模板77或者80
        if resp.response.startswith('77'):
            if len(tlvs) != 2:
                Log.error('response: %s',resp.response)
                Log.error('internal authentication response data is not correct')
                return ''
            return tlvs[1].value
        elif resp.response.startswith('80'):
            return tlvs[0].value
        else:
            Log.error('response: %s',resp.response)
            Log.error('internal authentication response data is not startwith 70/80')
        return ''
            

    def application_selection(self,aid):
        '''
        应用选择
        '''
        return apdu.select(aid)

    def gpo(self,pdol):
        '''
        GPO 应用初始化
        '''
        return apdu.gpo(pdol)


    def read_record(self,tag94):
        '''
        读记录数据
        '''
        resps = []
        afls = utils.parse_afl(tag94)
        for afl in afls:
            Log.info('read record: %02X%02X',afl.sfi,afl.record_no)
            resp = apdu.read_record(afl.sfi,afl.record_no)
            if resp.sw != 0x9000:
                Log.error('read record wrong')
                return resps
            tools.output_apdu_info(resp)
            resps.append(resp)
            if afl.is_static_sign_data:
                self.sig_data += utils.remove_template70(resp.response)
        return resps

    def get_data(self,tags):
        for tag in tags:
            resp = apdu.get_data(tag)
            if resp.sw == 0x9000:
                tlvs = utils.parse_tlv(resp.response)
                self.store_tag_group(PROCESS_STEP.GET_DATA,tlvs)

    def _get_issuer_pub_key(self):
        '''
        恢复发卡行公钥
        '''
        issuer_pub_key = ''
        tag84 = self.get_tag(PROCESS_STEP.SELECT,'84')
        tag8F = self.get_tag(PROCESS_STEP.READ_RECORD,'8F')
        tag90 = self.get_tag(PROCESS_STEP.READ_RECORD,'90')
        tag92 = self.get_tag(PROCESS_STEP.READ_RECORD,'92')
        tag9F32 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F32')
        tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
        tag5F24 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F24')
        if not tag84 or len(tag84) < 10:
            Log.error('tag84: %s',tag84)
            Log.error('tag84 is empty or length less than 10 bytes whereby dda failed')
            return issuer_pub_key
        if not tag8F:
            Log.error('tag8F: %s',tag8F)
            Log.info('require tag8F failed whereby dda failed')
            return issuer_pub_key
        if not tag90:
            Log.error('tag90: %s',tag90)
            Log.info('require tag90 failed whereby dda failed')
            return issuer_pub_key
        if not tag9F32:
            Log.error('tag9F32: %s',tag9F32)
            Log.info('require tag9F32 failed whereby dda failed')
            return issuer_pub_key
        if not tag5A:
            Log.error('tag5A: %s',tag5A)
            Log.info('require tag5A failed whereby dda failed')
            return issuer_pub_key
        if not tag5F24:
            Log.error('tag5F24: %s',tag5F24)
            Log.info('require tag5F24 failed whereby dda failed')
            return issuer_pub_key
        # 验证tag90,获取发卡行公钥
        # 获取CA 公钥及CA指数
        ca_pub_key,ca_exp = auth.get_ca_pub_key(tag84[0:10],tag8F)
        if not ca_pub_key or not ca_exp:
            Log.error('rid: %s index: %s ',tag84[0:10],tag8F)
            Log.error('can not get ca public key, make sure this root ca existed, please check pcsc.db file')
            return issuer_pub_key
        issuer_pub_key = auth.get_issuer_pub_key(ca_pub_key,ca_exp,tag90,tag92,tag9F32,tag5A,tag5F24)
        if not issuer_pub_key:
            Log.error('CA public key: %s',ca_pub_key)
            Log.error('CA exp: %s',ca_exp)
            Log.error('tag90: %s',tag90)
            Log.error('tag92: %s',tag92)
            Log.error('tag9F32: %s',tag9F32)
            Log.error('tag5A: %s',tag5A)
            Log.error('tag5F24: %s',tag5F24)
            Log.info('can not get issuer public key whereby dda failed')
            return ''
        return issuer_pub_key

    def _get_icc_pub_key(self,issuer_pub_key):
        icc_pub_key = ''
        tag9F32 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F32')
        tag9F46 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F46')
        tag9F48 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F48')
        tag9F47 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F47')
        tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
        tag5F24 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F24')
        
        if not tag9F46:
            Log.error('tag9F46: %s',tag9F46)
            Log.error('require tag9F46 failed whereby dda failed')
            return icc_pub_key
        if not tag9F47:
            Log.error('tag9F47: %s',tag9F47)
            Log.error('require tag9F47 failed whereby dda failed')
            return icc_pub_key
        if not tag5A:
            Log.error('tag5A: %s',tag5A)
            Log.error('require tag5A failed whereby dda failed')
            return icc_pub_key
        if not tag5F24:
            Log.error('tag5F24: %s',tag5F24)
            Log.error('require tag5F24 failed whereby dda failed')
            return icc_pub_key
        if not tag9F32:
            Log.error('tag9F32: %s',tag9F32)
            Log.info('require tag9F32 failed whereby dda failed')
            return issuer_pub_key
        tag9F4A = self.get_tag(PROCESS_STEP.READ_RECORD,'9F4A')
        if tag9F4A:
            tag82 = self.get_tag(PROCESS_STEP.GPO,'82')
            if not tag82:
                Log.error('require tag82 failed whereby dda failed')
                return icc_pub_key
            self.sig_data += tag82
        icc_pub_key = auth.get_icc_pub_key(issuer_pub_key,tag9F32,tag9F46,tag9F48,tag9F47,self.sig_data,tag5A,tag5F24)
        if not icc_pub_key:
            Log.error('issuer public key: %s',issuer_pub_key)
            Log.error('tag9F32: %s',tag9F32)
            Log.error('tag9F46: %s',tag9F46)
            Log.error('tag9F47: %s',tag9F47)
            Log.error('sig data: %s',self.sig_data)
            Log.error('tag5A: %s',tag5A)
            Log.error('tag5F24: %s',tag5F24)
            Log.error('can not get icc public key whereby dda failed')
            return ''
        return icc_pub_key

    def do_dda(self):
        tag9F47 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F47')
        tag9F49 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F49')
        if not tag9F47:
            Log.error('tag9F47: %s',tag9F47)
            Log.error('require tag9F47 failed whereby dda failed')
            return False
        if not tag9F49:
            Log.error('tag9F49: %s',tag9F49)
            Log.error('require tag9F49 failed whereby dda failed')
            return False
        ddol = tools.assemble_dol(tag9F49)
        if not ddol:
            Log.error('tag9F49: %s',tag9F49)
            Log.error('can not get terminal ddol data whereby dda failed')
            return False
        tag9F4B = self.gen_9F4B(ddol)
        if not tag9F4B:
            Log.error('can not get tag9F4B data whereby dda failed')
            return False
        issuer_pub_key = self._get_issuer_pub_key()
        if not issuer_pub_key:
            Log.error('get issuer public key failed where by dda failed.')
            return False
        icc_pub_key = self._get_icc_pub_key(issuer_pub_key)
        if not icc_pub_key:
            Log.error('get icc public key failed where by dda failed.')
            return False
        if not auth.validate_9F4B(icc_pub_key,tag9F47,ddol,tag9F4B):
            Log.error('icc public key: %s',icc_pub_key)
            Log.error('tag9F47: %s',tag9F47)
            Log.error('ddol data: %s',ddol)
            Log.error('tag9F4B: %s',tag9F4B)
            Log.error('validate tag9F4B failed whereby dda failed')
            return False
        Log.info('dda authentication sucess.')
        return True

    
    def do_cda(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        tag9F47 = self.get_tag(PROCESS_STEP.READ_RECORD,'9F47')
        tag9F4B = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F4B')
        if not tag8C:
            Log.error('tag8C: %s',tag8C)
            Log.error('require tag8C failed whereby dda failed')
            return False
        if not tag9F47:
            Log.error('tag9F47: %s',tag9F47)
            Log.error('require tag9F47 failed whereby dda failed')
            return False
        if not tag9F4B:
            Log.error('tag9F4B: %s',tag9F4B)
            Log.error('require tag9F4B failed whereby dda failed')
            return False
        issuer_pub_key = self._get_issuer_pub_key()
        if not issuer_pub_key:
            Log.error('get issuer public key failed where by cda failed.')
            return False
        icc_pub_key = self._get_icc_pub_key(issuer_pub_key)
        if not icc_pub_key:
            Log.error('get icc public key failed where by cda failed.')
            return False
        sig_data = self.unpredicatble_number
        if not auth.validate_9F4B(icc_pub_key,tag9F47,sig_data,tag9F4B):
            Log.error('icc public key: %s',icc_pub_key)
            Log.error('tag9F47: %s',tag9F47)
            Log.error('tag9F4B: %s',tag9F4B)
            Log.error('validate tag9F4B failed whereby cda failed')
            return False
        Log.info('cda authentication sucess.')
        return True

    def gac(self,crypto_type,data):
        '''
        GAC
        '''
        return apdu.gac(crypto_type,data)

