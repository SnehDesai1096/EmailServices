import os
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Set up the necessary scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    """Authenticate with Gmail API."""
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def delete_older_emails(days_threshold=30):
    """Delete emails older than a specified number of days using Gmail API."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Calculate the date threshold
    date_threshold = (datetime.utcnow() - timedelta(days=days_threshold)).strftime('%Y/%m/%d')

    # Get the list of messages older than the date threshold
    results = service.users().messages().list(userId='me', q=f'before:{date_threshold}').execute()
    messages = results.get('messages', [])

    if not messages:
        print('No older messages to delete.')
    else:
        for message in messages:
            msg_id = message['id']

            # Delete the message
            service.users().messages().delete(userId='me', id=msg_id).execute()

            print(f'Deleted message with ID {msg_id}.')

def delete_emails_past_year():
    """Delete emails older than one year using Gmail API."""
    days_threshold = 365  # Set to 366 for a leap year
    delete_older_emails(days_threshold)

def mark_unread_as_read():
    """Mark unread messages as read using Gmail API with pagination."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Get the list of unread messages
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = results.get('messages', [])
    total_unread = len(messages)

    while messages:
        # Mark the unread messages as read
        mark_read_label = {'removeLabelIds': ['UNREAD']}
        for message in messages:
            msg_id = message['id']
            service.users().messages().modify(userId='me', id=msg_id, body=mark_read_label).execute()

        # Get the next page of unread messages
        if 'nextPageToken' in results:
            page_token = results['nextPageToken']
            results = service.users().messages().list(userId='me', q='is:unread', pageToken=page_token).execute()
            messages = results.get('messages', [])
            total_unread += len(messages)
        else:
            messages = None

    print(f'Marked {total_unread} unread messages as read.')

def list_subscription_senders():
    """List unique senders from emails using Gmail API."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Set to store unique sender emails
    unique_senders = set()

    # Get the list of messages containing subscription-related keywords with a larger maxResults
    results = service.users().messages().list(userId='me', q='subject:subscribe OR subject:subscription', maxResults=500).execute()
    messages = results.get('messages', [])

    while 'nextPageToken' in results:
        page_token = results['nextPageToken']
        results = service.users().messages().list(userId='me', q='subject:subscribe OR subject:subscription', pageToken=page_token, maxResults=500).execute()
        messages.extend(results.get('messages', []))

    if not messages:
        print('No subscription-related emails found.')
    else:
        print('Unique Subscription-related senders:')
        for message in messages:
            msg_id = message['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            sender = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), 'Unknown Sender')
            unique_senders.add(sender)

        # Print the unique sender emails
        for sender_email in unique_senders:
            print(f'Sender: {sender_email}')
            print('---')

if __name__ == '__main__':
    # list_subscription_senders()
    mark_unread_as_read()
    # delete_emails_past_year()