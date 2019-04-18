from perso_lib.transaction.cases.base import case_application_selection as cb

def run_visa(trans_obj,apdu_resp):
    cb.check_startswith_6F(apdu_resp.response)