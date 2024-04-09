# Copyright Luca de Alfaro, 2019
# BSD License

import argparse
import csv
import os
import pickle
import shutil
import zipfile

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly']
# https://www.googleapis.com/auth/spreadsheets for r/w
#


def main(args):
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

    sheet_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Call the Sheets API
    range_name = args.sheet + '!' + args.email_column + '2:' + args.file_column
    sheet = sheet_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=args.spreadsheet_id,
                                range=range_name).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return

    # Now downloads all the submissions.
    student_submissions = {row[0]: row[-1] for row in values}
    bad_files = []
    for email, url in student_submissions.items():
        if args.test:
            print(email, url)
            continue
        docid = url.split("=")[-1]
        student_dir = os.path.join(args.destination_dir, email)
        download_fn = os.path.join(args.destination_dir, email + '.' + args.extension)
        # Creates the directory if necessary.
        if not os.path.exists(args.destination_dir):
            os.makedirs(args.destination_dir)
        # Removes previous files.
        if os.path.exists(download_fn):
            os.unlink(download_fn)
        if os.path.exists(student_dir):
            shutil.rmtree(student_dir)
        with open(download_fn, 'wb') as f:
            request = drive_service.files().get_media(fileId=docid)
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %s to %s : %d%%." % (email, download_fn, int(status.progress() * 100)))
        if not args.no_unzip: 
            try:
                if args.extension == 'zip':
                    with zipfile.ZipFile(download_fn, 'r') as zip_ref:
                        extraction_dir = os.path.join(args.destination_dir, email)
                        zip_ref.extractall(extraction_dir)
                    os.remove(download_fn)
            except Exception as e:
                bad_files.append(email)
                print(f"Error unzipping {download_fn}: {e}")
                os.unlink(download_fn)
    # Finally, writes the csv file with all the students who have submitted,
    # so their work can be included.
    csv_fn = os.path.join(args.destination_dir, 'students.csv')
    with open(csv_fn, 'w', newline='') as csvfile:
        fieldnames=['email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for email in student_submissions.keys():
            writer.writerow({'email': email})
    if bad_files:
        print(f"Errors in unzipping files for {", ".join(bad_files)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--spreadsheet_id', default=None,
                        help="ID of the spreadsheet to use as base of download.")
    parser.add_argument('-m', '--email_column', default='B',
                        help='Column containing email')
    parser.add_argument('-f', '--file_column', default='C',
                        help='Column containing submission')
    parser.add_argument('--sheet', type=str, default='Form Responses 1',
                        help='Sheet name')
    parser.add_argument('-e', '--extension', type=str, default='zip',
                        help='Extension to be used in download.'
                        )
    parser.add_argument('-z', '--no_unzip', action='store_true', default=False,
                        help='Do not unzip the downloaded files.')
    parser.add_argument('-d', '--destination_dir', type=str,
                        default='.', help='Directory where to store the submissions.')
    parser.add_argument('-t', '--test', action='store_true', default=False,
                        help="Test but do not download anything")
    args = parser.parse_args()
    main(args)