import os
from perso_lib import utils

class FileHandle:
    def __init__(self,file_name,mode):
        self.file_name = file_name
        self._file = open(file_name,mode)

    @property
    def current_offset(self):
        return self._file.tell()

    @property
    def file_size(self):
        return os.path.getsize(self.file_name)

    @property
    def EOF(self):
        return self.current_offset == self.file_size

    def read_line(self):
        value = self._file.readline()
        ret = str(value).endswith('\n')
        if ret:
            value = value[0 : len(value) - 1]
        ret = value.endswith('\r')
        if ret:
            value = value[0 : len(value) - 1]
        return value

    def read(self,offset,read_len):
        self._file.seek(offset,0)
        return self._file.read(read_len)

    def read_pos(self,start,end):
        if start > 0:
            start = start - 1   #从1开始
        read_len = end - start
        return self.read(start,read_len)

    def read_str(self,offset,read_len):
        '''读取二进制文件，并转换为字符串形式'''
        data = self.read(offset,read_len)
        return bytes.decode(data)

    def read_binary(self,offset,read_len):
        '''读取二进制文件，并按二进制呈现为字符串形式'''
        data = ''
        #self._file.seek(offset,0)
        value_arr = self.read(offset,read_len)
        for value in value_arr:
            data += utils.int_to_hex_str(value)
        return data
        
    def read_int(self,offset):
        '''按二进制顺序读取2字节，转换为整形'''
        data = self.read_binary(offset,2)
        return utils.hex_str_to_int(data)

    def read_short(self,offset):
        '''按二进制顺序读取1字节，转换为整形'''
        data = self.read_binary(offset,1)
        return utils.hex_str_to_int(data)

    def read_int_reverse(self,offset):
        '''读取2字节，逆序转换为整形'''
        data = self.read_binary(offset,2)
        hex_str = ''
        for i in range(0,4,2):
            hex_str += data[2 - i : 2 - i + 2]
        return utils.hex_str_to_int(hex_str)

    def read_int64(self,offset):
        '''读取4字节，并将ASCII转化为整形'''
        data = self.read_binary(offset,4)
        return utils.hex_str_to_int(data)

    def read_int64_reverse(self,offset):
        '''读取4个字节，全部逆序转换为整形'''
        data = self.read_binary(offset,4)
        hex_str = ''
        for i in range(0,8,2):
            hex_str += data[6 - i : 6 - i + 2]
        return utils.hex_str_to_int(hex_str)



if __name__ == '__main__':
    fh = FileHandle('PBH00PBH.00D','rb+')
    for i in range(5):
        value = fh.read_binary(fh.current_offset,2)
        value = fh.read_int(fh.current_offset)
        value = fh.read_int(fh.current_offset)
        value = fh.read_str(fh.current_offset,2)