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
import telethon

SESSION_ID = 'mercury'
LOCAL_DIR = '.local/share/harbour-mercury/'
TIMEFORMAT = '%H:%M'
PROXY = None
DC_IP = None
TEST = 0

if not os.path.isdir(LOCAL_DIR):
    os.makedirs(LOCAL_DIR)

os.chdir(LOCAL_DIR)    

class Client(telethon.TelegramClient):
    
    def __init__(self, session_user_id, api_id, api_hash, proxy=None):

        print('Initializing interactive example...')
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
        pyotherside.send('log', '{} {}'.format(type(code), code))
        try:
            success = self.sign_in(phone_number=self.phonenumber, code=code)
        # Two-step verification may be enabled
        except telethon.errors.RPCError as e:
            if e.password_required:
                return 'pass_required'
            else:
                raise
        return success

    # Two-step verification
    def send_pass(self, password):
        return self.sign_in(password=password)

    #######################
    ###  requeste data  ###
    #######################
    
    def request_contacts(self):
        self.get_contacts()
        contacts_model = []
        for contact, user in self.contacts.values():
            contactdict = {}
            contactdict['user_id'] = 'user_{}'.format(user.id)
            contactdict['name'] = telethon.utils.get_display_name(user)
            contacts_model.append(contactdict)
        pyotherside.send('contacts_list', sorted(contacts_model, key=lambda u:u['name']))

    def request_dialogs(self):
        dialogs, entities = self.get_dialogs(limit=0)
        dialogs_model = []
        
        for entity in entities:
            
            entity_type = get_entity_type(entity)
            dialogdict = {}
            dialogdict['name'] = telethon.utils.get_display_name(entity)
            dialogdict['entity_id'] = '{}_{}'.format(entity_type, entity.id)
            
            self.entities[dialogdict['entity_id']] = entity
            dialogs_model.append(dialogdict)
            
        pyotherside.send('update_dialogs', dialogs_model)
        
    def request_messages(self, ID):
        entity = self.get_entity(ID)            
        total_count, messages, senders = self.get_message_history(entity)
        
        # Iterate over all (in reverse order so the latest appear last)
        messages_model = []
        for msg, sender in zip(reversed(messages), reversed(senders)):
            msgdict = {}
            msgdict['name'] = sender.first_name if sender else '???'
            msgdict['time'] = msg.date.strftime(TIMEFORMAT)
            
            if hasattr(msg, 'action'):
                msgdict['message'] = msg.action
            elif msg.media:
                msgdict['message'] = '<media file>'
            elif msg.message:
                msgdict['message'] = msg.message
            else:
                # Unknown message, simply print its class name
                msgdict['message'] = msg.__class__.__name__
        
            messages_model.append(msgdict)
            
        pyotherside.send('update_messages', messages_model)
    
    ############################
    ###  internal functions  ###
    ############################
    
    def get_entity(self, ID):
        
        if ID in self.entities:
            return self.entities[ID]
        
        entity_type, entity_id = ID.split('_')
        if entity_type == 'Chat':
            entity = self.invoke(telethon.tl.functions.messages.GetChatsRequest([entity_id,])).chats[0]
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
        r = client.invoke(telethon.tl.functions.contacts.GetContactsRequest(client.api_hash))
        for contact, user in zip(r.contacts, r.users):
            self.contacts['user_{}'.format(user.id)] = contact, user
        
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
    
    return True

def call(method, args):
    getattr(client, method)(*args)

def get_entity_type(entity):
    
    types = (
        'User', 'UserFull',
        'Channel', 'ChannelForbidden',
        'Chat', 'ChatEmpty', 'ChatForbidden', 'ChatFull',
        'InputPeerChannel', 'InputPeerChat', 'InputPeerUser', 'InputPeerEmpty', 'InputPeerSelf',
    )
    
    for t in types:
        if isinstance(entity, getattr(telethon.tl.types, t)):
            return t
    raise ValueError('unkown type: {}'.format(type(entity)))