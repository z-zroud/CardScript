
from perso_lib.transaction.trans_base import *
from perso_lib.transaction.trans_pse import PseTrans,PpseTrans
from perso_lib import utils
from perso_lib import algorithm
from perso_lib.apdu import Crypto_Type
from perso_lib.log import Log
from perso_lib.transaction.utils import terminal,auth,tools
from perso_lib.transaction.utils.property import App_Master_Key,PROCESS_STEP,TransTag

class McTrans(TransBase):
    def __init__(self):
        super().__init__()
        self.idn_key = terminal.get_terminal(App_Master_Key.IDN_KEY)
        self.cvc3_key = terminal.get_terminal(App_Master_Key.CVC3_KEY)

    def application_selection(self,aid):
        resp = super().application_selection(aid)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.SELECT,utils.parse_tlv(resp.response))
        # self.run_case('case_application_selection','run_visa',resp)
        return resp

    def gpo(self):
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
            # self.run_case('case_read_record','run_visa',resps)
        return resps

    def read_log(self):
        Log.info('get trans log')
        tag9F4D = self.get_tag(PROCESS_STEP.SELECT,'9F4D')
        if not tag9F4D:
            Log.info('no tag9F4D,do not support record log')
        else:
            record_count = int(tag9F4D[2:4],16)
            log_sfi = int(tag9F4D[0:2],16)
            buffer = []
            for i in range(record_count + 1):
                resp = apdu.read_record(log_sfi,i + 1,(0x9000,0x6A83))
                if resp.sw == 0x9000:
                    Log.info(resp.response)
                    buffer.append(resp.response)
                else:
                    break
            Log.info('%-10s%-15s%-10s%-10s%-8s%-15s%-10s%-10s%-10s','result','money','currency','date','atc','cvr','interface','time','merchant')           
            for resp in buffer:
                result = resp[0:2]
                money = resp[2:14]
                currency = resp[14:18]
                date = resp[18:24]
                atc = resp[24:28]
                cvr = resp[28:40]
                interface = resp[40:42]
                trans_time = resp[42:48]
                merchant = utils.bcd_to_str(resp[48:])
                Log.info('%-10s%-15s%-10s%-10s%-8s%-15s%-10s%-10s%-10s',result,money,currency,date,atc,cvr,interface,trans_time,merchant)           
                

    def first_gac(self):
        tag8C = self.get_tag(PROCESS_STEP.READ_RECORD,'8C')
        data = tools.assemble_dol(tag8C)
        resp = super().gac(Crypto_Type.ARQC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        tlvs = utils.parse_tlv(resp.response)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.FIRST_GAC,utils.parse_tlv(resp.response))
        self.run_case('case_first_gac','run_mc',resp)
        return resp

    def divert_key(self):
        if self.key_flag == App_Master_Key.MDK:
            tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
            tag5F34 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F34')
            self.key_ac = auth.gen_udk(self.key_ac,tag5A,tag5F34)
            self.key_mac = auth.gen_udk(self.key_mac,tag5A,tag5F34)
            self.key_enc = auth.gen_udk(self.key_enc,tag5A,tag5F34)
        tag9F36 = self.get_tag('9F36')
        tagD5 = self.get_tag('D5')
        left_input = ''
        right_input = ''
        if int(tagD5[1]) & 0x02 == 0x02:
            #SKD
            tag9F37 = terminal.get_terminal('9F37')
            left_input = tag9F36 + 'F000' + tag9F37
            right_input = tag9F36 + '0F00' + tag9F37
        else:
            #CSK
            left_input = tag9F36 + 'F00000000000'
            right_input = tag9F36 + '0F0000000000'
        self.session_key_ac = self.key_ac
        self.session_key_enc = algorithm.des3_encrypt(self.key_enc,left_input) + algorithm.des3_encrypt(self.key_enc,right_input)
        self.session_key_mac = algorithm.des3_encrypt(self.key_mac,left_input) + algorithm.des3_encrypt(self.key_mac,right_input)
        
        
    def issuer_auth(self):
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        arc = '0012'
        if self.key_flag == App_Master_Key.MDK:
            tag5A = self.get_tag(PROCESS_STEP.READ_RECORD,'5A')
            tag5F34 = self.get_tag(PROCESS_STEP.READ_RECORD,'5F34')
            self.key_ac = auth.gen_udk(self.key_ac,tag5A,tag5F34)
            self.key_enc = auth.gen_udk(self.key_enc,tag5A,tag5F34)
            self.key_mac = auth.gen_udk(self.key_mac,tag5A,tag5F34)
        self.divert_key() #需要使用AC session key
        arpc = auth.gen_arpc_by_des3(self.session_key_ac,tag9F26,arc)
        terminal.set_terminal('91',arpc + arc)



    def second_gac(self):
        tag8D = self.get_tag(PROCESS_STEP.READ_RECORD,'8D')
        data = tools.assemble_dol(tag8D)
        resp = super().gac(Crypto_Type.TC,data)
        if resp.sw != 0x9000:
            Log.info('send gac1 failed.')
            return
        tlvs = utils.parse_tlv(resp.response)
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.SECOND_GAC,utils.parse_tlv(resp.response))
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

    def get_data(self):
        tags = ['D5','9F72']
        super().get_data(tags)
        # self.run_case('case_get_data','run_visa')


    def unlock_app(self):
        tag9F36 = self.get_tag('9F36')
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        key_input = '000000000000' + tag9F36 + '000000000000' + algorithm.xor(tag9F36,'FFFF')
        mac_input = '8418000008' + tag9F36 + tag9F26
        key_mac = algorithm.xor(key_input,self.session_key_mac)
        mac = algorithm.des3_mac(key_mac,mac_input)
        apdu.unlock_app(mac)

    def lock_app(self):
        tag9F36 = self.get_tag('9F36')
        tag9F26 = self.get_tag(PROCESS_STEP.FIRST_GAC,'9F26')
        key_input = '000000000000' + tag9F36 + '000000000000' + algorithm.xor(tag9F36,'FFFF')
        mac_input = '841E000008' + tag9F36 + tag9F26
        key_mac = algorithm.xor(key_input,self.session_key_mac)
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
        self.gpo()
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
            self.gpo()
            self.read_record()
            self.get_data()
            self.first_gac_cda()
            self.do_cda()


if __name__ == '__main__':

    from perso_lib.pcsc import get_readers,open_reader
    from perso_lib.transaction.utils import terminal
    from perso_lib.transaction.trans_pse import PseTrans,PpseTrans
    from perso_lib.transaction.utils.property import App_Master_Key
    from perso_lib.log import Log
    import time

    Log.init()
    terminal.set_terminal(App_Master_Key.UDK,'D616705D0D7C9D4394130476E3C4EA862C020DF42980D6C47943DC1C52F7F780C4076E2FBC49B3B5498C07ECBF23F23E')
    terminal.set_terminal(App_Master_Key.IDN_KEY,'C4076E2FBC49B3B5498C07ECBF23F23E')
    terminal.set_terminal(App_Master_Key.CVC3_KEY,'C4076E2FBC49B3B5498C07ECBF23F23E')
    trans = McTrans()
    readers = get_readers()
    for index,reader in enumerate(readers):
        print("{0}: {1}".format(index,reader))
    index = input('select readers: ')
    if open_reader(readers[int(index)]):
        #================= contactless trans ==================
        trans.do_contactless_trans()
        #=================== contact trans ====================
        # trans.do_contact_trans()
        # trans.read_log()
