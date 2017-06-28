import os
import pyotherside
from telethon import tl
from . import utils

class FileManager:

    def __init__(self, client, settings):
        self.client = client
        self.settings = settings
        self.media = {}

    def get_msg_media(self, media):
        media_type = utils.get_media_type(media)
        mediadict = {}

        if media_type == 'photo':
            file_name = self.get_photo_path(media)
            media_id = media.photo.id
            mediadict['filename'] = file_name
            mediadict['downloaded'] = float(os.path.isfile(file_name))
            mediadict['caption'] = media.caption

        elif media_type == 'document':
            file_name = self.get_document_path(media)
            media_id = media.document.id
            mediadict['filename'] = file_name
            mediadict['downloaded'] = float(os.path.isfile(file_name))
            mediadict['caption'] = os.path.basename(file_name)

        elif media_type == 'webpage':
            file_name = media.webpage.url
            media_id = media.webpage.id
            mediadict['url'] = media.webpage.url
            mediadict['title'] = media.webpage.title
            mediadict['site_name'] = media.webpage.site_name

        elif media_type == 'contact':
            raise NotImplemented

        media_id = str(media_id)
        mediadict['media_id'] = media_id
        self.media[media_id] = media
        return media_type, mediadict

    def download_media(self, media_id):
        media = self.media[media_id]
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

        if file_name is None:
            file_name = document.date.strftime('doc_%Y-%m-%d_%H-%M-%S')
            file_name += utils.get_extension(message_media_document)

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
