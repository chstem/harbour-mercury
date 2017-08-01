import pickle
from .peewee import *

####################
###  Basic Setup ###
####################

db = SqliteDatabase(None, threadlocals=False, check_same_thread=False)

class BaseModel(Model):
    class Meta:
        database = db

class Meta(BaseModel):
    key = CharField(primary_key=True)
    value = BareField()

class Dialog(BaseModel):
    id = IntegerField(primary_key=True)
    blob = BlobField()

class Sender(BaseModel):
    id = IntegerField(primary_key=True)
    blob = BlobField()

class Message(BaseModel):
    id = IntegerField(primary_key=True)
    dialog = ForeignKeyField(Dialog, related_name='messages')
    sender = ForeignKeyField(Sender, related_name='messages')
    date = DateTimeField()
    blob = BlobField()

def initialize(dbfile):
    db.init(dbfile)
    db.connect()
    db.create_tables([Meta, Dialog, Sender, Message], safe=True)
    db.commit()

###################
###  Meta Data  ###
###################

def add_meta(**kwargs):
    with db.atomic() as txn:
        for key, value in kwargs.items():
            Meta.get_or_create(key=key, value=value)

def get_meta(*keys):
    if not keys:
        query = Meta.select()
    else:
        query = Meta.select().where(Meta.key << keys)
    meta = {item.key:item.value for item in query}
    if len(keys) == 1:
        return meta.get(keys[0], None)
    return meta

#############################
###  Dialogs and Senders  ###
#############################

def add_dialog(entity):
    blob = pickle.dumps(entity)
    with db.atomic() as txn:
        try:
            dialog = Dialog.get(id=entity.id)
            dialog.blob = blob
        except Dialog.DoesNotExist:
            dialog = Dialog.create(id=entity.id, blob=blob)
        dialog.save()

def get_dialog(entity_id):
    try:
        dialog = Dialog.get(Dialog.id == entity_id)
        entity = pickle.loads(dialog.blob)
        return entity
    except Dialog.DoesNotExist:
        return None

def add_sender(sender):
    blob = pickle.dumps(sender)
    with db.atomic() as txn:
        try:
            s = Sender.get(id=sender.id)
            s.blob = blob
        except Sender.DoesNotExist:
            s = Sender.create(id=sender.id, blob=blob)
        s.save()

def get_sender(sender_id):
    try:
        sender = Sender.get(Sender.id == sender_id)
    except Sender.DoesNotExist:
        sender = None
    if not sender:
        try:
            sender = Dialog.get(Dialog.id == sender_id)
        except Sender.DoesNotExist:
            sender = None
    if sender:
        return pickle.loads(sender.blob)
    return None

def get_self():
    self_id = get_meta('self_id')
    if self_id:
        return get_sender(self_id)
    for sender in Sender.select():
        s = pickle.loads(sender.blob)
        if s.is_self:
            return s
    return None

##################
###  Messages  ###
##################

def add_messages(dialog_id, messages):
    """
    messages needs to be a sequence of (message, sender)
    """
    with db.atomic() as txn:
        dialog = Dialog.get(Dialog.id == dialog_id)
        for message, sender in messages:
            try:
                s = Sender.get(id=sender.id)
            except Sender.DoesNotExist:
                s = Sender.create(id=sender.id, blob=pickle.dumps(sender))
                s.save()
            m = Message.create(
                id = message.id,
                date = message.date,
                dialog = dialog,
                sender = s,
                blob = pickle.dumps(message),
            )
            m.save()

def get_message(message_id):
    msg = Message.get(id=message_id)
    return pickle.loads(msg.blob)

def get_message_sender(message_id):
    msg = Message.get(id=message_id)
    sender = pickle.loads(msg.sender.blob)
    return sender

def update_message(message):
    blob = pickle.dumps(message)
    with db.atomic() as txn:
        try:
            msg = Message.get(id=message.id)
            msg.blob = blob
        except Message.DoesNotExist:
            msg = Message.create(id=message.id, blob=blob)
        msg.save()

def delete_messages(message_ids):
    with db.atomic() as txn:
        Message.delete().where(Message.id << message_ids).execute()

def messages_count(dialog_id):
    return Message.select().join(Dialog).where(Dialog.id == dialog_id).count()

def get_message_history(dialog_id, limit=0, max_id=0, min_id=0):
    """
    Gets the message history for the specified entity (dialog_id)

    :param dialog_id:   The dialog_id (or input peer) from whom to retrieve the message history
    :param limit:       Maximum Number of messages to be retrieved
    :param max_id:      All the messages with a higher (newer) ID or equal to this will be excluded
    :param min_id:      All the messages with a lower (older) ID or equal to this will be excluded

    :return: list of (message, sender)
    """
    query = Message.select().join(Dialog).where(Dialog.id == dialog_id)
    if max_id:
        query = query.where(Message.id <= max_id)
    if min_id:
        query = query.where(Message.id >= min_id)
    query = query.order_by(-Message.id)
    if limit:
        query = query.limit(limit)
    return [(pickle.loads(msg.blob), pickle.loads(msg.sender.blob)) for msg in query]

def get_last_message(dialog_id):
    """get newest message_id (highest id) cached for dialog_id"""
    query = Message.select().join(Dialog).where(Dialog.id == dialog_id)
    query = query.order_by(-Message.id).first()
    if query:
        return query.id
    else:
        return 0

def get_first_message(dialog_id):
    """get oldest message_id (lowest id) cached for dialog_id"""
    query = Message.select().join(Dialog).where(Dialog.id == dialog_id)
    query = query.order_by(Message.id).first()
    if query:
        return query.id
    else:
        return 0
