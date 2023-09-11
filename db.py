from peewee import *

db = SqliteDatabase('data.db')
class User(Model):
    id = CharField()
    name = CharField()
    
    class Meta:
        database = db

class Booking(Model):
    position = AutoField()
    owner = ForeignKeyField(User)

    class Meta:
        database = db