#!/usr/bin/env python
#encoding: utf-8
#python setup.py sdist upload -r pypi
from setuptools import setup


setup(name="tailor",
      version='0.0.1',
      description='cross platform photo booth',
      author='Leif Theden',
      author_email='leif.theden@gmail.com',
      packages=['tailor'],
      install_requires=['kivy', 'zeroconf', 'shutter', 'pysdl2'],
      license="LGPLv3",
      long_description='https://github.com/bitcraft/tailor',
      classifiers=[
          "Intended Audience :: Developers",
          "Intended Audience :: End Users/Desktop",
          "Development Status :: 2 - Pre-Alpha",
          "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
          "Programming Language :: Python :: 3.4",
          "Operating System :: Android",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: Microsoft :: Windows",
          "Operating System :: POSIX :: Linux",
          "Topic :: Multimedia :: Graphics",
          "Topic :: Multimedia :: Graphics :: Capture :: Digital Camera"
      ],
)
