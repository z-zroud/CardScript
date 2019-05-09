from perso_lib.transaction.cases.base import case_get_data as cb

def run_visa(trans_obj):
    cb.check_tag_len(trans_obj)