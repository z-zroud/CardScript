
# convert int value to hex string type
# eg. 48 => '30'
def int_to_hex_str(int_value):
    '''将整形转化为十六进制的字符串'''
    num = '{0:X}'.format(int_value)
    if len(num) % 2 != 0:
        num = '0' + num
    return num

def str_to_int(str_value):
    '''将十六进制的字符串转化为整形'''
    result = 0
    str_len = len(str_value)
    for i in range(str_len):
        result += int(str_value[i],16) * (16 ** (str_len - 1 - i))
    return result

#convert hex str to int, eg. '30' => 48
def hex_str_to_int(str_value):
    '''将十六进制的字符串转化为整形'''
    return int(str_value,16)

    
# get bcd data hex str len
def get_strlen(data):
    '''获取数据的长度，并转化为十六进制的字符串'''
    bcd_len = int(len(data) / 2)
    return int_to_hex_str(bcd_len)

# convert int sw to string sw
def str_sw(sw, prefix=True):
    if prefix:
        s = '0x{0:04X}'.format(sw)
    else:
        s = '{0:04X}'.format(sw)
    return s

#convert bcd to asc str
def bcd_to_str(bcd):
    result = ""
    if len(bcd) % 2 != 0:
        return result
    for index in range(0, len(bcd), 2):
        temp = bcd[index:index + 2]
        asc = chr(int(temp,16))
        result += asc
    return result

def is_hex_str(hex_str):
    str_list = '0123456789ABCDEF'
    for c in hex_str:
        if c not in str_list:
            return False
    return True

if __name__ == '__main__':
    print(bcd_to_str("30303038"))
    print(int_to_hex_str(4))
    print(int_to_hex_str(26))
    print(get_strlen("3F00"))
    print(get_strlen("32149895898392844"))