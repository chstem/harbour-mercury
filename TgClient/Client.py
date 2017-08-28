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

from datetime import datetime
import os
import pyotherside
from telethon import *
import time

from .FileManager import FileManager
from . import database
from . import utils

class Client():

    __version__ = '0.1'

    def __init__(self, session_user_id, api_id, api_hash, settings, proxy=None):
        self.client = TelegramClient(session_user_id, api_id, api_hash, proxy)
        self.connected = False
        self.settings = settings
        self.filemanager = FileManager(self.client, settings)
        self.contacts = {}
        self.user = None
        database.initialize('cache.db')
        #database.initialize('{}.db'.format(session_user_id))
        #database.initialize(':memory:')

    def reconnect(self, new_dc=None):
        try:
            self.client.reconnect(new_dc)
            self.connected = True
        except OSError:
            return False
        pyotherside.send('connection', True)
        if not self.client._update_handlers:
            self.client.add_update_handler(self.update_handler)
        try:
            self.client._set_updates_thread(running=True)
        except RuntimeError:
            # still running
            pass
        self.get_updates()
        return True

    def invoke(self, request, updates=None):
        if not self.connected:
            if not self.reconnect():
                return False
        try:
            return self.client.invoke(request, updates)
        except (TimeoutError, ConnectionError):
            self.connected = False
            pyotherside.send('connection', False)
            pyotherside.send('log', 'Connection lost, try reconnecting ...')
            if self.reconnect():
                return self.client.invoke(request, updates)
        return False

    ###############
    ###  login  ###
    ###############

    # login code
    def request_code(self, phonenumber=None):
        if phonenumber:
            self.phonenumber = phonenumber
        self.client.send_code_request(self.phonenumber)

    def send_code(self, code):
        try:
            status = self.client.sign_in(phone_number=self.phonenumber, code=code)
        # Two-step verification may be enabled
        except errors.SessionPasswordNeededError:
            return 'pass_required'
        if not status:
            return 'invalid'
        if isinstance(status, tl.types.User):
            self.user = status
            database.add_sender(self.user)
            return True
        raise ValueError('Unkown return status for sign_in')

    # Two-step verification
    def send_pass(self, password):
        status = self.client.sign_in(password=password)
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
        if self.connected:
            dialogs, entities = self.client.get_dialogs(limit=0)
        elif self.reconnect():
            dialogs, entities = self.client.get_dialogs(limit=0)
        else:
            entities = database.get_dialogs()

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
            database.add_dialog(entity)

            if filename:
                if not os.path.isfile(filename) or not os.path.getsize(filename):
                    # queue for download and send preliminary empty icon
                    download_queue.append((entity, filename))
                    dialogdict['icon'] = ''

            dialogs_model.append(dialogdict)

        pyotherside.send('update_dialogs', dialogs_model)

        if self.connected:
            # download icons
            for chat, filename in download_queue:
                pyotherside.send('log', 'start icon download: {}'.format(filename))
                t = time.time()
                self.filemanager.download_dialog_photo(chat, filename)
                pyotherside.send('log', 'finished icon download: {}, {:.2f} sec'.format(filename, time.time()-t))

    def request_messages(self, entity_id, last_id=0, count=20):
        entity = self.get_entity(int(entity_id))
        last_id = int(last_id)

        if not last_id:
            # initial loading
            # check for older messages (if less than <count> cached)
            if database.messages_count(entity_id) < count:
                first_message_id = database.get_first_message(entity_id)
                self.download_messages(entity, limit=count, offset_id=first_message_id)

            # check for newer messages than chached
            # get last message from database
            last_message_id = database.get_last_message(entity_id)
            if not last_message_id:
                # nothing cached yet
                self.download_messages(entity, limit=count, min_id=last_id)
            else:
                # load everything missing
                self.download_messages(entity, limit=0, min_id=last_message_id+1)

            # collect latest messages from cache
            messages = database.get_message_history(entity_id, limit=count)

        else:
            # load older messages
            # check oldest messages in cache
            first_message_id = database.get_first_message(entity_id)

            # load even older messages from server
            if first_message_id >= last_id:
                self.download_messages(entity, limit=count, offset_id=first_message_id)

            # collect requested messages from cache
            messages = database.get_message_history(entity_id, limit=count, max_id=last_id-1)

        messages_model = [self.build_message_dict(msg, sender) for msg, sender in messages]
        pyotherside.send('new_messages', entity_id, messages_model)

    def download(self, media_id):
        self.filemanager.download_media(media_id)

    def get_updates(self):
        """get updates since last saved state"""
        pts = database.get_meta('pts')
        state = self.invoke(tl.functions.updates.GetStateRequest())
        if not state:
            return
        if pts is None:
            # initialize with current state
            database.set_meta(pts=state.pts, date=state.date.timestamp())
            return
        date = datetime.fromtimestamp(database.get_meta('date'))
        pyotherside.send('log', 'requesting updates, last state: {}, {}'.format(pts, date.timestamp()))

        while pts < state.pts:
            updates = self.invoke(tl.functions.updates.GetDifferenceRequest(pts=pts, date=date, qts=0))
            if not updates:
                return

            # get sender (User) for each message
            senders = [utils.find_user_or_chat(m.from_id, updates.users, updates.chats)
                        if m.from_id is not None else
                        utils.find_user_or_chat(m.to_id, updates.users, updates.chats)
                        for m in updates.new_messages]

            for message, sender in zip(updates.new_messages, senders):
                from_id = message.from_id
                entity_type = utils.get_entity_type(message.to_id)
                if 'User' in entity_type:
                    if message.out:
                        entity_id = message.to_id.user_id
                    else:
                        entity_id = message.from_id
                elif 'Chat' in entity_type:
                    entity_id = message.to_id.chat_id
                try:
                    database.add_messages(entity_id, [(message, sender),])
                except ValueError:
                    continue

            for message in updates.new_encrypted_messages:
                pass

            for update in updates.other_updates:
                self.handle_update(update, send=False, users=updates.users, chats=updates.chats)

            if isinstance(updates, tl.types.updates.DifferenceSlice):
                pts = updates.intermediate_state.pts
                database.set_meta(pts=pts, date=updates.intermediate_state.date.timestamp())
            else:
                database.set_meta(pts=updates.state.pts, date=updates.state.date.timestamp())
                break

    ########################
    ###  update handler  ###
    ########################

    def update_handler(self, update_object):
        """this function gets passed to client.add_update_handler()"""
        if isinstance(update_object, tl.types.UpdatesTg):
            for update in update_object.updates:
                self.handle_update(update, users=update_object.users, chats=update_object.chats)
            pts = max([getattr(u, 'pts', 0) for u in update_object.updates if not isinstance(u, tl.types.UpdateNewChannelMessage)], default=None)
        else:
            self.handle_update(update_object)
            pts = getattr(update_object, 'pts', None)
        date = getattr(update_object, 'date', None)
        if pts:
            database.set_meta(pts=pts)
        if date:
            database.set_meta(date=date.timestamp())

    def handle_update(self, update_object, send=True, users=[], chats=[]):
        """update cache with update_object and optionally update QML model"""

        if isinstance(update_object, tl.types.UpdateNewMessage):
            from_id = update_object.message.from_id
            to_entity = update_object.message.to_id
            entity_type = utils.get_entity_type(to_entity)
            if 'User' in entity_type:
                entity_id = update_object.message.from_id
            elif 'Chat' in entity_type:
                entity_id = update_object.message.to_id.chat_id
            sender = utils.find_user_or_chat(from_id, users, chats)
            try:
                database.add_messages(entity_id, [(update_object.message, sender),])
            except database.DialogDoesNotExist:
                # add dialog entity and try again
                dialog = utils.find_user_or_chat(entity_id, users, chats)
                database.add_dialog(dialog)
                database.add_messages(entity_id, [(update_object.message, sender),])
            if send:
                msgdict = self.build_message_dict(update_object.message, sender)
                pyotherside.send('new_messages', str(entity_id), [msgdict,])

        elif isinstance(update_object, tl.types.UpdateNewChannelMessage):
            entity_id = update_object.message.to_id.channel_id
            sender = utils.find_user_or_chat(update_object.message.from_id, users, chats)
            try:
                database.add_messages(entity_id, [(update_object.message, sender),])
            except database.DialogDoesNotExist:
                # add channel entity (=sender) and try again
                database.add_dialog(sender)
                database.add_messages(entity_id, [(update_object.message, sender),])
            if send:
                msgdict = self.build_message_dict(update_object.message, sender)
                pyotherside.send('new_messages', str(entity_id), [msgdict,])

        elif isinstance(update_object, tl.types.UpdateEditMessage):
            try:
                database.update_message(update_object.message)
            except ValueError:
                # not yet cached
                return
            if send:
                sender = database.get_message_sender(update_object.message.id)
                msgdict = self.build_message_dict(update_object.message, sender)
                pyotherside.send('update_message', msgdict)

        elif isinstance(update_object, tl.types.UpdateMessageID):
            m = self.invoke(tl.functions.messages.GetMessagesRequest(id=[update_object.id,]))
            if not m:
                return
            database.update_message(m.messages[0])
            if send:
                sender = database.get_message_sender(message.id)
                msgdict = self.build_message_dict(message, sender)
                pyotherside.send('new_messages', str(entity_id), [msgdict,])

        elif isinstance(update_object, tl.types.UpdateDeleteMessages):
            database.delete_messages(update_object.messages)
            if send:
                pyotherside.send('delete_messages', map(str, update_object.messages))

        elif isinstance(update_object, tl.types.UpdateReadHistoryOutbox) or \
                isinstance(update_object, tl.types.UpdateReadHistoryInbox) or \
                isinstance(update_object, tl.types.UpdateReadChannelInbox):
            if send:
                self.request_dialogs()

        elif isinstance(update_object, tl.types.UpdateShortMessage):
            # User
            entity_id = update_object.user_id
            if update_object.out:
                sender = self.get_sender('self')
            else:
                sender = self.get_sender(entity_id)
            if not sender:
                # not cached yet
                return
            database.add_messages(entity_id, [(update_object, sender),])
            if send:
                msgdict = self.build_message_dict(update_object, sender)
                pyotherside.send('new_messages', str(entity_id), [msgdict,])

        elif isinstance(update_object, tl.types.UpdateShortChatMessage):
            # Chat (Group/Channel)
            entity_id = update_object.chat_id
            sender = self.get_sender(update_object.from_id)
            if not sender:
                # not cached yet
                fullchat = self.invoke(tl.functions.messages.GetFullChatRequest(chat_id=entity_id))
                if not fullchat:
                    return
                sender = utils.find_user_or_chat(update_object.from_id, fullchat.users, [])
            try:
                database.add_messages(entity_id, [(update_object, sender),])
            except database.DialogDoesNotExist:
                # add dialog entity and try again
                dialog = utils.find_user_or_chat(entity_id, users, chats)
                database.add_dialog(dialog)
                database.add_messages(entity_id, [(update_object, sender),])
            if send:
                msgdict = self.build_message_dict(update_object, sender)
                pyotherside.send('new_messages', str(entity_id), [msgdict,])

    ############################
    ###  internal functions  ###
    ############################

    def get_entity(self, entity_id):
        entity = database.get_dialog(entity_id)
        if not entity:
            r = self.invoke(tl.functions.messages.GetChatsRequest(id=[entity_id,]))
            if not r:
                return
            entity = r.chats[0]
        return entity

    def get_sender(self, sender_id):
        if sender_id == 'self':
            if not self.user:
                self.user = database.get_self()
            if not self.user:
                inputuser = tl.types.InputUserSelf()
                r = self.invoke(tl.functions.users.GetUsersRequest((inputuser,)))
                if not r:
                    return
                self.user = r[0]
                database.add_sender(self.user)
                database.set_meta(self_id=self.user.id)
            return self.user
        sender = database.get_sender(sender_id)
        if not sender:
            pyotherside.send('log', 'Sender {} not found'.format(sender_id))
        return sender

    def get_contacts(self):
        r = self.invoke(tl.functions.contacts.GetContactsRequest(self.api_hash))
        if not r:
            return
        for contact, user in zip(r.contacts, r.users):
            self.contacts[user.id] = contact, user

    def download_messages(self, entity, limit=20, offset_id=0, max_id=0, min_id=0):
        """download messages from Telegram server"""
        while 1:
            result = self.invoke(tl.functions.messages.GetHistoryRequest(
                utils.get_input_peer(entity),
                limit=limit,
                offset_date=None,
                offset_id=offset_id,
                max_id=max_id,
                min_id=min_id,
                add_offset=0,
            ))

            if not result:
                return

            # get sender (User) for each message
            senders = [utils.find_user_or_chat(m.from_id, result.users, result.chats)
                        if m.from_id is not None else
                        utils.find_user_or_chat(m.to_id, result.users, result.chats)
                        for m in result.messages]
            messages = zip(result.messages, senders)

            # add to cache
            database.add_messages(entity.id, messages)

            # check exit conditions
            if limit or len(result.messages) == 0:
                break
            else:
                # continue to check for more chunks
                offset_id = result.messages[-1].id

    def build_message_dict(self, msg, sender):
        mdata = {
            'name' : utils.get_display_name(sender),
            'time' : msg.date.timestamp() * 1000,
            'downloaded' : 0.0,
        }
        msgdict = {
            'id' : str(msg.id),
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
