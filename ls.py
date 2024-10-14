# Copyright Luca de Alfaro, 2019.
# BSD License.

"""
Usage: 

python ls.py <dir_id> [-d <depth>] [-a]

-d: maximum depth at which to inspect directories.  Default is 1.
-a: list all directories, not just the top one. 

To use this script, you need to create credentials for Google Drive.
Here is how to proceed: 

To create a Google credentials JSON file for accessing Google Drive, navigate to the Google Cloud Console, go to "APIs & Services" > "Credentials", then create a new "Service Account" and select "JSON" as the key type to download a JSON file containing your access credentials; this file is typically named "credentials.json" and should be stored securely as it contains your private key information. [1, 2, 3, 4, 5]

Key steps:
* Access Google Cloud Console: Open the Google Cloud Platform console and select your project. [1, 2, 3]
* Go to Credentials page: Navigate to "APIs & Services" > "Credentials". [1, 2, 3]
* Create a Service Account: Click "Create Credentials" and select "Service account". [1, 2, 3]
* Name your Service Account: Provide a name for your service account. [1, 2, 4]
* Add a Key: Select "Add Key" > "Create new key". [1, 2, 3]
* Choose JSON format: Set the "Key type" to "JSON" and click "Create". [1, 2, 3]
* Download the JSON file: A JSON file containing your credentials will be downloaded to your computer.  Name it `credentials.json` . [1, 2, 3]

References:
* [1] https://developers.google.com/workspace/guides/create-credentials
* [2] https://support.google.com/a/answer/7378726?hl=en
* [3] https://support.google.com/cloud/answer/6158849?hl=en
* [4] https://cloud.google.com/docs/authentication/provide-credentials-adc
* [5] https://cloud.google.com/iam/docs/keys-create-delete
"""

import argparse
import io
import os
import pickle
import re

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
    q = f"'{dir_id}' in parents" if dir_id != "root" else "'root' in parents"
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
                if depth is not None and depth > args.depth:
                    continue
                t = list_dir(file.get('id'), path + file.get('name', '') + "/", depth, args)
                total_size += t
                if t > 0 and (args.all or depth <= 1):
                    print(f"{hsize(t)} \t{path}{sanitize(file.get('name'))}")
            else:
                total_size += int(file.get('size', 0))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return total_size


def main(args):
    t = list_dir(args.dir_id, "", 0, args)
    filename = drive_service.files().get(fileId=args.dir_id).execute().get('name')
    print(f"Total size of {filename}: {hsize(t)}")

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--depth', type=int, default=1,
                        help="Depth limit for recursion.")
    parser.add_argument('-a', '--all', action='store_true',
                        help="List all directory sizes.")
    parser.add_argument('dir_id', default="root",)
    args = parser.parse_args()
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
    
