#    Copyright (C) 2017 Christian Stemmle
#
#    This file is part of Mercury.
#
#    Mercury is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Mercury is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Mercury. If not, see <http://www.gnu.org/licenses/>.

import os
import pyotherside
from telethon import *

SESSION_ID = 'mercury'
LOCAL_DIR = '/home/nemo/.local/share/harbour-mercury/'
FILE_CACHE = os.path.join(LOCAL_DIR, 'files')
DOWNLOAD_PREFER_SMALL = False       # prefered photo size for download
TIMEFORMAT = '%H:%M'
PROXY = None
DC_IP = None
TEST = 0

if not os.path.isdir(LOCAL_DIR):
    os.makedirs(LOCAL_DIR)
if not os.path.isdir(FILE_CACHE):
    os.makedirs(FILE_CACHE)

os.chdir(LOCAL_DIR)

class Client(TelegramClient):

    def __init__(self, session_user_id, api_id, api_hash, proxy=None):
        super().__init__(session_user_id, api_id, api_hash, proxy)
        self.entities = {}
        self.contacts = {}

    ###############
    ###  login  ###
    ###############

    # login code
    def request_code(self, phonenumber=None):
        if phonenumber:
            self.phonenumber = phonenumber
        self.send_code_request(self.phonenumber)

    def send_code(self, code):
        try:
            status = self.sign_in(phone_number=self.phonenumber, code=code)
        # Two-step verification may be enabled
        except errors.SessionPasswordNeededError:
            return 'pass_required'
        if not status:
            return 'invalid'
        if isinstance(status, tl.types.User):
            return True
        raise ValueError('Unkown return status for sign_in')

    # Two-step verification
    def send_pass(self, password):
        status = self.sign_in(password=password)
        if not status:
            return 'invalid'
        if isinstance(status, tl.types.User):
            return True
        raise ValueError('Unkown return status for sign_in')

    ######################
    ###  request data  ###
    ######################

    def request_contacts(self):
        self.get_contacts()
        contacts_model = []
        for contact, user in self.contacts.values():
            contactdict = {}
            contactdict['user_id'] = 'User_{}'.format(user.id)
            contactdict['name'] = utils.get_display_name(user)
            contacts_model.append(contactdict)
        pyotherside.send('contacts_list', sorted(contacts_model, key=lambda u:u['name']))

    def request_dialogs(self):
        dialogs, entities = self.get_dialogs(limit=0)
        dialogs_model = []

        for entity in entities:
            entity_type = get_entity_type(entity)
            if 'Forbidden' in entity_type:
                # no access, do not add to dialogs_model
                continue
            dialogdict = {}
            dialogdict['name'] = utils.get_display_name(entity)
            dialogdict['entity_id'] = '{}_{}'.format(entity_type, entity.id)

            self.entities[dialogdict['entity_id']] = entity
            dialogs_model.append(dialogdict)

        pyotherside.send('update_dialogs', dialogs_model)

    def request_messages(self, ID):
        entity = self.get_entity(ID)
        total_count, messages, senders = self.get_message_history(entity)

        # Iterate over all (in reverse order so the latest appear last)
        messages_model = [self.build_message_dict(msg, sender) for msg, sender in zip(reversed(messages), reversed(senders))]

        pyotherside.send('update_messages', messages_model)

    ##############################
    ###  download media files  ###
    ##############################

    def download_msg_media(self, message):
        t = get_media_type(message.media)
        if t == 'photo':
            return self.download_photo(message)
        if t == 'document':
            return self.download_document(message)
        if t == 'contact':
            return self.download_contact(message)

    def download_photo(self, message):

        # Determine the photo and its largest size
        if DOWNLOAD_PREFER_SMALL:
            size = message.media.photo.sizes[0]
        else:
            size = message.media.photo.sizes[-1]
        file_size = size.size

        filename = message.media.photo.date.strftime('photo_%Y-%m-%d_%H-%M-%S')
        filename += utils.get_extension(message.media)
        from_id = message.from_id
        file_path = os.path.join(FILE_CACHE, str(from_id))

        if not os.path.isdir(file_path):
            os.makedirs(file_path)

        file_path = os.path.join(file_path, filename)

        if not os.path.isfile(file_path):
            self.download_file(
                tl.types.InputFileLocation(
                    volume_id=size.location.volume_id,
                    local_id=size.location.local_id,
                    secret=size.location.secret
                ),
                file_path,
                file_size=file_size,
                progress_callback=progress_callback
            )

        return file_path

    def download_document(self, message):

        document = message.media.document
        file_size = document.size

        for attr in document.attributes:
            if type(attr) == tl.types.DocumentAttributeFilename:
                filename = attr.file_name
                break  # This attribute has higher priority
            elif type(attr) == tl.types.DocumentAttributeAudio:
                filename = '{} - {}'.format(attr.performer, attr.title)

        if filename is None:
            filename = document.date.strftime('doc_%Y-%m-%d_%H-%M-%S')
        #filename += utils.get_extension(message_media_document)

        from_id = message.from_id
        file_path = os.path.join(FILE_CACHE, str(from_id))

        if not os.path.isdir(file_path):
            os.makedirs(file_path)

        file_path = os.path.join(file_path, filename)

        if not os.path.isfile(file_path):
            self.download_file(
                tl.types.InputDocumentFileLocation(
                    id=document.id,
                    access_hash=document.access_hash,
                    version=document.version
                ),
                file_path,
                file_size=file_size,
                progress_callback=progress_callback
            )

        return file_path

    def download_contact(message):
        """Downloads a media contact using the vCard 4.0 format"""

        first_name = message.media.first_name
        last_name = message.media.last_name
        phone_number = message.media.phone_number

        if last_name and first_name:
            filename = '{} {}'.format(first_name, last_name)
        elif first_name:
            filename = first_name
        else:
            filename = last_name
        filename += '.vcard'
        file_path = os.path.join(FILE_CACHE, filename)

        if not os.path.isfile(file_path):
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write('BEGIN:VCARD\n')
                file.write('VERSION:4.0\n')
                file.write('N:{};{};;;\n'.format(first_name, last_name
                                                if last_name else ''))
                file.write('FN:{}\n'.format(' '.join((first_name, last_name))))
                file.write('TEL;TYPE=cell;VALUE=uri:tel:+{}\n'.format(
                    phone_number))
                file.write('END:VCARD\n')

        return file_path

    ########################
    ###  update handler  ###
    ########################

    def update_handler(self, update_object):

        if isinstance(update_object, tl.types.UpdatesTg):

            # check for new chat messages
            for update in update_object.updates:
                if isinstance(update, tl.types.UpdateNewMessage):
                    from_id = 'User_{}'.format(update.message.from_id)
                    to_entity = update.message.to_id
                    entity_type = get_entity_type(to_entity)
                    if 'User' in entity_type:
                        entity_id = 'User_{}'.format(update.message.from_id)
                    elif 'Chat' in entity_type:
                        entity_id = 'Chat_{}'.format(update.message.to_id.chat_id)
                    msgdict = self.build_message_dict(update.message, self.get_entity(from_id))
                    pyotherside.send('new_message', entity_id, msgdict)

                elif isinstance(update, tl.types.UpdateNewChannelMessage):
                    entity_id = 'Channel_{}'.format(update.message.to_id.channel_id)
                    msgdict = self.build_message_dict(update.message, self.get_entity(entity_id))
                    pyotherside.send('new_message', entity_id, msgdict)

                elif isinstance(update, tl.types.UpdateReadHistoryOutbox) or \
                        isinstance(update, tl.types.UpdateReadHistoryInbox) or \
                        isinstance(update, tl.types.UpdateReadChannelInbox):
                    self.request_dialogs()

        elif isinstance(update_object, tl.types.UpdateShortChatMessage):
            # Group
            entity_id = 'Chat_{}'.format(update_object.chat_id)
            msgdict = self.build_message_dict(update_object, self.get_entity(entity_id))
            pyotherside.send('new_message', entity_id, msgdict)

    ############################
    ###  internal functions  ###
    ############################

    def get_entity(self, ID):

        if ID in self.entities:
            return self.entities[ID]

        entity_type, entity_id = ID.split('_')
        if entity_type == 'Chat':
            entity = self.invoke(tl.functions.messages.GetChatsRequest([entity_id,])).chats[0]
        elif entity_type == 'User':
            if not self.contacts:
                self.get_contacts()
            for contact, user in self.contacts.values():
                if user.id == entity_id:
                    return user
            raise ValueError('Entity user not found {}'.format(entity_id))
        elif entity_type == 'Channel':
            raise NotImplementedError
        else:
            raise ValueError('Unkown type {}'.format(entity_type))

    def get_contacts(self):
        r = client.invoke(tl.functions.contacts.GetContactsRequest(client.api_hash))
        for contact, user in zip(r.contacts, r.users):
            self.contacts['user_{}'.format(user.id)] = contact, user

    def build_message_dict(self, msg, sender):
        msgdict = {
            'name' : utils.get_display_name(sender),
            'time' : msg.date.timestamp() * 1000,
            'message' :  msg.message,
            'filename' : '',
            'media' : '',
            'action' : '',
            'caption' : '',
        }

        if hasattr(msg, 'action'):
            msgdict['action'] = str(msg.action)
        if getattr(msg, 'media', None):
            fname = client.download_msg_media(msg)
            msgdict['media'] = get_media_type(msg.media)
            msgdict['filename'] = os.path.abspath(fname)
            msgdict['caption'] = msg.media.caption

        return msgdict

client = None
def connect():
    global client

    if TEST:
        import Test
        client = Test.TestClient()
        #raise RuntimeError('Missing API ID/HASH')
        return Test.connect_state

    # load apikey
    if not os.path.isfile('apikey'):
        if not os.path.isfile('apikey.example'):
            with open('apikey.example', 'w') as fd:
                fd.write('api_id <ID>\napi_hash <HASH>\n')
        raise RuntimeError('Missing API ID/HASH')
        return False
    else:
        with open('apikey') as fd:
            tmp = fd.readlines()
            api_id = int(tmp[0].split()[1])
            api_hash = tmp[1].split()[1]

    client = Client(
        SESSION_ID,
        api_id = api_id,
        api_hash = api_hash,
        proxy = PROXY
    )

    pyotherside.send('log', ''.join(('Telethon Client Version: ', client.__version__)))

    if DC_IP:
        client.session.server_address = DC_IP

    pyotherside.send('log', 'Connecting to Telegram servers...')
    if not client.connect():
        pyotherside.send('log', 'Initial connection failed. Retrying...')
        if not client.connect():
            pyotherside.send('log', 'Could not connect to Telegram servers.')
            return False

    if not client.is_user_authorized():
        return 'enter_number'

    client.add_update_handler(client.update_handler)

    return True

def get_entity_type(entity):

    types = (
        'User', 'UserFull', 'InputPeerUser', 'PeerUser',
        'Chat', 'ChatEmpty', 'ChatForbidden', 'ChatFull', 'PeerChat', 'InputPeerChat',
        'Channel', 'ChannelForbidden', 'InputPeerChannel', 'PeerChannel'
        'InputPeerEmpty', 'InputPeerSelf',
    )

    for t in types:
        if isinstance(entity, getattr(tl.types, t)):
            return t
    raise ValueError('unkown type: {}'.format(type(entity)))

def get_media_type(message_media):
    if type(message_media) == tl.types.MessageMediaPhoto:
        return 'photo'
    elif type(message_media) == tl.types.MessageMediaDocument:
        return 'document'
    elif type(message_media) == tl.types.MessageMediaContact:
        return 'contact'

def call(method, args):
    getattr(client, method)(*args)

def progress_callback(size, total_size):
    pyotherside.send('progress', size/total_size)
