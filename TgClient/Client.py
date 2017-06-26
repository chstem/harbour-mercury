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
from . import utils

from .FileManager import FileManager

class Client(TelegramClient):

    def __init__(self, session_user_id, api_id, api_hash, settings, proxy=None):
        super().__init__(session_user_id, api_id, api_hash, proxy)
        self.settings = settings
        self.filemanager = FileManager(self, settings)
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
            entity_type = utils.get_entity_type(entity)
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
                    from_id = 'User_{}'.format(update.message.from_id)
                    to_entity = update.message.to_id
                    entity_type = utils.get_entity_type(to_entity)
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
        r = self.invoke(tl.functions.contacts.GetContactsRequest(self.api_hash))
        for contact, user in zip(r.contacts, r.users):
            self.contacts['user_{}'.format(user.id)] = contact, user

    def build_message_dict(self, msg, sender):
        msgdict = {
            'name' : utils.get_display_name(sender),
            'time' : msg.date.timestamp() * 1000,
            'message' : '',
            'media' : '',
            'media_data' : None,
            'action' : '',
        }

        if hasattr(msg, 'action'):
            msgdict['action'] = str(msg.action)
        else:
            msgdict['message'] = msg.message

        if getattr(msg, 'media', None):
            msgdict['media_data'] = self.filemanager.get_msg_media(msg.media)
            msgdict['media'] = msgdict['media_data']['type']

        return msgdict
