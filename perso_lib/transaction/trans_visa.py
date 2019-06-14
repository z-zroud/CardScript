
from perso_lib.transaction.trans_base import *
from perso_lib.transaction.trans_pse import PseTrans,PpseTrans
from perso_lib import utils
from perso_lib import algorithm
from perso_lib.apdu import Crypto_Type
from perso_lib.log import Log
from perso_lib.transaction.utils import terminal,auth,tools
from perso_lib.transaction.utils.property import App_Master_Key,PROCESS_STEP,TransTag

class VisaTrans(TransBase):
    def __init__(self):
        super().__init__()

    def application_selection(self,aid):
        resp = super().application_selection(aid)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.SELECT,utils.parse_tlv(resp.response))
        self.run_case('case_application_selection','run_visa',resp)
        return resp

    def gpo_VSDC(self):
        tag9F38 = self.get_tag(PROCESS_STEP.SELECT,'9F38')
        data = ''
        if tag9F38:
            data = tools.assemble_dol(tag9F38)
        resp = super().gpo(data)
        if resp.sw == 0x9000:
            tools.output_not_tlv_gpo_info(resp)
            self.store_tag(PROCESS_STEP.GPO,'82',resp.response[4:8])
            self.store_tag(PROCESS_STEP.GPO,'94',resp.response[8:])
            self.run_case('case_gpo','run_visa',resp)
        return resp

    def gpo_qVSDC(self):
        tag9F38 = self.get_tag(PROCESS_STEP.SELECT,'9F38')
        data = ''
        if tag9F38:
            data = tools.assemble_dol(tag9F38)
        resp = super().gpo(data)
        if resp.sw == 0x9000:
            tools.output_apdu_info(resp)
            self.store_tag_group(PROCESS_STEP.GPO,utils.parse_tlv(resp.response))
            # self.run_case('case_gpo','run_visa',resp)
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

    def first_gac(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        data = tools.assemble_dol(tag8C)
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
        if not self.cvn:
            Log.error('can not get CVN, check tag9F10 wether existed.')
            return
        if self.cvn == '0A':    # CVN10处理流程
            arc = '3030'
            key = self.key_ac
            if self.key_flag == App_Master_Key.MDK:
                tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
                tag5F34 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F34')
                key = auth.gen_udk(key,tag5A,tag5F34)
            arpc = auth.gen_arpc_by_des3(key,tag9F26,arc)
            resp = apdu.external_auth(arpc,arc)
            if resp.sw == 0x9000:
                return True
        elif self.cvn == '12': # CVN18处理流程
            csu = '00820000' 
            self.divert_key() #需要使用AC session key
            arpc = auth.gen_arpc_by_mac(self.session_key_ac,tag9F26,csu)
            terminal.set_terminal('91',arpc + csu)
            return True
        return False


    def second_gac(self):
        tag8D = self.get_tag(PROCESS_STEP.READ_RECORD,'8D')
        data = tools.assemble_dol(tag8D)
        resp = super().gac(Crypto_Type.TC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        return resp

    def get_data(self):
        tags = ['9F75','9F72']
        super().get_data(tags)
        self.run_case('case_get_data','run_visa')

    def put_data(self,tag,value):
        tag9F36 = self.get_tag('9F36')
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        key_input = '000000000000' + tag9F36 + '000000000000' + algorithm.xor(tag9F36,'FFFF')
        if len(tag) == 2:
            tag = '00' + tag
        data_len = utils.int_to_hex_str(len(value) // 2 + 8)
        mac_input = '04DA' + tag + data_len + tag9F36 + tag9F26 + value
        key_mac = algorithm.xor(key_input,self.key_mac)
        mac = algorithm.des3_mac(key_mac,mac_input)
        apdu.put_data(tag,value,mac)

    def unlock_app(self):
        tag9F36 = self.get_tag('9F36')
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        key_input = '000000000000' + tag9F36 + '000000000000' + algorithm.xor(tag9F36,'FFFF')
        mac_input = '8418000008' + tag9F36 + tag9F26
        key_mac = algorithm.xor(key_input,self.key_mac)
        mac = algorithm.des3_mac(key_mac,mac_input)
        apdu.unlock_app(mac)

    def lock_app(self):
        tag9F36 = self.get_tag('9F36')
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        key_input = '000000000000' + tag9F36 + '000000000000' + algorithm.xor(tag9F36,'FFFF')
        mac_input = '841E000008' + tag9F36 + tag9F26
        key_mac = algorithm.xor(key_input,self.key_mac)
        mac = algorithm.des3_mac(key_mac,mac_input)
        apdu.lock_app(mac)


    def do_contact_trans(self,do_pse=True,aid="A0000000031010"):
        '''
        Visa借记/贷记接触交易主流程
        '''
        if do_pse:
            self.pse = PseTrans()
            self.pse.application_selection()
            aids = self.pse.read_record()
            for index,aid in enumerate(aids):
                print("{0}: {1}".format(index,aid))
            aid_index = input('select app to do transaction:')
            self.application_selection(aids[int(aid_index)])
        else:
            self.application_selection(aid)
        self.gpo_VSDC()
        self.read_record()
        self.get_data()
        self.do_dda()
        self.first_gac()
        self.issuer_auth()
        self.second_gac()

    def do_contactless_trans(self):
        self.ppse = PpseTrans()
        aids = self.ppse.application_selection()
        if aids:
            for index,aid in enumerate(aids):
                print("{0}: {1}".format(index,aid))
            aid_index = input('select app to do transaction:')
            self.application_selection(aids[int(aid_index)])
            self.gpo_qVSDC()
            self.read_record()
            self.get_data()
            self.do_dda(fDDA=True)


if __name__ == '__main__':
    from perso_lib.pcsc import get_readers,open_reader
    from perso_lib.transaction.utils import terminal
    from perso_lib.transaction.trans_pse import PseTrans,PpseTrans
    from perso_lib.transaction.utils.property import App_Master_Key
    from perso_lib.log import Log
    import time

    Log.init()
    terminal.set_terminal(App_Master_Key.UDK,'5856D35E3405B7C2D97B65809468C2D31C71E2AE1EED4377603877A357428DBAF6241FCA77459F62ACB2CA38CDFD7175')
    trans = VisaTrans()
    readers = get_readers()
    for index,reader in enumerate(readers):
        print("{0}: {1}".format(index,reader))
    index = input('select readers: ')
    if open_reader(readers[int(index)]):
        #================= contactless trans ==================
        # terminal.set_offline_only()
        # terminal.set_currency_code('0446')
        # trans.do_contactless_trans()
        #=================== contact trans ====================
        trans.do_contact_trans()
        trans.put_data('9F79','000000010000')
        resp = apdu.get_data('9F79')
        print(resp.response)
        trans.lock_app()
        trans.unlock_app()
