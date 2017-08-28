import os
import pyotherside
import threading

from telethon import tl
from . import utils

class FileManager:

    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.media = {}

    def get_msg_media(self, media):
        media_type = utils.get_media_type(media)

        if media_type == 'photo':
            file_name = self.get_photo_path(media)
            self.media[media.photo.id] = media

        elif media_type == 'document':
            file_name = self.get_document_path(media)
            self.media[media.document.id] = media

        elif media_type == 'contact':
            raise NotImplemented

        downloaded = float(os.path.isfile(file_name))
        return file_name, downloaded

    def get_dialog_photo(self, chat):
        if not chat.photo or type(chat.photo) == tl.types.ChatPhotoEmpty:
            return ''
        if type(chat.photo) == tl.types.ChatPhoto:
            filename = os.path.join(self.settings['FILE_CACHE'], 'chats', str(chat.id))
        elif type(chat.photo) == tl.types.UserProfilePhoto:
            filename = os.path.join(self.settings['FILE_CACHE'], 'users', str(chat.id))
        else:
            pyotherside.send('log', 'Photo type unkown: {} id: {}'.format(type(chat.photo), chat.id))
            raise TypeError('Invalid Photo Type')

        filename += utils.get_extension(chat.photo)

        #if not os.path.isfile(filename) or not os.path.getsize(filename):
            ## initialize download and send preliminary empty return value
            #thread = threading.Thread(target=self.download_dialog_photo, args=(chat, filename))
            #thread.start()
            #return ''

        return filename

    def download_dialog_photo(self, chat, filename):

        # choose size
        if self.settings['DOWNLOAD_PREFER_SMALL']:
            photo = chat.photo.photo_small
        else:
            photo = chat.photo.photo_big

        # check Data Center
        if photo.dc_id != utils.get_dc(self.client):
            client = self.client._get_exported_client(photo.dc_id)
        else:
            client = self.client

        # download file
        client.download_file(
            tl.types.InputFileLocation(
                volume_id = photo.volume_id,
                local_id = photo.local_id,
                secret = photo.secret,
            ),
            filename,
        )

        entity_id = str(chat.id)
        pyotherside.send('icon', entity_id, filename)

    def download_media(self, media_id):
        media = self.media[int(media_id)]
        media_type = utils.get_media_type(media)
        if media_type == 'photo':
            file_name = self.get_photo_path(media)
            self.download_photo(media, file_name)
        if media_type == 'document':
            file_name = self.get_document_path(media)
            self.download_document(media, file_name)
        if media_type == 'contact':
            self.download_contact(media)

    def get_photo_path(self, media):
        file_name = media.photo.date.strftime('photo_%Y-%m-%d_%H-%M-%S')
        file_name += utils.get_extension(media)
        photo_id = media.photo.id
        return os.path.join(self.settings['FILE_CACHE'], str(photo_id), file_name)

    def get_document_path(self, media):

        for attr in media.document.attributes:
            if type(attr) == tl.types.DocumentAttributeFilename:
                file_name = attr.file_name
                break  # This attribute has higher priority
            elif type(attr) == tl.types.DocumentAttributeAudio:
                file_name = '{}_{}'.format(attr.performer, attr.title)
            elif type(attr) == tl.types.DocumentAttributeVideo:
                file_name = media.document.date.strftime('video_%Y-%m-%d_%H-%M-%S')

        if file_name is None:
            file_name = document.date.strftime('doc_%Y-%m-%d_%H-%M-%S')
            file_name += utils.get_extension(media)

        doc_id = media.document.id

        return os.path.join(self.settings['FILE_CACHE'], str(doc_id), file_name)

    def download_photo(self, media, file_path):

        # choose size
        if self.settings['DOWNLOAD_PREFER_SMALL']:
            size = media.photo.sizes[0]
        else:
            size = media.photo.sizes[-1]

        dirname = os.path.dirname(file_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        self.client.download_file(
            tl.types.InputFileLocation(
                volume_id = size.location.volume_id,
                local_id = size.location.local_id,
                secret = size.location.secret,
            ),
            file_path,
            file_size = size.size,
            progress_callback = progress_callback(media.photo.id),
        )

    def download_document(self, media, file_path):

        dirname = os.path.dirname(file_path)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        self.client.download_file(
            tl.types.InputDocumentFileLocation(
                id = media.document.id,
                access_hash = media.document.access_hash,
                version = media.document.version,
            ),
            file_path,
            file_size = media.document.size,
            progress_callback = progress_callback(media.document.id),
        )

    @staticmethod
    def download_contact(media):
        """Downloads a media contact using the vCard 4.0 format"""

        first_name = media.first_name
        last_name = media.last_name
        phone_number = media.phone_number

        if last_name and first_name:
            file_name = '{} {}'.format(first_name, last_name)
        elif first_name:
            file_name = first_name
        else:
            file_name = last_name
        file_name += '.vcard'
        file_path = os.path.join(self.settings['FILE_CACHE'], file_name)

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

def progress_callback(media_id):
    def progress(size, total_size):
        pyotherside.send('progress', str(media_id), size/total_size)
    return progress
