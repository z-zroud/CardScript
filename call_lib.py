from perso_lib.pcsc import send,get_readers,open_reader
from perso_lib import des
from perso_lib import gen_kmc_session
from perso_lib import auth
from perso_lib import cps_perso
from perso_lib import goldpac_dp

#goldpac_dp.process_goldpac_dp('goldpac.dp','金邦达测试.xml')

readers = get_readers()
if open_reader(readers[0]):
    send('00A40400 0E 325041592E5359532E4444463031')
    send('00A40400 07 A0000000031010')
    sw = send('80 CA DF 61',(0x6A81,0x9000,0x1111))
    print(sw.response)
    sw = send('80 CA BF 55')
    print(sw.response)
    #delete old instance
    send("00A4040008A000000003000000")
    auth.open_secure_channel("404142434445464748494A4B4C4D4E4F")
    send("80E40000 09 4F07A0000000031010")
    send("80E40000 10 4F0E325041592E5359532E4444463031")
    send("80E40000 10 4F0E315041592E5359532E4444463031")
    
    #install pse
    send("80E60C00 24 06 A00000000316 07 A0000000031650 0E 315041592E5359531E4444463031 0100 02C900 00")
    #install ppse
    send("80E60C00 24 06A00000000316 07 A0000000031650 0E 325041592E5359532E4444463031 0100 02C900 00")
    #install aid
    #send("80E60C00 21 08 A000000333010130 07 A0000003330101 08 A000000333010101 0110 03C9012A 00")
    send("80E60C00 1D 06 A00000000310 07 A0000000031056 07 A0000000031010 0110 02C900 00")
    #perso pse
    send("00A40400 0E 315041592E5359532E4444463031")  
    auth.open_secure_channel("404142434445464748494A4B4C4D4E4F")
    send("80E20000 37 010134703261304F07A0000000031010500D465442205649534120434152449F120B564953412043524544495487010173054203437500")
    send("80E28001 11 91020EA50C8801015F2D02454E9F110101")
    #perso ppse
    send("00A40400 0E 325041592E5359532E4444463031") 
    auth.open_secure_channel("404142434445464748494A4B4C4D4E4F")
    send("80E28000 25 910222A520BF0C1D611B4F07A0000000031010500D46544220564953412043415244870101")
    #perso aid
    send("00A40400 07 A0000000031010")
    dek_session_key = auth.open_secure_channel("404142434445464748494A4B4C4D4E4F")
    cps_perso.perso('FTB.txt','install.xml',dek_session_key)
