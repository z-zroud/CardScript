
# convert int value to hex string type
def int_to_hex_str(int_value):
    num = '{0:X}'.format(int_value)
    if len(num) % 2 != 0:
        num = '0' + num
    return num

# get bcd data hex str len
def get_bcd_len(data):
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

if __name__ == '__main__':
    print(bcd_to_str("FF68"))
    print(int_to_hex_str(4))
    print(int_to_hex_str(26))
    print(get_bcd_len("3F00"))
    print(get_bcd_len("32149895898392844"))