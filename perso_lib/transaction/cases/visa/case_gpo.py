from perso_lib.transaction.cases.base import case_gpo as cb


def run_visa(trans_obj,apdu_resp):
    cb.check_startswith_80(apdu_resp.response)