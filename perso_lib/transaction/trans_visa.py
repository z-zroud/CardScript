
from perso_lib.transaction.trans_base import TransBase,TransTag,PROCESS_STEP
from perso_lib import utils



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
            data = self.assemble_cdol(tag9F38)
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
            self.run_case('case_read_record','run_visa',resps)
        return resps






if __name__ == '__main__':
    from perso_lib.pcsc import get_readers,open_reader
    from perso_lib import log
    log.init()
    trans = VisaTrans()
    readers = get_readers()
    for index,reader in enumerate(readers):
        print("{0}: {1}".format(index,reader))
    index = input('select readers: ')
    if open_reader(readers[int(index)]):
        trans.application_selection('A0000000031010')
        trans.gpo()
        trans.read_record()
