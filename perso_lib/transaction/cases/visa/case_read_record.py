from perso_lib.transaction.cases.base import case_read_record as cb

def run_visa(trans_obj,apdu_resps):
    cb.check_startswith_70(apdu_resps)
    cb.check_duplicate_tag(trans_obj)
    cb.check_empty_tag(trans_obj)