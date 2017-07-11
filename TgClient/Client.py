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

from .FileManager import FileManager
from . import database
from . import utils

class Client(TelegramClient):

    def __init__(self, session_user_id, api_id, api_hash, settings, proxy=None):
        super().__init__(session_user_id, api_id, api_hash, proxy)
        self.settings = settings
        self.filemanager = FileManager(self, settings)
        self.entities = {}
        self.contacts = {}
        #database.initialize('cache.db')
        database.initialize('{}.db'.format(session_user_id))
        #database.initialize(':memory:')

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
            contactdict['user_id'] = str(user.id)
            contactdict['name'] = utils.get_display_name(user)
            contacts_model.append(contactdict)
        pyotherside.send('contacts_list', sorted(contacts_model, key=lambda u:u['name']))

    def request_dialogs(self):
        dialogs, entities = self.get_dialogs(limit=0)
        dialogs_model = []
        download_queue = []

        for entity in entities:
            entity_type = utils.get_entity_type(entity)
            if 'Forbidden' in entity_type:
                # no access, do not add to dialogs_model
                continue
            dialogdict = {}
            filename = self.filemanager.get_dialog_photo(entity)
            dialogdict['name'] = utils.get_display_name(entity)
            dialogdict['icon'] = filename
            dialogdict['entity_id'] = str(entity.id)

            # store
            self.entities[entity.id] = entity
            database.add_dialog(entity)

            if filename:
                if not os.path.isfile(filename) or not os.path.getsize(filename):
                    # queue for download and send preliminary empty icon
                    download_queue.append((entity, filename))
                    dialogdict['icon'] = ''

            dialogs_model.append(dialogdict)

        pyotherside.send('update_dialogs', dialogs_model)

        # start downloads
        for chat, filename in download_queue:
            self.filemanager.download_dialog_photo(chat, filename)
        pyotherside.send('log', 'all chat icons downloaded')

    def request_messages(self, ID):
        entity = self.get_entity(ID)

        # get last message from database
        last_message = database.get_message_history(ID, limit=1)

        if not last_message:
            last_id = 0
            limit = 20
        else:
            last_id = last_message[0][0].id + 1
            limit = 0

        # check for newer messages from server
        result = self(tl.functions.messages.GetHistoryRequest(
            utils.get_input_peer(entity),
            limit=limit,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=last_id,
            add_offset=0,
        ))

        # get sender (User) for each message
        senders = [utils.find_user_or_chat(m.from_id, result.users, result.chats)
                    if m.from_id is not None else
                    utils.find_user_or_chat(m.to_id, result.users, result.chats)
                    for m in result.messages]
        messages = zip(result.messages, senders)

        # add to cache
        database.add_messages(entity.id, messages)

        # collect latest messages from database
        messages = database.get_message_history(ID, limit=20)
        messages = reversed(messages)
        messages_model = [self.build_message_dict(msg, sender) for msg, sender in messages]

        pyotherside.send('update_messages', messages_model)

    def download(self, media_id):
        self.filemanager.download_media(media_id)

    ########################
    ###  update handler  ###
    ########################

    def update_handler(self, update_object):

        if isinstance(update_object, tl.types.UpdatesTg):

            # check for new chat messages
            for update in update_object.updates:
                if isinstance(update, tl.types.UpdateNewMessage):
                    from_id = update.message.from_id
                    to_entity = update.message.to_id
                    entity_type = utils.get_entity_type(to_entity)
                    if 'User' in entity_type:
                        entity_id = update.message.from_id
                    elif 'Chat' in entity_type:
                        entity_id = update.message.to_id.chat_id
                    msgdict = self.build_message_dict(update.message, self.get_entity(from_id))
                    pyotherside.send('new_message', entity_id, msgdict)

                elif isinstance(update, tl.types.UpdateNewChannelMessage):
                    entity_id = update.message.to_id.channel_id
                    msgdict = self.build_message_dict(update.message, self.get_entity(entity_id))
                    pyotherside.send('new_message', entity_id, msgdict)

                elif isinstance(update, tl.types.UpdateReadHistoryOutbox) or \
                        isinstance(update, tl.types.UpdateReadHistoryInbox) or \
                        isinstance(update, tl.types.UpdateReadChannelInbox):
                    self.request_dialogs()

        elif isinstance(update_object, tl.types.UpdateShortChatMessage):
            # Group
            entity_id = update_object.chat_id
            msgdict = self.build_message_dict(update_object, self.get_entity(entity_id))
            pyotherside.send('new_message', entity_id, msgdict)

    ############################
    ###  internal functions  ###
    ############################

    def get_entity(self, entity_id):
        entity_id = int(entity_id)
        if entity_id in self.entities:
            return self.entities[entity_id]
        raise ValueError('Entity not found: {}'.format(entity_id))

    def get_contacts(self):
        r = self.invoke(tl.functions.contacts.GetContactsRequest(self.api_hash))
        for contact, user in zip(r.contacts, r.users):
            self.contacts[user.id] = contact, user

    def build_message_dict(self, msg, sender):
        mdata = {
            'name' : utils.get_display_name(sender),
            'time' : msg.date.timestamp() * 1000,
            'downloaded' : 0.0,
        }
        msgdict = {
            'type' : '',
            'mdata' : mdata,
            }

        if hasattr(msg, 'action'):
            msgdict['type'] = 'action'
            msgdict['mdata']['action'] = str(msg.action)

        elif getattr(msg, 'media', False):

            media_type, media = self.build_media_dict(msg.media)
            if media_type == 'webpageempty':
                msgdict['type'] = 'message'
                msgdict['mdata']['message'] = msg.message
            else:
                msgdict['type'] = media_type
                msgdict['mdata'].update(media)

        else:
            msgdict['type'] = 'message'
            msgdict['mdata']['message'] = msg.message

        return msgdict

    def build_media_dict(self, media):
        media_type = utils.get_media_type(media)
        mediadict = {}

        if media_type == 'photo':
            file_name, downloaded = self.filemanager.get_msg_media(media)
            media_id = media.photo.id
            mediadict['filename'] = file_name
            mediadict['downloaded'] = downloaded
            mediadict['caption'] = media.caption

        elif media_type == 'document':
            file_name, downloaded = self.filemanager.get_msg_media(media)
            media_id = media.document.id
            mediadict['filename'] = file_name
            mediadict['downloaded'] = downloaded
            mediadict['caption'] = os.path.basename(file_name)

        elif media_type == 'webpage':
            media_id = media.webpage.id
            if isinstance(media.webpage, tl.types.WebPageEmpty):
                media_type = 'webpageempty'
            else:
                file_name = media.webpage.url
                mediadict['url'] = media.webpage.url
                mediadict['title'] = media.webpage.title
                mediadict['site_name'] = media.webpage.site_name

        elif media_type == 'contact':
            raise NotImplemented

        mediadict['media_id'] = str(media_id)
        return media_type, mediadict
