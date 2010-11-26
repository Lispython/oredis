#!/usr/bin/env python
# -*- coding:  utf-8 -*-

import os
from setuptools import setup
import oredis

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'oredis',
    description = 'Object-hash mapping library for Redis',
    long_description = read('README.markdown'),
    license = 'BSD',
    version = oredis.__version__,
    author = oredis.__author__,
    author_email = oredis.__email__,
    url = 'http://github.com/lispython/oredis/',
    keywords = ['Object', 'hash mapping', 'redis'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
        ],
    packages = ["oredis"], 
    platforms='any',
    test_suite = 'tests', 
    install_requires = ['redis-py']
    )
