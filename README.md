[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/V7V0Z8HFF)


# Inbox Ninja

This Python script automates the deletion of emails from specified senders in your Gmail account using the Gmail API. The script runs in a loop, periodically checking and deleting emails from the specified senders.

## Prerequisites

1. **Python 3.6+**: Ensure you have Python installed.
2. **Gmail API Credentials**: Obtain OAuth 2.0 Client IDs from the Google Cloud Console.

## Setup Instructions

### Step 1: Enable the Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the Gmail API for your project.
4. Create OAuth 2.0 Client IDs under "APIs & Services" > "Credentials".
5. Download the `credentials.json` file.

### Step 2: Install Required Libraries

Open your terminal or command prompt and run the following command to install the necessary libraries:

```sh
pip install -r requirements.txt
```

### Step 3: Edit the JSON file for Your Needs

You can edit `emails_to_delete.json` and add as many unwanted senders as you want :

```json
{
    "sender_emails": [
        "example1@example.com",
        "example2@example.com"
    ]
}
```

### Step 4: Configure and Run the Script

1. Save the script as `InboxNinja.py`.
2. Place the downloaded `credentials.json` file in the same directory as the script.
3. Run the script using the following command:

```sh
python delete_emails.py
```

The script will prompt you to authorize access to your Gmail account the first time it runs.

## Script Overview

### `delete_emails.py`

```python
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
```

### Explanation

- **Authenticate Gmail**: The `authenticate_gmail()` function ensures you have the correct credentials and necessary permissions.
- **Delete Emails**: The `delete_emails()` function deletes emails from the specified sender.
- **Load Emails**: The `load_emails_to_delete` function reads the list of sender emails from the JSON file.
- **Main Loop**: The `main()` function authenticates the Gmail service, loads sender emails from the JSON file, then enters an infinite loop where it iterates over the list of sender emails, calling `delete_emails()` for each one. After processing all senders, it sleeps for a specified period (`time.sleep(60)`) before repeating the process.

### Note

- Ensure you have the `credentials.json` file in the same directory as the script.
- The `token.json` file will be created after the first successful authentication and stores your access and refresh tokens.
- Adjust the `time.sleep(60)` value as needed to control how frequently the script checks for and deletes emails.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
