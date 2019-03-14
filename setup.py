import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="perso_lib",
    version="2.0.0.7",
    author="z_road",
    author_email="489469935@qq.com",
    description="A lib for parse dp data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/z-zroud/CardScript",
    packages=setuptools.find_packages(),
    # packages=['perso_lib'],
    package_data={

        '':['dll/*','template/*'],
    },
    install_requires=[
        'openpyxl',
        'python-docx',
        'pillow'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)