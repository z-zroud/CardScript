from perso_lib.transaction.cases import helper
from perso_lib.transaction.cases.helper import CR
from perso_lib.transaction.utils.property import PROCESS_STEP
from perso_lib.log import Log

Log.init()

def check_startswith_70(apdu_resps):
    '''
    检测读记录响应数据是否以70模板开头
    '''
    for resp in apdu_resps:
        if helper.case_startswith('70',resp.response) != CR.OK:
            Log.error('read record response not start with template 70')
            return CR.ERROR
    return CR.OK

def check_duplicate_tag(trans_obj):
    '''
    检测GPO和读记录数据中是否有重复tag出现
    '''
    tags = []
    has_duplicate = False
    for tag_info in trans_obj.tags_info:
        if tag_info.step in (PROCESS_STEP.GPO,PROCESS_STEP.READ_RECORD):
            tags.append(tag_info.tag)
    tag_counts = len(tags)
    for current in range(tag_counts):
        for index in range(current + 1,tag_counts):
            if tags[current] == tags[index]:
                Log.error('tag%s has duplicated',tags[current])
                has_duplicate = True
    if has_duplicate:
        return CR.ERROR
    return CR.OK

def check_empty_tag(trans_obj):
    '''
    检测读记录之前的数据是否有空值的现象
    '''
    has_empty_tag = False
    for tag_info in trans_obj.tags_info:
        if not tag_info.value:
            Log.error('tag%s is empty',tag_info.tag)
            has_empty_tag = True
    if has_empty_tag:
        return CR.ERROR
    return CR.OK



