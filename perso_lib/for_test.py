from perso_lib import utils
class ClassName:
    __slots__= ('x','y','__name')
    def __init__(self,x,y,name):
        self.x = x
        self.y = y
        self.__name = name

    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self,value):
        self.__name = value

class DGIData:
    def __init__(self):
        self.dgi = ''
        self.tags = []

if __name__ == '__main__':
    def custom_key(dgi_data):
        number = utils.hex_str_to_int(dgi_data.dgi)
        return number
    cps = []
    data1 = DGIData()
    data2 = DGIData()
    data3 = DGIData()
    data1.dgi = '0201'
    data2.dgi = '0101'
    data3.dgi = '0301'
    cps.append(data1)
    cps.append(data2)
    cps.append(data3)
    cps.sort(key=custom_key)
    for item in cps:
        print(item.dgi)
