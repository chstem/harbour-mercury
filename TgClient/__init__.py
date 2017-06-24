import os
import pyotherside
from .Client import Client

SESSION_ID = 'mercury'
LOCAL_DIR = '/home/nemo/.local/share/harbour-mercury/'
FILE_CACHE = os.path.abspath(os.path.join(LOCAL_DIR, 'files'))
PROXY = None
DC_IP = None
TEST = 0

settings = {
    'FILE_CACHE' : FILE_CACHE,
    'DOWNLOAD_PREFER_SMALL' : False,       # prefered photo size for download
}

if not os.path.isdir(LOCAL_DIR):
    os.makedirs(LOCAL_DIR)
if not os.path.isdir(FILE_CACHE):
    os.makedirs(FILE_CACHE)

os.chdir(LOCAL_DIR)

client = None
def connect():
    global client

    if TEST:
        from . import Test
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
        settings = settings,
        proxy = PROXY,
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

def call(method, args):
    getattr(client, method)(*args)
