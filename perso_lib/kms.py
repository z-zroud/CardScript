from perso_lib import algorithm

# 此类用于自动生成个人化脱机数据认证相关的数据，每一次只生成一个发卡行
# 公钥证书，可以通过多次调用gen_new_icc_cert生成多个IC卡公钥证书
class Kms():
    is_init = False
    ca_d = '7196A0BE381BEEB6CBFC78B8E79A3D87F6B20364729352F5694B52DB7651EC1A87B5D5BEA94E5770AF6C7390A50DE48BDEF989D2DC23651C99E1F30FD666C0177E47BDD93DF04C3DA55B11A7C6CD9941B0E36CC865384E1C63D23A36AB742E5B95F991FF742B1673EBAC34DC9FD5D36F3A1FAB88ED79F2A46A83AEB35E07129B1540E1D8512387F4BBAABA210A28DF6B'
    ca_n = 'AA61F11D5429E61231FAB5155B675C4BF20B0516ABDCFC701DF0FC49317AE227CB90C09DFDF583290722AD58F794D6D1CE764EBC4A3517AAE6D2EC97C19A20233D6B9CC5DCE8725E19BBB9A04248A23000313C32B25A6E936C500F6568F75EB5EAEBEDAA4A8B437AC8D02949136D24A40D9B511EFAD90CCCCEF60FC91C732C4CA97CE54798DD82421EC84B041D91852B'
    mdk_ac = '5856D35E3405B7C2D97B65809468C2D3'
    mdk_mac = '1C71E2AE1EED4377603877A357428DBA'
    mdk_enc = 'F6241FCA77459F62ACB2CA38CDFD7175'
    idn_key = 'F6241FCA77459F62ACB2CA38CDFD7175'
    kdcvc3 = 'F6241FCA77459F62ACB2CA38CDFD7175'
    def __init__(self):
        self.tags = dict()
        self.exp = '03'
        self.expiry_date = '1249'    #失效日期2049年12月

    def init(self,issuer_bin,rsa_len=1152):
        if not self.is_init:
            self.issuer_bin = issuer_bin
            self.tags['9F32'] = self.exp
            self.tags['9F47'] = self.exp
            self.tags['8F'] = 'AA'  #默认索引为AA
            self.issuer_d,self.issuer_n,*_ = algorithm.gen_rsa(rsa_len,self.exp)
            _,self.icc_n,tag8205,tag8204,tag8203,tag8202,tag8201 = algorithm.gen_rsa(rsa_len,self.exp)
            self.tags['8201'] = tag8201
            self.tags['8202'] = tag8202
            self.tags['8203'] = tag8203
            self.tags['8204'] = tag8204
            self.tags['8205'] = tag8205
            tag90,tag92 = algorithm.gen_issuer_cert(self.ca_d,self.ca_n,self.issuer_n,self.exp,issuer_bin,self.expiry_date)
            self.tags['90'] = tag90
            self.tags['92'] = tag92
            self.tags['8000'] = self.mdk_ac + self.mdk_mac + self.mdk_enc
            self.tags['9000'] = algorithm.gen_app_key_kcv(self.tags['8000'])
            self.tags['8001'] = self.tags['8000']
            self.tags['9001'] = self.tags['9000']
            self.tags['A006'] = self.idn_key
            self.tags['A016'] = self.tags['A006']
            self.tags['8400'] = self.kdcvc3
            self.tags['8401'] = self.tags['8400']

    def close(self):
        self.tags.clear()
        self.is_init = False

    def gen_new_icc_cert(self,pan,sig_data,sig_id=None):
        tag9F46,tag9F48 = algorithm.gen_icc_cert(self.issuer_d,self.issuer_n,self.icc_n,self.exp,pan,sig_data,self.expiry_date)
        key9F46 = '9F46'
        key9F48 = '9F48'
        if sig_id:
            key9F46 += '_' + sig_id
            key9F48 += '_' + sig_id
        self.tags[key9F46] = tag9F46
        self.tags[key9F48] = tag9F48
        return tag9F46,tag9F48

    def gen_new_ssda(self,issuer_bin,sig_data,sig_id=None):
        aip = sig_data[-4:]
        sig_data = sig_data[0:-4]
        tag93 = algorithm.gen_tag93(self.issuer_d,self.issuer_n,sig_data,aip)
        key93 = '93'
        if sig_id:
            key93 += '_' + sig_id
        self.tags[key93] = tag93
        return tag93

    def gen_mc_cvc3(self,tag56,tag9F6B):
        self.tags['DC'] = algorithm.des3_mac(self.kdcvc3,tag56)[-4:]
        self.tags['DD'] = algorithm.des3_mac(self.kdcvc3,tag9F6B)[-4:]
        return self.tags['DC'] + self.tags['DD']
        
    def get_value(self,tag):
        return self.tags.get(tag,'')