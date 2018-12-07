import sys

# 个人化时，不同的芯片需加密的DGI(国密)不一样
hd_encrypts = [
    ('8000',False),
    ('8020',False),
    ('8201',True),
    ('8202',True),
    ('8203',True),
    ('8204',True),
    ('8205',True),
    ('8100',True),
    ('8030',False),
]

tf_encrypts = [
    ('8000',False),
    ('8020',False),
    ('8201',True),
    ('8202',True),
    ('8203',True),
    ('8204',True),
    ('8205',True),
    ('8700',False),
    ('8401',False),
    ('8400',False),
    ('8001',False),
    ('A006',False),
    ('A016',False),
    ('8010',False),
]

ifx_encrypts = [
    ('8000',False),
    ('8020',False),
    ('8201',True),
    ('8202',True),
    ('8203',True),
    ('8204',True),
    ('8205',True),
]

fd_encrypts = [
    ('8000',False),
    ('8020',False),
    ('8201',True),
    ('8202',True),
    ('8203',True),
    ('8204',True),
    ('8205',True),
]

dt_encrypts = [
    ('8000',False),
    ('8020',False),
    ('8201',True),
    ('8202',True),
    ('8203',True),
    ('8204',True),
    ('8205',True),
]
kmc = '404142434445464748494A4B4C4D4E4F'

#华大芯片安装参数集合
hd_G81140042_pse = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
hd_G81140042_ppse = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='325041592E5359532E4444463031',priviliage='00',param='C900') 
hd_G81140042_uics_debit = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010101',priviliage='10',param='C902F30B')
hd_G81140042_uics_credit = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010102',priviliage='10',param='C902F30B')
hd_G81140042_pboc_debit = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010101',priviliage='10',param='C90100')
hd_G81140042_pboc_credit = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010102',priviliage='10',param='C90100')

#英飞凌芯片安装参数集合
ifx_05059081_pse = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
ifx_05059081_ppse = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
ifx_05059081_uics_debit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010101',priviliage='10',param='C9022A03')
ifx_05059081_uics_credit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010102',priviliage='10',param='C9022A03')
ifx_05059081_pboc_debit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010101',priviliage='10',param='C9022803')
ifx_05059081_pboc_credit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010102',priviliage='10',param='C9022803')

#同方芯片安装参数集合
tf_G8C140026_pse = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140026_ppse = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140026_pse_visa = dict(packet='A00000000316',applet='A0000000031650',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140026_ppse_visa = dict(packet='A00000000316',applet='A0000000031650',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140026_uics_debit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010101',priviliage='10',param='C90102')
tf_G8C140026_uics_credit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010102',priviliage='10',param='C90102')
tf_G8C140026_pboc_debit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010101',priviliage='10',param='C9018A')
tf_G8C140026_pboc_credit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010102',priviliage='10',param='C9018A')
tf_G8C140026_mc = dict(packet='A0000000180F000001833032',applet='A0000000180F0000018303',inst='A0000000041010',priviliage='10',param='C90100')
tf_G8C140026_visa = dict(packet='A00000000310',applet='A0000000031056',inst='A0000000031010',priviliage='10',param='C900')
tf_G8C140026_jetco = dict(packet='A00000033301',applet='A0000003330103',inst='A00000047400000001',priviliage='10',param='C906200400000001')


tf_G8C140031_pse = dict(packet='F062732E50424F432E505345',applet='F062732E50424F432E50534501',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140031_ppse = dict(packet='F062732E50424F432E505345',applet='F062732E50424F432E50534501',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140031_uics_debit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010101',priviliage='10',param='C90102')
tf_G8C140031_uics_credit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010102',priviliage='10',param='C90102')
tf_G8C140031_pboc_debit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010101',priviliage='10',param='C9018A')
tf_G8C140031_pboc_credit = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010102',priviliage='10',param='C9018A')

tf_G8C140046_pse = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140046_ppse = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
tf_G8C140046_uics_debit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010101',priviliage='10',param='C9022A03')
tf_G8C140046_uics_credit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010102',priviliage='10',param='C9022A03')
tf_G8C140046_pboc_debit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010101',priviliage='10',param='C9022803')
tf_G8C140046_pboc_credit = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010102',priviliage='10',param='C9022803')
tf_G8C140046_jetco = dict(packet='A000000333010130',applet='A0000003330101',inst='A00000047400000001',priviliage='10',param='C906380300000001')

class Chip:
    tf_G8C140026 = 'tf_G8C140026'
    tf_G8C140031 = 'tf_G8C140031'
    tf_G8C140046 = 'tf_G8C140046'
    ifx_05059081 = 'ifx_05059081'
    hd_G81140042 = 'hd_G81140042'

class App:
    pse = 'pse'
    ppse = 'ppse'
    pboc_credit = 'pboc_credit'
    pboc_debit = 'pboc_debit'
    uics_credit = 'uics_credit'
    uics_debit = 'uics_debit'
    visa = 'visa'
    mc = 'mc'
    jetco = 'jetco'

def get_encrypts(chip):
    index = str(chip).find('_')
    if chip[0:index] == 'hd':
        return hd_encrypts
    elif chip[0:index] == 'dt':
        return dt_encrypts
    elif chip[0:index] == 'ifx':
        return ifx_encrypts
    elif chip[0:index] == 'fd':
        return fd_encrypts
    elif chip[0:index] == 'tf':
        return tf_encrypts


def get_tf_G8C140026_param(app):
    pse_param = tf_G8C140026_pse
    ppse_param = tf_G8C140026_ppse
    if app == App.mc:
        pse_param = tf_G8C140026_pse
        ppse_param = tf_G8C140026_ppse
    elif app == App.visa:
            pse_param = tf_G8C140026_pse_visa
            ppse_param = tf_G8C140026_ppse_visa
    return dict(pse=pse_param,ppse=ppse_param,pboc_credit=tf_G8C140026_pboc_credit,pboc_debit=tf_G8C140026_pboc_debit,
    uics_credit=tf_G8C140026_uics_credit,uics_debit=tf_G8C140026_uics_debit,visa=tf_G8C140026_visa,mc=tf_G8C140026_mc,jetco=tf_G8C140026_jetco)

# 返回所有chip应用的字典集合
def get_param(chip,module_code=None):
    pse = chip + '_pse'
    ppse = chip + '_ppse'
    pboc_credit = chip + '_pboc_credit'
    pboc_debit = chip + '_pboc_debit'
    uics_credit = chip + '_uics_credit'
    uics_debit = chip + '_uics_debit'
    visa = chip + '_visa'
    mc = chip + '_mc'
    jetco = chip + '_jetco'
    mod = sys.modules[__name__]
    pse_param = getattr(mod,pse,None)
    ppse_param = getattr(mod,ppse,None)
    pboc_credit_param = getattr(mod,pboc_credit,None)
    pboc_debit_param = getattr(mod,pboc_debit,None)
    uics_credit_param = getattr(mod,uics_credit,None)
    uics_debit_param = getattr(mod,uics_debit,None)
    visa_param = getattr(mod,visa,None)
    mc_param = getattr(mod,mc,None)
    jetco_param = getattr(mod,jetco,None)
    return dict(pse=pse_param,ppse=ppse_param,pboc_credit=pboc_credit_param,pboc_debit=pboc_debit_param,
    uics_credit=uics_credit_param,uics_debit=uics_debit_param,visa=visa_param,mc=mc_param,jetco=jetco_param)

    