# -*- coding: utf-8 -*-
"""
oredis.models
~~~~~~~~~~~~~

Models for Object-hash mapping library for Redis

:copyright: (c) 2011 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""

from oredis.manager import Manager
from oredis.exceptions import NotFoundError
from oredis.fields import Field, PrimaryKey


class BaseModel(type):
    def __new__(cls, name, bases, attrs):
        new = type.__new__(cls, name, bases, attrs)
        new._fields = {}
        new._managers = {}
        module = attrs['__module__']
        for attr, value in attrs.iteritems():
            if not attr.startswith('__') and isinstance(value, Field):
                new._fields[attr] = value
                value.contribute_to_class(new, attr)

            elif isinstance(value, Manager):
                new._managers[attr] = value
                value.contribute_to_class(new, attr)

        if not 'objects' in new._managers:
            manager = Manager()
            new._managers['objects'] = manager
            manager.contribute_to_class(new, 'objects')

        if not 'id' in new._fields:
            field = PrimaryKey()
            new._fields['id'] = field
            field.contribute_to_class(new, 'id')
        excdict = {'__module__': module}
        new.NotFound = type('NotFound', (NotFoundError, ), excdict)
        return new


class Model(object):
    __metaclass__ = BaseModel
    _redis = None
    _connection = None
    _manager = None

    def __init__(self, **kwargs):
        if self.__class__ == Model:
            raise NotImplementedError('Model must be subclassed')
        self._data = {}
        self._queries = []
        self._queries_counter = 0
        for n, field in self._fields.items():
            self._data[n] = kwargs.get(n, None) or self._fields[n].default
            field.__post_init__(self)
            self._loaded = False


    def __str__(self):
        return u"%s object" % self.__class__.__name__

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self.id)

    def __unicode__(self):
        return self.__str__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.id == self.id

    def __hash__(self):
        return hash(self.id)

    def get_field(self, field_name, default = None):
        value = self._data.get(field_name, None)
        if not value and hasattr(default, "__call__"):
            value = default(self)
        elif not value and hasattr(self._fields[field_name].default, '__call__'):
            value = self._fields[field_name].default()
        if self._loaded and not value:
            return self._fields[field_name].load(self)
        return self.set_field(field_name, value or self._fields[field_name].default)

    def set_field(self, field, value):
        self._data[field] = value
        return self._data[field]

    def update_counter(self):
        self._queries_counter += 1

    def update_queries(self, query):
        self._queries.append(query)
        self.update_counter()

    def get_queries(self):
        total_time = 0
        for x in self._queries:
            total_time += x[-1]
        return {
            'model': self.__class__.  __name__.lower(),
            'count': self._queries_counter,
            'queries': self._queries,
            'total_time': total_time
            }


    @property
    def redis(self):
        return self._connection

    @classmethod
    def key(cls, *args):
        return ':'.join((cls.__name__.lower(), ) + args)

    def validate(self):
        for field in self._fields.values():
            field.validate(field.__get__(self))
        return True

    def save(self):
        self.validate()
        for name, field in self._fields.items():
            field.save(self)
        return True

    def delete(self):
        for name, field in self._fields.items():
            field.delete(self)
        return True

    @classmethod
    def get(cls, id):
        if not cls._connection.sismember(cls.id.key(), id):
            raise cls.NotFound('%s with id %s is not found' % (cls.__name__, id))
        new_model = cls(id=cls.id.to_python(id))
        new_model._loaded = True
        return new_model
