# Copyright Luca de Alfaro, 2019
# BSD License

import argparse
import os
import pickle
# import yatl

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

from file_distributor import FileDistributor

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive']
# https://www.googleapis.com/auth/spreadsheets for r/w


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
    range_name = args.sheet
    sheet = sheet_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=args.spreadsheet_id,
                                range=range_name).execute()
    values = result.get('values', [])

    if not values or len(values) == 1:
        print('No data found.')
        return
    
    # Creates the file distributor.
    file_distributor = FileDistributor(drive_service, args.destination_dir)
    
    headers = values[0]
    # Computes reverse index of header to column.
    header2column = {header: i for i, header in enumerate(headers)}
    # Figures out which column is the email. 
    if args.email_column is not None:
        email_column = header2column[args.email_column]
    else:
        possible_email_columns = [header2column[h] for h in headers if 'email' in h.lower()]
        if len(possible_email_columns) == 1:
            email_column = possible_email_columns[0]
        else:
            print(f"Could not determine email column from headers {headers}")
            return
        
    # Produces the text. 
    for row in values[1:]:
        email = row[email_column]
        if email is None or '@' not in email:
            continue
        # We only process the required students. 
        if args.students is not None and email not in args.students:
            continue
        d = {headers[i].strip().replace(' ', '_') : row[i] for i in range(len(row))}
        with open(args.feedback, 'r') as f:
            text = f.read().format(**d)
        if args.test:
            print("Feedback for", email, ":")
            print(text)
            break
        # Shares the text. 
        filename = f'feedback_{email}.html'
        file_distributor.distribute_bytes(
            email, text.encode('utf-8'), filename, mime='text/plain', mode='reader', update=True)
        print("Distributed feedback to", email)
    print("Done.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--spreadsheet_id', default=None,
                        help="ID of the spreadsheet to use as base of download.")
    parser.add_argument('--sheet', type=str, default='Feedback',
                        help='Sheet name')
    parser.add_argument('-f', '--feedback', type=str, default=None,
                        help="Feedback template. Use \{column_name\} to refer to a column called 'column name'")
    parser.add_argument('-m', '--email_column', default=None,
                        help='Column containing email, if title is not email')
    parser.add_argument('-d', '--destination_dir', type=str, default=None, 
                        help='Destination folder ID in Drive for the feedback')
    parser.add_argument('-t', '--test', action='store_true', default=False,
                        help="Test but do not share anything")
    parser.add_argument('--students', type=str, default=None,
                        help='Comma-separated list of student emails whose feedback we want to share')
    args = parser.parse_args()
    main(args)