from peewee import *

db = SqliteDatabase('data.db')
class User(Model):
    t_id = CharField(unique=True)
    name = CharField(unique=True)
    
    class Meta:
        database = db

class Booking(Model):
    owner = ForeignKeyField(User)

    class Meta:
        database = db