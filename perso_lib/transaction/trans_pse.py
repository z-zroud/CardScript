
from perso_lib.transaction.trans_base import *
from perso_lib import utils

class PseTrans(TransBase):
    def __init__(self):
        super().__init__()

    def run_case(self,module_name,apdu_resp=None):
        super().run_case(module_name,'run_pse',apdu_resp)

    def application_selection(self):
        resp = super().application_selection('315041592E5359532E4444463031')
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.SELECT,utils.parse_tlv(resp.response))
        # self.run_case('case_application_selection',resp)
        return resp

    def read_record(self):
        aids = []
        sfi = 1
        for record_no in range(1,5):
            resp = apdu.read_record(sfi,record_no,(0x9000,0x6A83))
            tools.output_apdu_info(resp)
            if resp.sw == 0x6A83:
                break
            tlvs = utils.parse_tlv(resp.response)
            for tlv in tlvs:
                if tlv.tag == '4F':
                    aids.append(tlv.value)
        return aids

class PpseTrans(TransBase):
    def __init__(self):
        super().__init__()

    def run_case(self,module_name,apdu_resp=None):
        super().run_case(module_name,'run_ppse',apdu_resp)

    def application_selection(self,aid):
        resp = super().application_selection('325041592E5359532E4444463031')
        tools.output_apdu_info(resp)
        self.store_tag_group(PROCESS_STEP.SELECT,utils.parse_tlv(resp.response))
        # self.run_case('case_application_selection',resp)
        return resp


if __name__ == "__main__":
    pass