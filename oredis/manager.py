# -*- coding:  utf-8 -*-
"""
oredis.manager
~~~~~~~~~~~~~~

Manager class for redis models

:copyright: (c) 2011 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""


from redis import Redis


class ManagerDescriptor(object):
    def __init__(self, manager):
        self.manager = manager

    def __get__(self, instance, type=None):
        if instance != None:
            raise AttributeError("Manager isn't accessible via %s instances" % type.__name__)
        return self.manager



class Manager(object):
    """Functons for managing redis queries
    """
    _connection = None
    def __init__(self, connection = None, *args, **kwargs):
        self._model = None
        self._name = None
        self.db = None
        self.setup_connection(connection)

    def setup_connection(self, connection = None, *args, **kwargs):
        if connection: self._connection = connection
        else: self._connection = Redis(*args, **kwargs)
        return self._connection

    @property
    def connection(self):
        return self._connection

    def contribute_to_class(self, model, name):
        self._model = model
        self._name = name
        self._model._connection = self._connection
        setattr(model, name, ManagerDescriptor(self))



