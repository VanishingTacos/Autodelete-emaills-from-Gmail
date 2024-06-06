import os
import time
import json
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://mail.google.com/']

LOG_FILE = 'bot.log'
MAX_LOG_LINES = 10000

def setup_logger():
    """Set up the logger."""
    logger = logging.getLogger('GmailDeletionBot')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def truncate_log_file():
    """Truncate the log file to the last MAX_LOG_LINES lines."""
    with open(LOG_FILE, 'r') as file:
        lines = file.readlines()

    if len(lines) > MAX_LOG_LINES:
        with open(LOG_FILE, 'w') as file:
            file.writelines(lines[-MAX_LOG_LINES:])

def authenticate_gmail():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        logger.error(f'An error occurred: {error}')

def delete_emails(service, sender_email):
    """Delete emails from the specified sender, including those in the spam folder."""
    try:
        query = f'from:{sender_email} OR (label:spam from:{sender_email})'
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            logger.info(f'No emails found from {sender_email}')
            return
        
        for message in messages:
            msg_id = message['id']
            try:
                service.users().messages().delete(userId='me', id=msg_id).execute()
                logger.info(f'Deleted email with ID: {msg_id}')
            except HttpError as error:
                if error.resp.status in [429, 500, 503]:
                    logger.warning(f'Rate limit or server error occurred: {error}')
                    backoff_time = random.uniform(1, 10)
                    logger.info(f'Retrying in {backoff_time:.2f} seconds...')
                    time.sleep(backoff_time)
                elif error.resp.status == 400 and error.resp.reason == 'failedPrecondition':
                    logger.warning(f'Skipping email with ID {msg_id} due to precondition failure.')
                else:
                    logger.error(f'An error occurred: {error}')
    except HttpError as error:
        logger.error(f'An error occurred: {error}')

def load_emails_to_delete(filename):
    """Load sender emails from a JSON file."""
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['sender_emails']

def main():
    global logger
    logger = setup_logger()
    service = authenticate_gmail()
    sender_emails = load_emails_to_delete('emails_to_delete.json')  # Load email addresses from JSON file

    while True:
        for sender_email in sender_emails:
            delete_emails(service, sender_email)
        truncate_log_file()
        time.sleep(60)

if __name__ == '__main__':
    main()
