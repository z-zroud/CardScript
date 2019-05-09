from perso_lib.transaction.cases import helper
from perso_lib.transaction.cases.helper import CR
from perso_lib.transaction.utils.property import PROCESS_STEP
from perso_lib.log import Log
from perso_lib.settings import LenType,get_tag_len

Log.init()

def check_tag_len(trans_obj):
    has_error = False
    for tag_info in trans_obj.tags_info:
        tag_len = len(tag_info.value) // 2
        len_type,lens = get_tag_len(tag_info.tag,trans_obj.aid)
        if len_type == LenType.Range:
            if tag_len < lens[0] or tag_len > lens[1]:
                Log.error('tag%s length is not correct, should be in range%d-%d. current len: %d',tag_info.tag,lens[0],lens[1],tag_len)
                has_error = True
        elif len_type == LenType.Fixed:
            if tag_len not in lens:
                Log.error('tag%s length is not correct, should be any of %s. current len: %d',tag_info.tag,str(lens),tag_len)
                has_error = True
    if has_error:
        return CR.ERROR
    return CR.OK
