#!/usr/bin/env python

""" Downloads and prepares Priva WSU Glasshouse data for upload into a HIEv instance

1. Downloads CSV files sent from Priva system to dedicated Gmail
2. Converts Priva CSV files to HIEv-friendly TOA5 files

Refs:
- https://gist.github.com/baali/2633554

"""

import imaplib
import email
import os
import pandas as pd
import fnmatch
import re
import datetime
import credentials
import logging
import math


# ----------------
# Program settings
# ----------------
#  Set directory path for downloaded priva files (either relative or full pathname)
priva_directory = os.path.join('.', 'priva_originals')
#  Set directory path for converted TOA5 files (also where upload to HIEv will occur from)
hiev_directory = os.path.join('.', 'converted')


def clean_symbols(in_text):
    """ Convert subscripts/superscripts, symbols, etc to characters

    """
    if u'\u00B2' in str(in_text):
        return in_text.replace(u'\u00B2', '2')
    elif u'\u00B3' in str(in_text):
        return in_text.replace(u'\u00B3', '3')
    elif u'\u00B0' in str(in_text):
        return in_text.replace(u'\u00B0', 'Degrees')
    else:
        return in_text


def mail_grab():
    """ Downloads file attachments from given gmail address

    - Note that this function will only download attachments containing filenames that begin 'Export'

    """
    # Email settings
    username = credentials.gmail_login['username']
    passwd = credentials.gmail_login['password']

    yesterday = (datetime.date.today() - datetime.timedelta(2)).strftime('%Y%m%d')
    yesterday_under = (datetime.date.today() - datetime.timedelta(1)).strftime('%d-%b-%Y')

    try:
        imap_session = imaplib.IMAP4_SSL('imap.gmail.com')
        typ, account_details = imap_session.login(username, passwd)
        if typ != 'OK':
            raise Exception('Not able to sign in!')

        imap_session.select('"[Gmail]/All Mail"')
        typ, data = imap_session.search(None, "(ON {0})".format(yesterday_under))
        if typ != 'OK':
            print('Error searching Inbox.')
            raise Exception

        # Iterating over all emails
        for msgId in data[0].split():
            typ, message_parts = imap_session.fetch(msgId, '(RFC822)')
            if typ != 'OK':
                print('Error fetching mail.')
                raise Exception

            email_body = message_parts[0][1]
            mail = email.message_from_bytes(email_body)
            for part in mail.walk():
                if part.get_content_maintype() == 'multipart':
                    # print part.as_string()
                    continue
                if part.get('Content-Disposition') is None:
                    # print part.as_string()
                    continue
                file_name = part.get_filename()

                if bool(file_name) and file_name.startswith('Export') and yesterday in file_name:
                    file_path = os.path.join(priva_directory, file_name)
                    if not os.path.isfile(file_path):
                        fp = open(file_path, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()

        imap_session.close()
        imap_session.logout()

    except Exception as e:
        logging.error(e.args[0])


# PROGRAM START

logging.basicConfig(filename="log.txt", level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")
logging.info('')
logging.info('')
logging.info('-------------------------')
logging.info('Run Date - {}'.format(datetime.date.today()))
logging.info('-------------------------')


# Grab file attachment from Gmail account
logging.info('Checking gmail account for new priva files....')
mail_grab()

# Program works off of yesterday's data, so create a variable to hold that date
yesterday = (datetime.date.today() - datetime.timedelta(2)).strftime('%Y%m%d')
yesterday_match = '*%s.csv' % yesterday
priva_files = fnmatch.filter(os.listdir(priva_directory), yesterday_match)
logging.info('{} new priva files downloaded from gmail'.format(len(priva_files)))

# Modify downloaded priva CSV file to be HIEv-friendly
for priva_file in priva_files:
    logging.info("Converting priva file '{}' to TOA5 format and renaming".format(str(priva_file)))
    # Extract Table name from file name
    table_name = re.split('\[|\]', str(priva_file))
    toa5df = pd.DataFrame(["TOA5", "R3_T1", "CR3000", "6550", "CR3000.Std.22", "CPU:R3_T1_Flux_20160803.CR3", "50271",
                           table_name[0].replace(" ", "").replace("#", "")]).T

    # Open original file and modify to make it TOA5/'HIEv-friendly'
    with open(os.path.join(priva_directory, priva_file), newline='') as f:
        # Read in the Priva CSV file into dataframe
        r = pd.read_csv(f, sep=';', header=None)
        # Do a crude check that the CSV file actually contains CSV data
        if str(r.iloc[0][0]) != 'nan':
            logging.info('File {} ignored - does not contain CSV data'.format(str(priva_file)))
        else:
            # Check if the Priva data contains midnight date from the next day and delete it if so
            if '00:00:00' in r.iloc[-1][0]:
                r = r[:-1]
            # 'TIMESTAMP' needs to be in the header for proper hiev upload
            r.iloc[0][0] = "TIMESTAMP"
            # Concatenate together the toa5 dataframe with the priva dataframe
            toa5_final = pd.concat([toa5df, r])
            # Modify the format of the date column to 'YYYY-MM-DD HH:MM:SS'
            toa5_final[0][4:] = toa5_final[0][4:].map(lambda x: datetime.datetime.strptime(x,
                                                      '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'))

            # Swap the units and tables rows so that HIEv canm properly pick up correct units
            tables, units = toa5_final.iloc[2].copy(), toa5_final.iloc[3]
            toa5_final.iloc[2], toa5_final.iloc[3] = units, tables
            # Change the 'tables' row to 'sample type' row - in this case all 'AVE'.
            toa5_final.iloc[3] = 'AVE'
            # Convert subscripts/superscripts in units to full characters
            toa5_final.iloc[2] = toa5_final.iloc[2].map(lambda x: clean_symbols(x))

            new_filename = 'GHF_R_'+table_name[0].replace("_"+yesterday+".csv", "").replace(" ", "")\
                                                 .replace(".", "-").replace("#", "")+'.csv'

            with open(os.path.join(hiev_directory, new_filename), 'w', newline='') as p:
                toa5_final.to_csv(p, index=False, header=False)
                logging.info("TOA5 file '{}' successfully created".format(new_filename))
