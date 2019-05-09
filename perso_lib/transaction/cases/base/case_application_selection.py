from enum import Enum
from perso_lib.transaction.cases import helper
from perso_lib import utils
from perso_lib.log import Log

Log.init()

def check_startswith_6F(buffer):
    return helper.case_startswith('6F',buffer)

class TagCondition(Enum):
    M = 0
    C = 1
    O = 2

fci_9102 = [
    ('6F',0,TagCondition.M),
    ('84',1,TagCondition.M),
    ('A5',1,TagCondition.M),
    ('50',2,TagCondition.M),
    ('87',2,TagCondition.C),
    ('9F38',2,TagCondition.C),
    ('5F2D',2,TagCondition.O),
    ('9F11',2,TagCondition.C),
    ('9F12',2,TagCondition.O),
    ('BF0C',2,TagCondition.O),
    ('9F4D',3,TagCondition.O),
    ('DF4D',3,TagCondition.O)
]

def check_fci_9102(buffer):
    tlvs = utils.parse_tlv(buffer)
    sub_tlvs = []
    sub_fci_9102 = []
    for tlv in tlvs:
        for fci_item in fci_9102:
            if tlv.tag == fci_item[0]:
                sub_fci_9102.append(fci_item)
                sub_tlvs.append(tlv)
    # 判断集合中的顺序是否一致
    has_ordered = True
    for index in range(len(sub_fci_9102)):
        if sub_fci_9102[index][0] != sub_tlvs[index].tag or sub_fci_9102[index][1] != sub_tlvs[index].level:
            Log.warn('tag%s is not ordered.',sub_tlvs[index].tag)
            has_ordered = False
    if not has_ordered:
        order_tags = [item[0] for item in sub_fci_9102]
        Log.warn('the minium order list should be %s',str(order_tags))
    # 判断是否缺少必须的tag
    for item in fci_9102:
        if item not in sub_fci_9102:
            if item[2] == TagCondition.M:
                Log.error('FCI 9102 should contains tag%s',item[0])
            elif item[2] == TagCondition.C:
                Log.warn('FCI 9102 recommand that tag%s should be existed.',item[0])
    # 判断是否包含多余的tag
    for item in tlvs:
        if item not in sub_tlvs:
            Log.warn('FCI 9102 should not contains tag%s',item.tag)
            
