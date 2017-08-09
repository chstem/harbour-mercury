import os
import shutil
import pyotherside

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

# set working directory before loading client !!!
os.chdir(LOCAL_DIR)
from .Client import Client

client = None
def connect():
    global client

    if TEST:
        from . import Test
        client = Test.TestClient()
        #raise RuntimeError('Missing API ID/HASH')
        return Test.connect_state

    # load apikey
    if os.path.isfile('apikey'):
        with open('apikey') as fd:
            tmp = fd.readlines()
            api_id = int(tmp[0].split()[1])
            api_hash = tmp[1].split()[1]
    else:
        api_id = None
        api_hash = None

    if not api_id or not api_hash:
        raise RuntimeError('Missing API ID/HASH')
        return False

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
    client.get_sender('self')   # cache self user
    client.get_updates()

    return True

def reset_session():
    os.remove('{}.session'.format(SESSION_ID))

def call(method, args):
    getattr(client, method)(*args)

def file_copy(source, target):
    if source.startswith('file://'):
        source = source[7:]
    if target.startswith('file://'):
        target = target[7:]
    shutil.copy(source, target)

def file_remove(path):
    if path.startswith('file://'):
        path = path[7:]
    os.remove(path)
