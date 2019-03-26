from perso_lib.transaction.cases import case_base as cb
from perso_lib.transaction.cases.case_base import CR


def check_startswith_70(apdu_resps):
    for resp in apdu_resps:
        if cb.case_startswith('70',resp.response) != CR.OK:
            return CR.ERROR
    return CR.OK


def run_visa(trans_obj,apdu_resps):
    check_startswith_70(apdu_resps)
    print('ok')