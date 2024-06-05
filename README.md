
# Gmail Email Deletion Bot

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

### Step 3: Configure and Run the Script

1. Save the script as `delete_emails.py`.
2. Place the downloaded `credentials.json` file in the same directory as the script.
3. Modify the `sender_emails` list in the script to include the email addresses from which you want to delete emails.
4. Run the script using the following command:

```sh
python delete_emails.py
```

The script will prompt you to authorize access to your Gmail account the first time it runs.

## Script Overview

### `delete_emails.py`

```python
import os
import time
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://mail.google.com/']

def authenticate_gmail():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
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
    """Delete emails from the specified sender."""
    try:
        # Get the list of messages from the specified sender
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
    sender_emails = ['example1@example.com', 'example2@example.com']  # Add more email addresses as needed

    while True:
        for sender_email in sender_emails:
            delete_emails(service, sender_email)
        # Sleep for a specified time before running again (e.g., 60 seconds)
        time.sleep(60)

if __name__ == '__main__':
    main()
```

### Explanation

- **Authenticate Gmail**: The `authenticate_gmail()` function ensures you have the correct credentials and necessary permissions.
- **Delete Emails**: The `delete_emails()` function deletes emails from the specified sender.
- **Main Loop**: The `main()` function authenticates the Gmail service, then enters an infinite loop where it iterates over the list of sender emails, calling `delete_emails()` for each one. After processing all senders, it sleeps for a specified period (`time.sleep(60)`) before repeating the process.

### Note

- Ensure you have the `credentials.json` file in the same directory as the script.
- The `token.json` file will be created after the first successful authentication and stores your access and refresh tokens.
- Adjust the `time.sleep(60)` value as needed to control how frequently the script checks for and deletes emails.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
