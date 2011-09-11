# -*- coding: utf-8 -*-

"""
oredis.exceptions
~~~~~~~~~~~~~~~~~

Exceptions module for Object-Redis Mapper

:copyright: (c) 2011 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""

class ValidationError(Exception):
    pass

class NotFoundError(Exception):
    pass

class ImplementationError(Exception):
    pass
