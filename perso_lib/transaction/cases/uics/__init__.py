import os
from ctypes import *

depend_libs = ['libeay32.dll','sqlite3.dll']
dll_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'dll')

for lib in depend_libs:
    dll_path = os.path.join(dll_dir,lib)
    CDLL(dll_path)

xx = os.path.join(dll_dir,'Authencation.dll')
sm_lib = CDLL(os.path.join(dll_dir,'ChineseSM.dll'))
des_lib = CDLL(os.path.join(dll_dir,'Des0.dll'))
auth_lib = CDLL(os.path.join(dll_dir,'Authencation.dll'))
data_parse_lib = CDLL(os.path.join(dll_dir,'DataParse.dll'))
tool_lib = CDLL(os.path.join(dll_dir,'Tool.dll'))


