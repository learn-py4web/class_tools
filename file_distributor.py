# Copyright Luca de Alfaro, 2019.
# BSD License.

import io
import os
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

class FileDistributor(object):

    def __init__(self, drive_service, share_folder_id):
        """Initializes a file distributor."""
        self.drive_service = drive_service
        self.share_folder_id = share_folder_id

    def _distribute_media(self, email, media, file_name, mode='reader', update=False):
        """Distributes media to the student.
        @:param email: email of the user.
        @:param media: Google media object for upload.
        @:param file_name: file name to use in drive.
        @:param mode: mode with which to distribute the file.  It
        can be one of 'reader', 'writer', 'commenter'.
        @:param update: if True, check if a file by the same name exists,
        and if so, updates the feedback.
        """
        assert mode in ['reader', 'writer', 'commenter']
        # Uploads the file.
        file_meta = {'name': file_name, 'parents': [self.share_folder_id]}
        # do_create keeps track of whether we need to create the file.
        do_create = not update
        if update:
            # Checks if a file by the same name exists.
            existing_file_ids = []
            q = "'%s' in parents" % self.share_folder_id
            q += " and name = '%s'" % file_name
            page_token = None
            while True:
                response = self.drive_service.files().list(
                    q=q,
                    spaces='drive',
                    fields='nextPageToken, files(id, name)',
                    pageToken=page_token).execute()
                for file in response.get('files', []):
                    existing_file_ids.append(file.get('id'))
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
            if len(existing_file_ids) == 0:
                # We need to create.
                do_create = True
            else:
                # We can perform the update.
                # We update all files we find, because we could have old copies.
                for file_id in existing_file_ids:
                    self.drive_service.files().update(
                        fileId=file_id,
                        media_body=media
                    ).execute()
        if do_create:
            # The new file is created.
            upfile = self.drive_service.files().create(
                body=file_meta,
                media_body=media,
                fields='id').execute()
            file_id = upfile.get('id')
            # Shares the file
            user_permission = {
                'type': 'user',
                'role': mode,
                'emailAddress': email
            }
            self.drive_service.permissions().create(
                fileId=file_id,
                body=user_permission,
                fields='id',
                sendNotificationEmail=False, # otherwise, Google throttles us
            ).execute()


    def distribute_file(self, email, file_path, file_name, mime,
                        mode='reader', update=True):
        """Distributes a file to a user.
        @:param email: email of the user.
        @:param file_path: path to file to distribute
        @:param file_name: file name to use in drive.
        @:param mime: mime type of file to be distributed
        @:param mode: mode with which to distribute the file.  It
        can be one of 'reader', 'writer', 'commenter'.
        @:param update: if True, check if a file by the same name exists,
        and if so, updates the feedback.
        See https://developers.google.com/drive/api/v3/reference/permissions/create
        """
        media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
        self._distribute_media(email, media, file_name, mode, update=update)
        print("Distributed %s to %s" % (file_name, email))


    def distribute_bytes(self, email, content_bytes, file_name,
                         mime='text/html', mode='reader', update=True):
        """Distributes bytes to the user.
        @:param email: email of the user.
        @:param text: the text to distribute
        @:param file_name: file name to use in drive.
        @:param mime: mime type of file to be distributed.
        Can also be 'text/html', etc.
        @:param mode: mode with which to distribute the file.  It
        can be one of 'reader', 'writer', 'commenter'.
        @:param update: if True, check if a file by the same name exists,
        and if so, updates the feedback.
        """
        buffer = io.BytesIO()
        buffer.write(content_bytes)
        media = MediaIoBaseUpload(buffer, mime, resumable=True)
        self._distribute_media(email, media, file_name, mode, update=update)
        buffer.close()
        print("Distributed %s to %s" % (file_name, email))


# The following is for testing.
if __name__ == '__main__':
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    drive_service = build('drive', 'v3', credentials=creds)

    fd = FileDistributor(drive_service, 'my_class', 'some_id')
    fd.distribute_bytes('luca@ucsc.edu',
                        'Ciao sono io. \n\n Luca'.encode('utf-8'),
                        'be_happy.txt', 'text/plain')
