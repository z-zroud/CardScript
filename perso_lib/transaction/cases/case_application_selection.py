from perso_lib.transaction.cases import case_base as cb


def check_startswith_6F(buffer):
    return cb.case_startswith('6F',buffer)


def run_visa(trans_obj,apdu_resp):
    check_startswith_6F(apdu_resp.response)