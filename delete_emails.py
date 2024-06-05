import os.path
import base64
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://mail.google.com/']

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        # Handle errors from Gmail API.
        print(f'An error occurred: {error}')

def delete_emails(service, sender_email):
    # Get the list of messages
    try:
        results = service.users().messages().list(userId='me', q=f'from:{sender_email}').execute()
        messages = results.get('messages', [])
        
        if not messages:
            print(f'No emails found from {sender_email}')
            return
        
        for message in messages:
            msg_id = message['id']
            service.users().messages().delete(userId='me', id=msg_id).execute()
            print(f'Deleted email with ID: {msg_id}')
            
    except HttpError as error:
        print(f'An error occurred: {error}')

def main():
    service = authenticate_gmail()
    sender_email = 'News@insideapple.apple.com'  # Replace with the email address you want to delete emails from
    delete_emails(service, sender_email)

if __name__ == '__main__':
    main()
