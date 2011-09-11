#!/usr/bin/env python
# -*- coding:  utf-8 -*-
"""
oredis.setup
~~~~~~~~~~~~

Object-hash mapping library for Redis

:copyright: (c) 2011 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""



import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

__version__ = '0.1'
__author__ = 'Alexandr'
__email__ = 'alex@obout.ru'



try:
    readme_content = open(os.path.join(os.path.abspath(
        os.path.dirname(__file__)), "README.rst")).read()
except Exception, e:
    print(e)
    readme_content = __doc__


setup(
    name='oredis',
    description='Object-hash mapping library for Redis',
    long_description=readme_content,
    license='BSD',
    version=__version__,
    author=__author__,
    author_email=__email__,
    url='http://github.com/lispython/oredis/',
    keywords=['Object', 'hash mapping', 'redis'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
        ],
    packages=["oredis"],
    platforms='any',
    test_suite='tests',
    install_requires=['redis']
    )
