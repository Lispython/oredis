# -*- coding:  utf-8 -*-

from pprint import pprint
import unittest
from random import random
from redis import Redis
from oredis.exceptions import ValidationError
from oredis.models import (Model,  BaseModel)
from oredis.fields import (Field,  String, PrimaryKey,  Integer,  StringPK,  FK,  Composite,  List,  Set,  Link,  HashTable)
from oredis.manager import Manager

r = Redis()


    
class SuperUser(Model):
    name = String(required = True)
    description = String()
    tags = Set()

    
class NoteModel(Model):
    note = String(required = True)
    css = String()
    id = PrimaryKey()
    comments = Integer(required = False, default = 0)
    pk_hash = StringPK()
    #author =  FK(User)

    
class User(Model):
    name = String(required = True)
    description = String()
    likes = List()
    tags = Set()

    
class TagModel(Model):
    id = StringPK(require = True)
    counter = Integer(require = False, default = 0)

class HashModel(Model):
    name = String(required = True)
    data = HashTable()
    
class Author(Model):
    name = StringPK(require = False)
    tags = Link(TagModel)

    
class Reply(Model):
    to = FK('self', required = False)
    message = String()
    id = StringPK()

    
class UserProfile(Model):
    id = StringPK()
    user = FK(User)
    twitter = String()

    
class ArticleManager(Manager):
    def some_method(self):
        return "Some method work for model %s with name %s" % (self._model, self._name)

    
class Article(Model):
    title = String(required = True)
    body = String()

    amanager = ArticleManager(r)

    
class OredisTestCase(unittest.TestCase):
    def setUp(self):
        self.message = """
        This is a text for oredis -  object redis mapping library
        """
        self.id1 = int(random() * 100)
        self.message2 = """
        This is a second testing message.
        """
        self.css = """
        .test {
        color: #485485;
        background-color: #ffffff;
            }
        """
        self.user = User(name = "Alexandr", description = "It's a very crazy man!")
        self.super_user = User(name = "Superuser", description = "It't super user man!")
        self.note = NoteModel(
            note = self.message,
            css = self.css,
            id = self.id1,
            comments = None,
            #author = self.user
            )
        self.note_without_cid = NoteModel(
            note = self.message2, 
            css = self.css
            )

    def testConnection(self):
        pass

    def testModels(self):
        nid = int(random() * 100)
        note = NoteModel(
            note = self.message,
            css = self.css,
            id = nid
            )
        note_without_cid = NoteModel(
            note = self.message2, 
            css = self.css
            )
        self.assertEqual(note.note, self.message)
        self.assertEqual(note.css, self.css)
        self.assertEquals(isinstance(note, NoteModel), True)
        self.assertEqual(repr(self.note), u'<%s: %s>' % (self.note.__class__.__name__, unicode(self.note.id)))
        self.assertEqual(repr(self.note_without_cid), u'<%s: %s>' % (self.note_without_cid.__class__.__name__, unicode(self.note_without_cid.id)))
        self.assertNotEqual(self.note, self.note_without_cid)
        self.assertNotEqual(self.note.note, self.note_without_cid.note)
        self.assertEqual(self.note.id, self.id1)
        self.assertNotEqual(self.note_without_cid.id, self.note.id)

        self.assertEqual(str(self.note), "%s object" % self.note.__class__.__name__ )
        
        self.assertEqual(self.note.key(), self.note.__class__.__name__.lower())
        self.assertEqual(self.note.key("123"), ":".join((self.note.__class__.__name__.lower(), "123")))
        self.assertEqual(self.note.key(str(self.id1)), ":".join((self.note.__class__.__name__.lower(), str(self.id1))))
        note.save()
        note_without_cid.save()
        self.assertEqual(NoteModel.get(note.id).note, note.note)
        self.assertEqual(NoteModel.get(note.id).css, note.css)
        self.assertEqual(NoteModel.get(note_without_cid.id).note, note_without_cid.note)
        self.assertEqual(NoteModel.get(note_without_cid.id).css, note_without_cid.css)
        self.assertEqual(isinstance(NoteModel.get(note_without_cid.id), NoteModel), True)
        self.assertEqual(note.get_queries()['count'], 5)
        self.assertEqual(note_without_cid.get_queries()['count'], 6)
        
    def testProfile(self):
        twitter = "http:// twitter.com/Lispython"
        profile = UserProfile(
            user = self.user, 
            twitter = twitter
            )
        profile.save()
        self.assertEqual(twitter, profile.twitter)
        self.assertEquals(profile.user, self.user)

    def testReply(self):
        message1 = "Hello world!"
        message2 = "Reply to hello world message!"
        message3 = "Bad reply!"
        m1 = Reply(
            message = message1
            )
        self.assertEqual(m1.message, message1)
        self.assertEqual(m1.to, None)
        m2 = Reply(
            message = message2, 
            to = m1
            )
        self.assertEqual(m2.message, message2)
        self.assertEqual(m2.to, m1)
        m2.save()
        m1.save()
        self.assertEqual(m1.reply, m2)
        
    def testList(self):
        langs = ["ruby", "digg", "habr", "reddit",  "golang"]
        user =  self.user
        user.save()
        self.assertEqual(len(user.likes), 0)
        for x in langs:
            user.likes.append(x)
        self.assertEqual(len(user.likes), len(langs))
        self.assertEqual(len(user.likes[1:2]), len(langs[1:2]))
        self.assertEqual(user.likes[1:2], langs[1:2])
        user.likes[2] = "ycombinator"
        del(user.likes[3])
        user2 = User.get(user.id)
        self.assertEqual(user2.likes[2], user.likes[2])
        self.assertEqual(user2.likes, user.likes)
        user.likes.prepend("dzone")
        self.assertEqual(user.likes.rpop(), langs[len(langs)-1])
        self.assertEqual(user.likes.lpop(), "dzone")
        

    def testComposite(self):
        tags =  set(['django', 'python', 'ruby', 'erlang'])
        super_tags =  set(['python',   'hsakel', 'erlang', 'django'])
        for x in tags:
            self.user.tags.add(x)
        for x in super_tags:
            self.super_user.tags.add(x)
        self.assertEqual(len(self.user.tags.inter(self.super_user.tags)), 3)
        self.assertEqual(self.user.tags.inter(self.super_user.tags), tags.intersection(super_tags))
        self.assertEqual(len(self.user.tags.union(self.super_user.tags)), 5)
        self.assertEqual(self.user.tags.union(self.super_user.tags), tags.union(super_tags))
        self.assertEqual(len(self.user.tags.diff(self.super_user.tags)), 1)
        self.assertEqual(self.user.tags.diff(self.super_user.tags), tags.difference(super_tags))
        self.assertEqual(self.user.tags, tags)
        self.user.tags.add('bbb')
        self.assertNotEqual(self.user.tags, tags)
        self.user.tags.rem('ruby')
        self.assertNotEqual(self.user.tags, tags)
        self.assertEqual(len(self.user.tags), len(tags))
        self.user.tags.pop()
        self.assertEqual(len(self.user.tags), 3)

    def testLink(self):
        user = Author(
            name = "Alexander"
            )
        user.save()
        tags =  set(['django', 'python', 'ruby', 'erlang'])
        tags_models = []
        for x in tags:
            t =  TagModel(id = x)
            t.save()
            tags_models.append(t)
            user.tags.add(t)
        self.assertRaises(ValidationError, user.tags.add,  "bbfbf")
        self.assertEqual([x for x in user.tags], tags_models)
        self.assertEqual(len(user.tags),len(tags))
        user.tags.rem(tags_models[3])
        self.assertEqual(len(user.tags),len(tags) - 1)
        self.assertEqual(isinstance(user.tags.pop(), TagModel), True)
        user.save()
        user2 = Author.get(user.id)
        self.assertEqual(user2, user)
        self.assertEqual([ x for x in user2.tags], [x for x in user.tags])
        

    def testHash(self):
        h = HashModel(
            name = "Test table")
        test_hash = {
            'name': 'alex',
            'password': 'trololo',
            'email': 'bbbbbb', 
            'code': 'jwehfbwefwe'
            }
        for k, v in test_hash.items():
           h.data[k] = v
        h.save()
        ## h.data = {
        ##     'bbbb': 'trololo',
        ##     'fjwehfw': 'fwefwefw'
        ##     }
        for k, v in test_hash.items():
            self.assertEqual(h.data[k], v)
        self.assertEqual(len(h.data), len(test_hash))
        self.assertEqual(h.data.keys(), test_hash.keys())
        self.assertEqual(h.data.values(), test_hash.values())
        self.assertEqual(h.data.getall(), test_hash)
        self.assertEqual(h.data.exist('name'), True)
        h2 = HashModel.get(id = h.id)
        for x in h2.data:
            self.assertEqual(h2.data[x], test_hash[x])
        
    def testFields(self):
        self.assertEqual(self.note.validate(), True)
        self.assertEqual(self.note.save(), True)
        

class ManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.article = Article(
            title = "My first article",
            body = "I love the world!"
            )

    def testManager(self):
        self.assertEqual(Article.amanager.connection.ping(), True)
        self.assertEqual(Article.amanager.some_method(), "Some method work for model %s with name %s" % (Article, Article.amanager._name))

    
if __name__ == "__main__":
    unittest.main()
