# Copyright Luca de Alfaro, 2019.
# BSD License.

import argparse
import io
import os
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def hsize(size):
    """Reutrns a human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"


def sanitize(s):
    """Sanitizes a string for printing."""
    s = s.encode('ascii', 'replace').decode()
    s = s.replace('\n', ' ')
    return s


def list_dir(dir_id, path, depth, args):
    """List the contents of a directory dir_id, returning the total 
    size of the files in there."""
    depth += 1
    # Creates a query. 
    q = f"'{dir_id}' in parents"
    page_token = None
    total_size = 0
    while True:
        response = drive_service.files().list(
            q=q,
            spaces='drive',
            fields='nextPageToken, files(id, name, size, mimeType)',
            pageToken=page_token).execute()
        for file in response.get('files', []):
            if file.get('mimeType') == 'application/vnd.google-apps.folder':
                if depth is not None and depth >= args.depth:
                    continue
                t = list_dir(file.get('id'), path + file.get('name', '') + "/", depth, args)
                total_size += t
                if args.all and t > 0:
                    print(f"{hsize(t)} \t{path}{sanitize(file.get('name'))}")
            else:
                total_size += int(file.get('size', 0))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return total_size


def main(args):
    list_dir(args.dir_id, "", 0, args)
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--depth', type=int, default=1,
                        help="Depth limit for recursion.")
    parser.add_argument('-a', '--all', action='store_true',
                        help="List all directory sizes.")
    parser.add_argument('dir_id', default=None,)
    args = parser.parse_args()
    if args.dir_id is None: 
        raise ValueError("Please provide a directory id.")
    # Auth code. 
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
    main(args)
    
