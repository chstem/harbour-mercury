from telethon.utils import *
from telethon import tl

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
    elif type(message_media) == tl.types.MessageMediaWebPage:
        return 'webpage'
    raise TypeError('unsupported TL media type')
