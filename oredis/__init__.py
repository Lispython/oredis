#!/usr/bin/env python
# -*- coding:  utf-8 -*-

"""
oredis
~~~~~~

Object-hash redis mapping library

:copyright: (c) 2011 by Alexandr Library (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""


__all__ = ('Model', 'BaseModel', 'Field', 'String', 'Manager', 'Field', 'String', 'HashTable',
           'Link', 'Set', 'List', 'Composite', 'FK', 'StringPK', 'PrimaryKey', 'Integer',
           'DateTime', 'NotFoundError', 'ValidationError', 'ImplementationError', 'get_version')


__version__ = "0.1"
__author__ = "Alexandr (alex@obout.ru)"
__email__ = "alex@bout.ru"
__author__ = "Alex Lispython (alex@obout.ru)"
__license__ = "BSD, see LICENSE for more details"
__version_info__ = (0, 0, 1)
__version__ = ".".join(map(str, __version_info__))
__maintainer__ = "Alexandr Lispython (alex@obout.ru)"


def get_version():
    return __version__

from .models import Model, BaseModel
from .exceptions import NotFoundError, ValidationError, ImplementationError
from .fields import (Field, String, HashTable,  Link,  Set,  List,  Composite, FK,
                    StringPK,  PrimaryKey,  Integer,  DateTime)
from .manager import Manager

