from perso_lib.transaction.cases import case_base as cb


def check_startswith_80(buffer):
    return cb.case_startswith('80',buffer)


def run_visa(trans_obj,apdu_resp):
    check_startswith_80(apdu_resp.response)