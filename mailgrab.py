#!/usr/bin/env python

""" Grabs WSU glasshouse data from gmail account and saves to file

"""

import imaplib
import email
import os


ORG_EMAIL = "@gmail.com"
FROM_EMAIL = "WSU.Glasshouse" + ORG_EMAIL
FROM_PWD = "GhWSU_*Hawk*_1099b"
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT = 993


detach_dir = '.'
if 'attachments' not in os.listdir(detach_dir):
    os.mkdir('attachments')

userName = FROM_EMAIL
passwd = FROM_PWD

try:
    imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
    typ, accountDetails = imapSession.login(userName, passwd)
    if typ != 'OK':
        raise Exception('Not able to sign in!')

    imapSession.select('"[Gmail]/All Mail"')
    typ, data = imapSession.search(None, 'ALL')
    if typ != 'OK':
        print('Error searching Inbox.')
        raise Exception

    # Iterating over all emails
    for msgId in data[0].split():
        typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            print('Error fetching mail.')
            raise Exception

        emailBody = messageParts[0][1]
        mail = email.message_from_bytes(emailBody)
        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                # print part.as_string()
                continue
            if part.get('Content-Disposition') is None:
                # print part.as_string()
                continue
            fileName = part.get_filename()

            if bool(fileName):
                filePath = os.path.join(detach_dir, 'attachments', fileName)
                if not os.path.isfile(filePath):
                    print(fileName)
                    fp = open(filePath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()

    imapSession.close()
    imapSession.logout()

except Exception as e:
    print(e.args[0])
