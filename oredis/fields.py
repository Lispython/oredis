# -*- coding: utf-8 -*-

"""
oredis.fields
~~~~~~~~~~~~~

Fields for redis models

:copyright: (c) 2011 by Alexandr Lispython (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""

import copy
import uuid
from utils import timer
from datetime import datetime
from types import IntType, NoneType
from oredis.exceptions import ValidationError
from oredis.utils import super_force_unicode as sfu


def import_attr(module, name=None):
    """
    Import attribute using string reference.
    Example:
    import_attribute('a.b.c.foo')
    Throws ImportError or AttributeError if module or attribute do not exist.
    """
    if not name:
        module, name = module.rsplit('.', 1)
    mod = __import__(module, globals(), locals(), [name])

    return getattr(mod, name)



class Field(object):
    def __init__(self, required=False, default=None, **kwargs):
        self.required = required
        self.default = default

        self._name = None
        self._model = None
        self._data = None

    def __post_init__(self, model):
        pass

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, str(self._name))

    def __str__(self):
        return u"<%s> field object" % self._name or "*unbound*"

    def __get__(self, instance, owner=None):
        assert self._name, 'field is not initialized'
        if not instance:
            return self
        field_data = instance.get_field(self._name)
        field_data= self.to_python(field_data) if field_data else None
        return field_data

    def __set__(self, instance, value):
        assert self._name, 'field is not initialized'
        instance.set_field(self._name, self.from_python(value))

    def contribute_to_class(self, model, name):
        self._model = model
        self._name = name
        setattr(model, name, self)

    @property
    def pyname(self):
        assert self._name, 'field is not initialized'
        return '%s.%s' % (self._model.__name__, self._name)

    @property
    def redis(self):
        return self._model._connection

    def validate(self, value):
        if self.required and value in [None, '']:
            raise ValidationError('field %s is required' % self.pyname)
        return True

    def to_python(self, value):
        return value

    def from_python(self, value):
        self.validate(value)
        return value

    def key(self, instance = None):
        return self._model.key(str(instance.id), self._name)

    def delete(self, instance):
        cmd = self.deletecmd(instance)
        if not cmd:
            return
        self.execute_cmd(instance, cmd)

    def load(self, instance):
        cmd = self.loadcmd(instance)
        if not cmd:
            return
        return instance.set_field(self._name, self.execute_cmd(instance, cmd))

    def save(self, instance):
        cmd = self.savecmd(instance)
        if not cmd:
            return
        if cmd[2] is  None or cmd[2] == '' or cmd[2] == u'' or cmd[2] == "None" or cmd[2] == u"None":
            return
        self.execute_cmd(instance, cmd)

    @timer
    def execute_cmd(self, instance, cmd):
        return getattr(self.redis, cmd[0])(*cmd[1:])

    def deletecmd(self, instance):
        return ('delete', self.key(instance))

    def loadcmd(self, instance):
        return 'get', self.key(instance)

    def savecmd(self, instance):
        return ('set', self.key(instance), instance._data[self._name])

    def default(self):
        return None

    def get_internal_type(self):
        return "Field"


class String(Field):
    def to_python(self, value):
        super(String, self).to_python(value)
        return sfu(value)

    def from_python(self, value):
        super(String, self).to_python(value)
        return sfu(value)

    def get_internal_type(self):
        return "String"


class Integer(Field):
    def validate(self, value):
        super(Integer, self).validate(value)
        if not isinstance(value, IntType) and not isinstance(value, NoneType):
            raise ValidationError('field %s is required int value' % self.pyname)
        return True

    def to_python(self, value):
        try:
            return int(value)
        except ValueError:
            raise ValidationError('field %s requires integer value' % self.pyname)

    def from_python(self, value):
        value = super(Integer, self).from_python(value)
        try:
            return int(value)
        except ValueError:
            raise ValidationError('field %s requires integer value' % self.pyname)

class DateTime(Field):
    def to_python(self, value):
        return datetime.fromtimestamp(float(value))

    def from_python(self, value):
        value = super(DateTime, self).from_python(value)
        if not isinstance(value, datetime):
            raise ValidationError('field %s requires datetime value' % self.pyname)
        return value.strftime('%s')


class PrimaryKey(Integer):
    def __init__(self, *args, **kwargs):
        super(PrimaryKey, self).__init__(required=True, *args, **kwargs)

    def __get__(self, instance, owned = None):
        if not instance:
            return self
        return instance.get_field(self._name, self.next)

    def default(self):
        return self.next()

    def key(self, instance=None):
        return self._model.key('all')

    def next(self, instance):
        return self.execute_cmd(instance, ('incr', self._model.key()))

    def savecmd(self, instance):
        return 'sadd', self.key(), self.from_python(self.__get__(instance))

    def deletecmd(self, instance):
        return 'srem', self.key(), self.from_python(self.__get__(instance))

    def loadcmd(self, instance):
        return

    def get_internal_type(self):
        return "PrimaryKey"

class StringPK(String):
    def __init__(self, *args, **kwargs):
        super(StringPK, self).__init__(required=True, *args, **kwargs)

    def __get__(self, instance, owned = None):
        if not instance:
            return self
        return instance.get_field(self._name, self.next)

    def key(self, instance=None):
        return self._model.key('all')

    def next(self, instance):
        return uuid.uuid4().hex

    def savecmd(self, instance):
        return 'sadd', self.key(), self.from_python(self.__get__(instance))

    def deletecmd(self, instance):
        return 'srem', self.key(), self.from_python(self.__get__(instance))

    def loadcmd(self, instance):
        return

    def get_internal_type(self):
        return "StringPK"


class FK(Field):
    def __init__(self, to, related_name = None, *args, **kwargs):
        super(FK, self).__init__(*args, **kwargs)
        self.to = to
        self._related_name = related_name

    def __post_init__(self, model):
        super(FK, self).__post_init__(model)
        if self.to == 'self':
            self.to = self._model
        elif isinstance(self.to, basestring):
            self.to = import_attr(self.model.__module__, self.to)
        self._related_name = self._related_name or model.__class__.__name__.lower()
        setattr(self.to, self._related_name, model)

    def __get__(self, instance, owner=None):
        return super(FK, self).__get__(instance, owner)

    def validate(self, value):
        from models import Model
        super(FK, self).validate(value)
        if not isinstance(value, Model) and not isinstance(value, NoneType):
            raise ValidationError('field %s is required field instance value' % self.pyname)
        return True
    def from_python(self, value):
        try:
            return value.id
        except AttributeError:
            raise ValidationError('field %s only accepts models as values' % self.pyname)

    def to_python(self, value):
        return value

    def contribute_to_class(self, model, name):
        super(FK, self).contribute_to_class(model, name)
        self._model = model
        self._name = name
        setattr(model, name, self)

    def get_internal_type(self):
        return "FK"

class Composite(Field):
    def __get__(self, instance, owner=None):
        new = copy.copy(self)
        new.instance = instance
        return new

    def __set__(self, instance, value):
        raise AttributeError('use append/prepend to change %ss' % self.__class__.__name__.lower())

    def __str__(self):
        return str(self.value)

    def savecmd(self, instance):
        return

    @property
    def value(self):
        assert self.instance, '%s is not initialized' % self.pyname
        return super(Composite, self).__get__(self.instance)

    def get_internal_type(self):
        return "Composite"


class List(Composite):
    def __init__(self, handler=unicode, *args, **kwargs):
        super(List, self).__init__(*args, **kwargs)
        self.handler = handler
        self.instance = None

    def loadcmd(self, instance):
        return 'lrange', self.key(instance), 0, -1

    def to_python(self, value):
        value = super(List, self).to_python(value)
        return value and map(self.handler, value) or value

    def from_python(self, value):
        return self.handler(super(List, self).from_python(value))
    # list methods

    def __eq__(self, other):
        return self.value == other

    def __len__(self):
        return self.execute_cmd(self.instance, ('llen', self.key(self.instance)))

    def __str__(self):
        return str(self.value)

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, value):
        self.value[index] = value
        self.lset(value, index)

    def __delitem__(self, index):
        if isinstance(index, slice): return False
        uid = uuid.uuid4().hex
        self.lset(uid, index)
        self.lrem(self.value[index])

    def append(self,  value):
        self.execute_cmd(self.instance, ('rpush', self.key(self.instance), self.from_python(value)))
        self.load(self.instance)

    def prepend( self, value):
        self.execute_cmd(self.instance, ('lpush', self.key(self.instance), self.from_python(value)))
        self.load(self.instance)

    def rpop(self):
        return self.execute_cmd(self.instance, ('rpop', self.key(self.instance)))

    def lpop(self):
        return self.execute_cmd(self.instance, ('lpop', self.key(self.instance)))

    def lset(self, value, position):
        self.execute_cmd(self.instance, ('lset', self.key(self.instance), int(position), self.from_python(value)))
        self.load(self.instance)

    def lrem( self, value, count = 0):
        self.execute_cmd(self.instance, ('lrem', self.key(self.instance), self.from_python(value), int(count), ))
        self.load(self.instance)

    def lindex(self, index):
        return self.execute_cmd(self.instance, ('lindex', self.key(self.instance), int(index)))

    def trim(self, start=0, end=-1):
        self.execute_cmd(self.instance, ('ltrim', start, end))
        self.load(self.instance)

    def lrange(self, start = 0, end =- 1):
        return self.to_python(self.execute_cmd(self.instance, ('lrange', self.key(self.instance), start, end)))

    def get_internal_type(self):
        return "List"


class Set(Composite):
    def __init__(self, handler=unicode, *args, **kwargs):
        super(Set, self).__init__(*args, **kwargs)
        self.handler = handler
        self.instance = None

    def loadcmd(self, instance):
        return 'smembers', self.key(instance)

    def to_python(self, value):
        value = super(Set, self).to_python(value)
        return value and set(map(self.handler, value)) or value

    def __eq__(self, other):
        return self.value == other

    def __iter__(self):
        return self.value.__iter__()

    def __len__(self):
        return self.execute_cmd(self.instance, ('scard', self.key(self.instance)))

    def pop(self):
        pop = self.execute_cmd(self.instance, ('spop', self.key(self.instance)))
        self.load(self.instance)
        return self.handler(pop)

    def add(self, value):
        self.validate_value(value)
        self.execute_cmd(self.instance, ('sadd', self.key(self.instance), self.from_python(value)))
        self.load(self.instance)

    def rem(self, value):
        self.validate_value(value)
        self.execute_cmd(self.instance, ('srem', self.key(self.instance), self.from_python(value)))
        self.load(self.instance)

    def validate_value(self, value):
        return True

    def _interact(self, cmd, other):
        return self.execute_cmd(self.instance, (cmd, (self.key(self.instance), other.key(other.instance))))

    inter = lambda self, other: self._interact('sinter', other)
    union = lambda self, other: self._interact('sunion', other)
    diff = lambda self, other: self._interact('sdiff', other)

    def get_internal_type(self):
        return "Set"


class Link(Set):
    def __init__(self, to, related_name = None, *args, **kwargs):
        super(Link, self).__init__(*args, **kwargs)
        self.to = to
        self._related_name = related_name
        if not isinstance(to, basestring):
            self.handler = to.get


    def __post_init__(self, model):
        super(Link, self).__post_init__(model)
        if self.to == 'self':
            self.to = self._model
        elif isinstance(self.to, basestring):
            self.to = import_attr(self.model.__module__, self.to)
        self._related_name = self._related_name or model.__class__.__name__.lower()
        setattr(self.to, self._related_name, model)

    def __get__(self, instance, owner=None):
        return super(Link, self).__get__(instance, owner)

    def validate(self, value):
        super(Link, self).validate(value)
        if isinstance(value, NoneType):
            return True
        if not isinstance(value, Link):
            raise ValidationError('field %s is required Link instance value' % self.pyname)

        return True

    def validate_value(self, value):
        super(Link, self).validate_value(value)
        if not isinstance(value, self.to):
            raise ValidationError('field item %s is required %s instance value' % (self.pyname,  self.to))
        return True

    def from_python(self, value):
        try:
            if isinstance(value, self.to): return value.id
        except AttributeError:
            raise ValidationError('field %s only accepts models as values' %
                                  self.pyname)

    def to_python(self, value):
        value = super(Link, self).to_python(value)
        return value


    def contribute_to_class(self, model, name):
        super(Link, self).contribute_to_class(model, name)
        self._model = model
        self._name = name
        setattr(model, name, self)

    def get_internal_type(self):
        return "Link"



class HashTable(Field):

    def __get__(self, instance, owner=None):
        new = copy.copy(self)
        new.instance = instance
        return new

    def __post_init__(self,  instance, *args, **kwargs):
        super(HashTable, self).__post_init__(instance, *args, **kwargs)

    def __set__(self, instance, value):
        raise AttributeError('use object methods to change values for %s' %  self.__class__.__name__.lower())

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, str(self._name))

    def __iter__(self):
        return self.value.__iter__()

    def loadcmd(self, instance):
        return 'hgetall', self.key(instance)

    def keys(self):
        return self.execute_cmd(self.instance,  ('hkeys',  self.key(self.instance)))

    def values(self):
        return self.execute_cmd(self.instance,  ('hvals',  self.key(self.instance)))

    def getall(self):
        return self.execute_cmd(self.instance,  ('hgetall',  self.key(self.instance)))

    def exist(self,  key):
        return self.execute_cmd(self.instance,  ('hexists',  self.key(self.instance), key))

    def savecmd(self, instance):
        return

    @property
    def value(self):
        assert self.instance, '%s is not initialized' % self.pyname
        if not self.instance:
            return self
        return self.instance.get_field(self._name,  self.load)

    def load(self, instance):
        cmd = self.loadcmd(instance)
        if not cmd:
            return
        self.instance = instance
        return instance.set_field(self._name, self.getall())

    def __getitem__(self, index):
        return self.value[index]
        return self.execute_cmd(self.instance,  ('hget',  self.key(self.instance),  index))

    def __setitem__(self, index,  value):
        return self.execute_cmd(self.instance,  ('hset',  self.key(self.instance),  index,  value))

    def __len__(self):
        return self.execute_cmd(self.instance,  ('hlen',  self.key(self.instance)))

    def __delitem__(self, index):
        self.execute_cmd(self.instance,  ('hdel',  self.key(self.instance), index))
        self.load(self.instance)

    def from_python(self, value):
        return value

    def to_python(self, value):
        return value

    def get_internal_type(self):
        return "HashTable"
