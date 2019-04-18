from perso_lib.transaction.cases.base import case_read_record as cb

def run_pure(trans_obj,apdu_resps):
    cb.check_startswith_70(apdu_resps)
    print('ok')