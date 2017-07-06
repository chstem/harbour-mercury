import os
import pickle
from .peewee import *
from telethon import tl

db = SqliteDatabase('cache.db')

class BaseModel(Model):
    class Meta:
        database = db

class Dialog(BaseModel):
    id = IntegerField(primary_key=True)
    blob = BlobField()

class Message(BaseModel):
    id = IntegerField(primary_key=True)
    dialog = ForeignKeyField(Dialog, related_name='messages')
    date = DateTimeField()
    blob = BlobField()

# test database connection & create tables if necessary
db.connect()
db.create_tables([Dialog, Message], safe=True)
db.commit()

@db.atomic()
def add_dialog(entity):
    blob = pickle.dumps(entity)
    try:
        dialog = Dialog.get(id=entity.id)
        dialog.blob = blob
    except Dialog.DoesNotExist:
        dialog = Dialog.create(id=entity.id, blob=blob)
    dialog.save()

@db.atomic()
def get_dialog(entity_id):
    dialog = Dialog.get(Dialog.id == entity_id)
    entity = pickle.loads(dialog.blob)
    return entity

@db.atomic()
def add_messages(dialog_id, *messages):
    dialog = Dialog.get(Dialog.id == dialog_id)
    for message in messages:
        m = Message.create(
            id = message.id,
            date = message.date,
            dialog = dialog,
            blob = pickle.dumps(message),
        )
        m.save()
