
import os
import shutil


cwd = os.path.dirname(os.path.abspath(__file__))

perso_lib_path = os.path.join(cwd,'perso_lib')
lib_link_path = os.path.join(cwd,'perso_lib.egg-info')


def main(path, out):
    for files in os.listdir(path):
        name = os.path.join(path, files)
        back_name = os.path.join(out, files)
        if os.path.isfile(name):      
            if os.path.isfile(back_name):
                shutil.copy(name,back_name)     
            else:
                shutil.copy(name, back_name)
        else:
            if not os.path.isdir(back_name):
                os.makedirs(back_name)
            main(name, back_name)


if __name__ == '__main__':
    from distutils import sysconfig
    dst = sysconfig.get_python_lib()
    dst_perso_path = os.path.join(dst,'perso_lib')
    dst_link_path = os.path.join(dst,'perso_lib.egg-info')
    if not os.path.exists(dst_perso_path):
        os.makedirs(dst_perso_path)
    if not os.path.exists(dst_link_path):
        os.makedirs(dst_link_path)
    main(perso_lib_path, dst_perso_path)
    main(lib_link_path, dst_link_path)
