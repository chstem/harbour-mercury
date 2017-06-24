import os
from telethon import tl
from . import utils

class FileManager:

    def __init__(self, client, settings):
        self.client = client
        self.settings = settings

    def download_msg_media(self, message):
        t = utils.get_media_type(message.media)
        if t == 'photo':
            return self.download_photo(message)
        if t == 'document':
            return self.download_document(message)
        if t == 'contact':
            return self.download_contact(message)

    def download_photo(self, message):

        # Determine the photo and its largest size
        if self.settings['DOWNLOAD_PREFER_SMALL']:
            size = message.media.photo.sizes[0]
        else:
            size = message.media.photo.sizes[-1]
        file_size = size.size

        filename = message.media.photo.date.strftime('photo_%Y-%m-%d_%H-%M-%S')
        filename += utils.get_extension(message.media)
        from_id = message.from_id
        file_path = os.path.join(self.settings['FILE_CACHE'], str(from_id))

        if not os.path.isdir(file_path):
            os.makedirs(file_path)

        file_path = os.path.join(file_path, filename)

        if not os.path.isfile(file_path):
            self.client.download_file(
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
        file_path = os.path.join(self.settings['FILE_CACHE'], str(from_id))

        if not os.path.isdir(file_path):
            os.makedirs(file_path)

        file_path = os.path.join(file_path, filename)

        if not os.path.isfile(file_path):
            self.client.download_file(
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

    @staticmethod
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
        file_path = os.path.join(self.settings['FILE_CACHE'], filename)

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
