from telethon.extensions import BinaryReader
from .peewee import *

def from_bytes(data):
    """convert bytes to Telegram object"""
    with BinaryReader(data=data) as reader:
        return reader.tgread_object()

#####################
###  Basic Setup  ###
#####################

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

####################
###  Exceptions  ###
####################

class DialogDoesNotExist(Exception): pass
class MessageDoesNotExist(Exception): pass
class MessageAlreadyExists(Exception): pass

###################
###  Meta Data  ###
###################

def set_meta(**kwargs):
    with db.atomic() as txn:
        for key, value in kwargs.items():
            try:
                m = Meta.get(key=key)
                m.value = value
            except Meta.DoesNotExist:
                m = Meta.create(key=key, value=value)
            m.save()

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
    blob = entity.to_bytes()
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
        entity = from_bytes(dialog.blob)
        return entity
    except Dialog.DoesNotExist:
        return None

def get_dialogs(limit=-1):
    def last_msg(d):
        if not d.messages:
            return 0
        return d.messages[-1].date.timestamp()
    query = Dialog.select()
    dialogs = list(reversed(sorted(query, key=lambda d: last_msg(d))))
    return [from_bytes(d.blob) for d in dialogs[:limit]]

def add_sender(sender):
    blob = sender.to_bytes()
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
        except Dialog.DoesNotExist:
            sender = None
    if sender:
        return from_bytes(sender.blob)
    return None

def get_self():
    self_id = get_meta('self_id')
    if self_id:
        return get_sender(self_id)
    for sender in Sender.select():
        s = from_bytes(sender.blob)
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
        try:
            dialog = Dialog.get(Dialog.id == dialog_id)
        except Dialog.DoesNotExist:
            raise DialogDoesNotExist('Dialog with id {} does not exist'.format(dialog_id))
        for message, sender in messages:
            try:
                s = Sender.get(id=sender.id)
            except Sender.DoesNotExist:
                s = Sender.create(id=sender.id, blob=sender.to_bytes())
                s.save()
            try:
                m = Message.create(
                    id = message.id,
                    date = message.date,
                    dialog = dialog,
                    sender = s,
                    blob = message.to_bytes(),
                )
                m.save()
            except IntegrityError:
                if Message.get(Message.id == message.id):
                    continue
                    raise MessageAlreadyExists('Message with id {} already exists'.format(message.id))
                else:
                    raise

def get_message(message_id):
    msg = Message.get(id=message_id)
    return from_bytes(msg.blob)

def get_message_sender(message_id):
    msg = Message.get(id=message_id)
    sender = from_bytes(msg.sender.blob)
    return sender

def update_message(message):
    blob = message.to_bytes()
    with db.atomic() as txn:
        try:
            msg = Message.get(id=message.id)
            msg.blob = blob
        except Message.DoesNotExist:
            raise MessageDoesNotExist('Message with id {} does not exist'.format(message.id))
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
    return [(from_bytes(msg.blob), from_bytes(msg.sender.blob)) for msg in query]

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
