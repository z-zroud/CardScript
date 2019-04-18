from perso_lib.transaction import utils
from perso_lib.transaction.cases.helper import CR
from perso_lib.transaction.utils.property import PROCESS_STEP

def check_ac(trans_obj,apdu_resp):
    tag9F02 = utils.terminal.get_terminal('9F02')   # transaction amount
    tag9F03 = utils.terminal.get_terminal('9F03')   # cashback amount
    tag9F1A = utils.terminal.get_terminal('9F1A')   # terminal country code
    tag95 = utils.terminal.get_terminal('95') # terminal verification result TVR
    tag5F2A = utils.terminal.get_terminal('5F2A') # transaction currency code
    tag9A = utils.terminal.get_terminal('9A') # transaction date
    tag9C = utils.terminal.get_terminal('9C') # transaction type
    tag9F37 = utils.terminal.get_terminal('9F37') # unpredicatable number
    tag82 = trans_obj.get_tag(PROCESS_STEP.GPO,'82')
    tag9F36 = trans_obj.get_tag("9F36")
    tag9F10 = trans_obj.get_tag("9F10")
    data = tag9F02 + tag9F03 + tag9F1A + tag95 + tag5F2A + tag9A + tag9C + tag9F37 + tag82 + tag9F36 + tag9F10
    ac = utils.auth.gen_ac(trans_obj.session_key_ac,data)
    tag9F26 = trans_obj.get_tag('9F26')
    if ac != tag9F26:
        return CR.ERROR
    return CR.OK


def run_pure(trans_obj,apdu_resp):
    check_ac(trans_obj,apdu_resp)
