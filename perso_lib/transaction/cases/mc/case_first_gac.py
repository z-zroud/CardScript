from perso_lib.transaction.cases.base import case_application_selection as cb
from perso_lib.transaction.utils.property import PROCESS_STEP
from perso_lib.transaction.utils import terminal
from perso_lib import algorithm
from perso_lib.transaction.cases.helper import CR


def check_idn(trans_obj):
    tag9F36 = trans_obj.get_tag(PROCESS_STEP.FIRST_GAC,'9F36')
    tag9F4C = terminal.get_terminal('9F4C')
    idn_input = tag9F36 + '000000000000'
    idn = algorithm.des3_encrypt(trans_obj.idn_key,idn_input)
    if idn == tag9F4C:
        return CR.OK
    return CR.ERROR

def run_mc(trans_obj,apdu_resp):
    check_idn(trans_obj)