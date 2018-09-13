from perso_lib import utils

class FileHandle:
    def __init__(self,file_name,mode):
        self.file_name = file_name
        self._file = open(file_name,mode)

    @property
    def current_offset(self):
        return self._file.tell()

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

    def read_binary(self,offset,read_len):
        data = ''
        #self._file.seek(offset,0)
        value_arr = self.read(offset,read_len)
        for value in value_arr:
            data += utils.int_to_hex_str(value)
        return data
        
    def read_int(self,offset):
        data = self.read_binary(offset,2)
        return utils.str_to_int(data)



if __name__ == '__main__':
    fh = FileHandle('PBH00PBH.00D','rb+')
    for i in range(5):
        value = fh.read_binary(fh.current_offset,2)
        value = fh.read_int(fh.current_offset)