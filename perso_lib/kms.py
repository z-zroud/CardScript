from perso_lib import algorithm

# 此类用于自动生成个人化脱机数据认证相关的数据，每一次只生成一个发卡行
# 公钥证书，可以通过多次调用gen_new_icc_cert生成多个IC卡公钥证书
class Kms():
    is_init = False
    ca_d = '80CCA2CEDA5190CAC9B039840AC90B7F30470E93935C39F96EA2F72454E1651285D36E5C533829F64C072AAEE36697FFDF32C4A6509EA6A7B2F4894B83FE88452AE66D64B7F8B62DEA42FD126EA64D1A02616B8F089FB4B8B139D885D22E68F60928559893F9E16CA77683389F5CB44339B544090119A12B0BD7441CFD2F1EE3'
    ca_n = 'C132F436477A59302E885646102D913EC86A95DD5D0A56F625F472B67F52179BC8BD258A7CD43EF1720AC0065519E3FFCECC26F978EDF9FB8C6ECDF145FDCC697D6B72562FA2E0418B2B80A038D0DC3B769EB027484087CCE6652488D2B3816742AC9C2355B17411C47EACDD7467566B302F512806E331FAD964BF000169F641'
    mdk_ac = '5856D35E3405B7C2D97B65809468C2D3'
    mdk_mac = '1C71E2AE1EED4377603877A357428DBA'
    mdk_enc = 'F6241FCA77459F62ACB2CA38CDFD7175'
    def __init__(self):
        self.tags = dict()
        self.exp = '03'
        self.expiry_date = '1250'    #失效日期2050年12月

    def init(self,issuer_bin):
        if not self.is_init:
            self.issuer_bin = issuer_bin
            self.tags['9F32'] = self.exp
            self.tags['9F47'] = self.exp
            self.tags['8F'] = '50'  #默认索引为50
            self.issuer_d,self.issuer_n,*_ = algorithm.gen_rsa(1024,self.exp)
            _,self.icc_n,tag8205,tag8204,tag8203,tag8202,tag8201 = algorithm.gen_rsa(1024,self.exp)
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

    def close(self):
        self.tags.clear()
        self.is_init = False

    def gen_new_icc_cert(self,pan,sig_id,sig_data):
        tag9F46,tag9F48 = algorithm.gen_icc_cert(self.issuer_d,self.issuer_n,self.icc_n,self.exp,pan,sig_data,self.expiry_date)
        key9F46 = '9F46_' + sig_id
        key9F48 = '9F48_' + sig_id
        self.tags[key9F46] = tag9F46
        self.tags[key9F48] = tag9F48
        return tag9F46,tag9F48

    def gen_new_ssda(self,issuer_bin,sig_id,sig_data):
        aip = sig_data[-4:]
        sig_data = sig_data[0:-4]
        tag93 = algorithm.gen_tag93(self.issuer_d,self.issuer_n,sig_data,aip)
        key93 = '93_' + sig_id
        self.tags[key93] = tag93
        return tag93

    def get_value(self,tag):
        return self.tags.get(tag,'')