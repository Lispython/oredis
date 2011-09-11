Object-hash mapping library for Redis.
--------------------------------------

Oredis is a library for storing objects in Redis, a persistent key-value database. It includes an extensible list of validations and has very good performance.


## How to use

    from oredis.models import Model
    from oredis.manager import Manager
    from oredis.fields import String, PrimaryKey, StringPK, Integer, DateTime

    class NoteManager(Manager):
        pass

    class NoteModel(Model):
        id = PrimaryKey()
        title = String()
        pk_hash = StringPK()
        body = String(required = True)

        objects = NoteManager(connection = redis.Redis())

     In [19]: note1 = NoteModel(title = "Hello world!",
        ....: body="I am currently engaged in teaching my brother to program.
        He is a total beginner, but very smart. (And he actually wants to learn).
        I've noticed that some of our sessions have gotten bogged down in minor details,
        and I don't feel I've been very organized. (But the answers to this
        post have helped a lot.)")

     In [20]: note1
     Out[20]: <NoteModel: 942>

     In [21]: note1.title
     Out[21]: 'Hello world!'

     In [22]: note1.title


## Credits

Thanks Alexander Solovyov for some concepts are taken from orem library.