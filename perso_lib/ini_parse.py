from configparser import ConfigParser

#fix option always lower case bug
class MyIniConfig(ConfigParser):
    def __init__(self,defaults=None):
        ConfigParser.__init__(self,defaults)

    def optionxform(self,optionstr):
        return optionstr

class IniParser:
    def __init__(self,file_name):
        self.file_name = file_name
        self.ini = MyIniConfig()
        self.ini.read(file_name)

    def get_sections(self):
        return self.ini.sections()

    def get_options(self,section):
        return self.ini.options(section)

    def get_first_option_value(self,section):
        options = self.get_options(section)
        for option in options:
            return self.get_value(section,option)
    
    def get_value(self,section,option):
        return self.ini.get(section,option)

    def add_section(self,section):
        if self.ini.has_section(section) is False:
            self.ini.add_section(section)
            self.ini.write(open(self.file_name,'w+'),False)
            return True
        return False

    #若option存在，则添加失败
    #若section不存在，则添加section
    def add_option(self,section,key,value):
        self.add_section(section)
        if self.ini.has_option(section,key):
            return False
        if not key:
            print('保存文件是，ini文件存在值为None的option节点')
        self.ini.set(section,key,value)
        self.ini.write(open(self.file_name,'w+'),False)
        return True

    #若不存在指定的option,则修改失败
    def modify_option(self,section,key,value):
        if self.ini.has_option(section,key):
            self.ini.set(section,key,value)
            self.ini.write(open(self.file_name,'w+'),False)
            return True
        return False


if __name__ == '__main__':
    ini = IniParser('cps.ini')
    ret = ini.get_sections()
    ret = ini.get_options('person')
    ret = ini.get_value('person','age')
    #ini.add_section('shit')
    ini.add_option('shit','key','value')
    ini.add_option('shit','key1','value1')
    ini.add_option('shit','key1','value2')
    ini.modify_option('shit','key','value3')