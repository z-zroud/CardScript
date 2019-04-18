from perso_lib.transaction.cases import helper
from perso_lib.transaction.cases.helper import CR


def check_startswith_70(apdu_resps):
    for resp in apdu_resps:
        if helper.case_startswith('70',resp.response) != CR.OK:
            return CR.ERROR
    return CR.OK


