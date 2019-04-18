
from perso_lib.transaction.trans_base import *
from perso_lib import utils
from perso_lib.apdu import Crypto_Type
from perso_lib.log import Log
from perso_lib.transaction.utils import terminal,auth,tools
from perso_lib.transaction.utils.property import App_Master_Key,PROCESS_STEP,TransTag

class PureTrans(TransBase):
    def __init__(self):
        super().__init__()

    def run_case(self,module_name,apdu_resp=None):
        super().run_case(module_name,'run_pure',apdu_resp)

    def application_selection(self,aid):
        resp = super().application_selection(aid)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.SELECT,utils.parse_tlv(resp.response))
        self.run_case('case_application_selection',resp)
        return resp

    def gpo(self):
        tag9F38 = self.get_tag(PROCESS_STEP.SELECT,'9F38')
        pdol = ''
        if tag9F38:
            pdol = tools.assemble_dol(tag9F38)
        resp = super().gpo(pdol)
        if resp.sw == 0x9000:
            tools.output_apdu_info(resp)
            tlvs = utils.parse_tlv(resp.response)
            self.store_tag_group(PROCESS_STEP.GPO,tlvs)
            self.run_case('case_gpo',resp)
        return resp

    def read_record(self):
        resps = None
        tag94 = self.get_tag(PROCESS_STEP.GPO,'94')
        if tag94:
            resps = super().read_record(tag94)
            for resp in resps:
                self.store_tag_group(PROCESS_STEP.READ_RECORD,utils.parse_tlv(resp.response))
            self.run_case('case_read_record',resps)
        return resps

    def first_gac(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        data = tools.assemble_dol(tag8C)
        resp = super().gac(Crypto_Type.ARQC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        tlvs = utils.parse_tlv(resp.response)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.FIRST_GAC,tlvs)
        self.divert_key() # First GAC之后需要分散应用秘钥，后续case将会使用到
        self.run_case('case_first_gac',resp)
        return resp

    def divert_key(self):
        if self.key_flag == App_Master_Key.MDK:
            tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
            tag5F34 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F34')
            self.key_ac = auth.gen_udk(self.key_ac,tag5A,tag5F34)
            self.key_mac = auth.gen_udk(self.key_mac,tag5A,tag5F34)
            self.key_enc = auth.gen_udk(self.key_enc,tag5A,tag5F34)
        tag9F36 = self.get_tag('9F36')
        self.session_key_ac = auth.gen_udk_session_key_emv(self.key_ac,tag9F36)
        self.session_key_mac = auth.gen_udk_session_key_emv(self.key_mac,tag9F36)
        self.session_key_enc = auth.gen_udk_session_key_emv(self.key_enc,tag9F36)
        
    def issuer_auth(self):
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        csu = '00820000' 
        arpc = auth.gen_arpc_by_mac(self.session_key_ac,tag9F26,csu)
        terminal.set_terminal('91',arpc + csu)

    def second_gac(self):
        tag8D = self.get_tag(PROCESS_STEP.READ_RECORD,'8D')
        data = tools.assemble_dol(tag8D)
        resp = super().gac(Crypto_Type.TC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        return resp

    def first_gac_cda(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        if not tag8C:
            Log.error('first gac cda faild since tag8C is tempty')
            return False
        tls = utils.parse_tl(tag8C)
        data = ''
        self.unpredicatble_number = ''
        for tl in tls:
            data += terminal.get_terminal(tl.tag,tl.len)
            if tl.tag == '9F37':
                self.unpredicatble_number = terminal.get_terminal(tl.tag,tl.len)
        resp = super().gac(Crypto_Type.TC_CDA,data)
        if resp.sw != 0x9000:
            Log.error('send first gac command failed. SW:%04X',resp.sw)
            return
        tlvs = utils.parse_tlv(resp.response)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.FIRST_GAC,tlvs)


if __name__ == '__main__':
    from perso_lib.pcsc import get_readers,open_reader
    from perso_lib.transaction.utils import terminal,auth,tools
    from perso_lib.transaction.utils.property import App_Master_Key,PROCESS_STEP,TransTag
    from perso_lib.log import Log
    from perso_lib.transaction.trans_pse import PseTrans,PpseTrans
    import time

    Log.init()
    terminal.set_terminal(App_Master_Key.UDK,'B5DA8C6123075213573EFD0870BCB349FD8C5EEF5E01319D98808C25C416732C89CEFEDC68BAEF68851076978F5E2070')
    terminal.set_terminal('9F06','A0000000558020')
    terminal.set_terminal('5F2A','0036')
    terminal.set_terminal('9F40','0000')
    terminal.set_terminal('C7','2600000059') # 非接，联机Pin交易,支持SDA,CDA,支持CVM
    # terminal.set_terminal('C7','2600000059') # 非接，脱机交易,支持SDA,CDA,支持CVM

    trans = PureTrans()
    readers = get_readers()
    for index,reader in enumerate(readers):
        print("{0}: {1}".format(index,reader))
    index = input('select readers: ')
    if open_reader(readers[int(index)]):
        pse_trans = PseTrans()
        pse_trans.application_selection()
        aids = pse_trans.read_record()
        for index,aid in enumerate(aids):
            print("{0}: {1}".format(index,aid))
        aid_index = input('select app to do transaction:')
        trans.application_selection(aids[int(aid_index)])
        trans.gpo()
        trans.read_record()
        # trans.do_dda()
        trans.first_gac_cda()
        trans.do_cda()
        # trans.first_gac()
        # trans.issuer_auth()
        # trans.second_gac()
