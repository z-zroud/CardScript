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
    ('8700',True),
    ('8401',True),
    ('8001',True),
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

goldpac_encryptes = [
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

#个人化时，不同芯片安装参数不一样
hd_pse_install_param = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
hd_ppse_install_param = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='325041592E5359532E4444463031',priviliage='00',param='C900') 
hd_uics_debit_install_param = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010101',priviliage='10',param='C902F30B')
hd_uics_credit_install_param = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010102',priviliage='10',param='C902F30B')
hd_pboc_debit_install_param = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010101',priviliage='10',param='C90100')
hd_pboc_credit_install_param = dict(packet='F16865640065636170706C6574',applet='F16865640065636170706C657401',inst='A000000333010102',priviliage='10',param='C90100')

ifx_pse_install_param = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
ifx_ppse_install_param = dict(packet='315041592E',applet='315041592E5359532E4444463031',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
ifx_uics_debit_install_param = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010101',priviliage='10',param='C9022A03')
ifx_uics_credit_install_param = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010102',priviliage='10',param='C9022A03')
ifx_pboc_debit_install_param = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010101',priviliage='10',param='C9022803')
ifx_pboc_credit_install_param = dict(packet='A000000333010130',applet='A0000003330101',inst='A000000333010102',priviliage='10',param='C9022803')
ifx_mc_install_param = dict(packet='A0000000180F000001833032',applet='A0000000180F0000018303',inst='A0000000041010',priviliage='10',param='C90100')

goldpac_pse_install_param = dict(packet='A00000000316',applet='A0000000031650',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
goldpac_ppse_install_param = dict(packet='A00000000316',applet='A0000000031650',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
goldpac_visa_install_param = dict(packet='A00000000310',applet='A0000000031056',inst='A0000000031010',priviliage='10',param='C90101')
goldpac_jetco_install_param = dict(packet='A000000333010130',applet='A0000003330101',inst='A00000047400000001',priviliage='10',param='C906200000000001')


tf_pse_install_param = dict(packet='F062732E50424F432E505345',applet='F062732E50424F432E50534501',inst='315041592E5359532E4444463031',priviliage='00',param='C900')
tf_ppse_install_param = dict(packet='F062732E50424F432E505345',applet='F062732E50424F432E50534501',inst='325041592E5359532E4444463031',priviliage='00',param='C900')
tf_uics_debit_install_param = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010101',priviliage='10',param='C90102')
tf_uics_credit_install_param = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010102',priviliage='10',param='C90102')
tf_pboc_debit_install_param = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010101',priviliage='10',param='C9018A')
tf_pboc_credit_install_param = dict(packet='F062732E50424F432E415050',applet='F062732E50424F432E41505001',inst='A000000333010102',priviliage='10',param='C9018A')

kmc = '404142434445464748494A4B4C4D4E4F'

class Chip:
    hd = 0     #华大
    ifx = 1    #英飞凌
    fd = 2     #复旦
    dt = 3     #大唐
    tf = 4      #同方
    goldpac = 5     #自主产品

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
    if chip == Chip.hd:
        return hd_encrypts
    elif chip == Chip.dt:
        return dt_encrypts
    elif chip == Chip.ifx:
        return ifx_encrypts
    elif chip == Chip.fd:
        return fd_encrypts
    elif chip == Chip.tf:
        return tf_encrypts
    elif chip == Chip.goldpac:
        return goldpac_encryptes

# 返回所有chip应用的字典集合
def get_param(chip,module_code=None):
    if chip == Chip.hd:
        return dict(pse=hd_pse_install_param,
        ppse=hd_ppse_install_param,
        uics_credit=hd_uics_credit_install_param,
        uics_debit=hd_uics_debit_install_param,
        pboc_credit=hd_pboc_credit_install_param,
        pboc_debit=hd_pboc_debit_install_param)
    elif chip == Chip.dt:
        return dict()
    elif chip == Chip.ifx:
        return dict(pse=ifx_pse_install_param,
        ppse=ifx_ppse_install_param,
        uics_credit=ifx_uics_credit_install_param,
        uics_debit=ifx_uics_debit_install_param,
        pboc_credit=ifx_pboc_credit_install_param,
        pboc_debit=ifx_pboc_debit_install_param,
        mc=ifx_mc_install_param)
    elif chip == Chip.fd:
        return dict()
    elif chip == Chip.tf:
        return dict(pse=tf_pse_install_param,
        ppse=tf_ppse_install_param,
        uics_credit=tf_uics_credit_install_param,
        uics_debit=tf_uics_debit_install_param,
        pboc_credit=tf_pboc_credit_install_param,
        pboc_debit=tf_pboc_debit_install_param)
    elif chip == Chip.goldpac:
        return dict(pse=goldpac_pse_install_param,
        ppse=goldpac_ppse_install_param,
        visa=goldpac_visa_install_param,
        jetco=goldpac_jetco_install_param)