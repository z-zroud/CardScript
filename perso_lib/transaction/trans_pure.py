
from perso_lib.transaction.trans_base import *
from perso_lib import utils
from perso_lib.apdu import Crypto_Type
from perso_lib.log import Log



class PureTrans(TransBase):
    def __init__(self):
        super().__init__()

    def application_selection(self,aid):
        resp = super().application_selection(aid)
        self.output_apdu_response(resp)
        self.store_tag_group(PROCESS_STEP.SELECT,utils.parse_tlv(resp.response))
        self.run_case('case_application_selection','run_visa',resp)
        return resp

    def gpo(self):
        tag9F38 = self.get_tag(PROCESS_STEP.SELECT,'9F38')
        data = ''
        if tag9F38:
            data = self.assemble_dol(tag9F38)
        resp = super().gpo(data)
        if resp.sw == 0x9000:
            self.output_apdu_response(resp)
            tlvs = utils.parse_tlv(resp.response)
            self.store_tag_group(PROCESS_STEP.GPO,tlvs)
            self.run_case('case_gpo','run_visa',resp)
        return resp

    def read_record(self):
        resps = None
        tag94 = self.get_tag(PROCESS_STEP.GPO,'94')
        if tag94:
            resps = super().read_record(tag94)
            for resp in resps:
                self.store_tag_group(PROCESS_STEP.READ_RECORD,utils.parse_tlv(resp.response))
            self.run_case('case_read_record','run_visa',resps)
        return resps

    def gac1(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        data = self.assemble_dol(tag8C)
        resp = super().gac(Crypto_Type.ARQC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        tlvs = utils.parse_tlv(resp.response)
        self.output_apdu_response(resp)
        self.store_tag_group(PROCESS_STEP.FIRST_GAC,tlvs)
        return resp

    def issuer_auth(self):
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        csu = '00820000' 
        key = self.key_ac
        if self.key_flag == App_Key.MDK:
            tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
            tag5F34 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F34')
            key = auth.gen_udk(key,tag5A,tag5F34)
        
        arpc = auth.gen_arpc_by_mac(key,tag9F26,csu)
        config.set_terminal('91',arpc + csu)


    def gac2(self):
        tag8D = self.get_tag(PROCESS_STEP.READ_RECORD,'8D')
        data = self.assemble_dol(tag8D)
        resp = super().gac(Crypto_Type.TC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        return resp

    def gac_cda(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        data = self.assemble_dol(tag8C)
        resp = super().gac(Crypto_Type.ARQC_CDA,data)


if __name__ == '__main__':
    from perso_lib.pcsc import get_readers,open_reader
    from perso_lib.transaction.config import set_terminal
    from perso_lib.transaction import auth
    from perso_lib.log import Log
    import time

    Log.init()
    set_terminal('UDK','B5DA8C6123075213573EFD0870BCB349FD8C5EEF5E01319D98808C25C416732C89CEFEDC68BAEF68851076978F5E2070')
    set_terminal('OfflineAuth','CDA')
    set_terminal('9F06','A0000000558020')
    set_terminal('5F2A','0036')
    set_terminal('9F40','0000')

    trans = PureTrans()
    readers = get_readers()
    for index,reader in enumerate(readers):
        print("{0}: {1}".format(index,reader))
    index = input('select readers: ')
    if open_reader(readers[int(index)]):
        trans.application_selection('A0000000558020')
        trans.gpo()
        trans.read_record()
        trans.do_dda()
        trans.gac1()
        trans.issuer_auth()
        trans.gac2()
