from perso_lib import utils
from perso_lib.transaction.utils import terminal
from perso_lib.log import Log


def assemble_dol(dol):
    '''
    根据DOL标签列表，组装终端数据
    '''
    data = ''
    tls = utils.parse_tl(dol)
    for tl in tls:
        data += terminal.get_terminal(tl.tag,tl.len)
    return data

def output_not_tlv_gpo_info(apdu_response):
    '''
    输出不是TLV结构的GPO响应
    '''
    tab = '    ' #设置缩进为4个空格
    start_tab = '      ' #设置起始输出保留6个空格
    Log.info('send: %s %s %s',apdu_response.request[0:8],apdu_response.request[8:10],apdu_response.request[10:])
    Log.info('recv: %s',apdu_response.response)
    Log.info('sw  : %4X',apdu_response.sw)
    Log.info('tlv :')      
    Log.info("%s<%s>",start_tab,apdu_response.response[0:2])
    Log.info("%s[82]=%s",start_tab + tab,apdu_response.response[4:8])
    Log.info("%s[94]=%s",start_tab + tab,apdu_response.response[8:])
    Log.info('\n')

def output_apdu_info(apdu_response):
    '''
    输出APDU响应数据
    '''
    tab = '    ' #设置缩进为4个空格
    start_tab = '      ' #设置起始输出保留6个空格
    Log.info('send: %s %s %s',apdu_response.request[0:8],apdu_response.request[8:10],apdu_response.request[10:])
    Log.info('recv: %s',apdu_response.response)
    Log.info('sw  : %4X',apdu_response.sw)
    if apdu_response.response and utils.is_tlv(apdu_response.response):
        Log.info('tlv :')
        tlvs = utils.parse_tlv(apdu_response.response)
        for tlv in tlvs:
            prefix_padding = tab * tlv.level + start_tab
            if tlv.is_template:
                info = prefix_padding + '<' + tlv.tag + '>'
            else:
                info = prefix_padding + '[' + tlv.tag + ']=' + tlv.value
            Log.info(info)
    Log.info('\n')