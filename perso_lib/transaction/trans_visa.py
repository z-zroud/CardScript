
from perso_lib.transaction.trans_base import *
from perso_lib import utils
from perso_lib.apdu import Crypto_Type
from perso_lib.log import Log



class VisaTrans(TransBase):
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
            self.output_contact_gpo_info(resp)
            self.store_tag(PROCESS_STEP.GPO,'82',resp.response[4:8])
            self.store_tag(PROCESS_STEP.GPO,'94',resp.response[8:])
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
        if len(tlvs) != 1 and tlvs[0].tag != '80':
            Log.info('gac1 response data error')
        data = tlvs[0].value
        self.store_tag(PROCESS_STEP.FIRST_GAC,'9F27',data[0:2])
        self.store_tag(PROCESS_STEP.FIRST_GAC,'9F36',data[2:6])
        self.store_tag(PROCESS_STEP.FIRST_GAC,'9F26',data[6:22])
        self.store_tag(PROCESS_STEP.FIRST_GAC,'9F10',data[22:])
        return resp

    def issuer_auth(self):
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        arc = '3030'
        key = self.key_ac
        if self.key_flag == App_Key.MDK:
            tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
            tag5F34 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F34')
            key = auth.gen_udk(key,tag5A,tag5F34)
        arpc = auth.gen_arpc_by_des3(key,tag9F26,arc)
        resp = apdu.external_auth(arpc,arc)
        if resp.sw == 0x9000:
            return True
        return False


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
    from perso_lib.log import Log
    import time
    a = [1,2,3,4,5,6]
    print(a[2:-2])
    print(time.strftime('%C%m'))
    # print(time.strftime("%d/%m/%Y"))
    Log.init()
    set_terminal('UDK','CB40040401DABCBCC197FE2A01AD15B961CEE091A267BA6EFBB329A262B97616E01F7F3E7904641AE3862A07943276AE')
    trans = VisaTrans()
    readers = get_readers()
    for index,reader in enumerate(readers):
        print("{0}: {1}".format(index,reader))
    index = input('select readers: ')
    if open_reader(readers[int(index)]):
        trans.application_selection('A0000000031010')
        trans.gpo()
        trans.read_record()
        trans.get_data(['9F75','9F72'])
        trans.do_dda()
        trans.gac1()
        trans.issuer_auth()
        trans.gac2()
