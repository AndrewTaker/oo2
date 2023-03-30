import os.path
import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime
from time import sleep
from typing import Union, Dict, List, Tuple
from annotations import GOOGLE_SPREADSHEET_INSTANCE

SECRETS_DIRECTORY = os.path.join(os.path.dirname(os.getcwd()), 'secrets')
load_dotenv(os.path.join(SECRETS_DIRECTORY, '.env'))

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS = os.path.join(SECRETS_DIRECTORY, 'credentials.json')
TOKEN = os.path.join(SECRETS_DIRECTORY, 'token.json')

START = datetime.strptime('08:50', "%H:%M").time()
END = datetime.strptime('18:00', "%H:%M").time()
SLEEP_TIME = 600

CODES_RANGE = 'Sheet1!A2:A163'
STATUS_RANGE = 'Sheet1!H2:H163'
DATE_RANGE = 'Sheet1!G2:G163'
UPDATE_TIME_RANGE = 'Sheet1!J3'

GIVC_LOGIN = os.getenv('GIVC_LOGIN')
GIVC_PASSWORD = os.getenv('GIVC_PASSWORD')


def login_givc(
        GIVC_LOGIN: Union[str, int],
        GIVC_PASSWORD: Union[str, int]
) -> requests.Session:
    """
    Login to givc via requests library.
    Return 'requests.Session' instance to keep coockies.
    """
    login_credentials = {
        'login': GIVC_LOGIN,
        'pswrd': GIVC_PASSWORD,
    }
    login_url = 'https://cabinet.miccedu.ru/'
    givc = requests.Session()
    try:
        givc.post(login_url, data=login_credentials)
    except Exception as error:
        print(error)
    return givc


def process_org(givc: requests.Session, id: Union[str, int]) -> Tuple:
    """
    Make a call to a cabinet.miccedu.ru with your login credentials
    and access accordion values. Returns tuple with (status, date) values.
    """
    url = 'https://cabinet.miccedu.ru/object/ajax/edit.php?id={}&pid\
        =35716&type=99&form=oo2&reqtype=supload&container=juploadtr&edulevel=2'
    report = givc.get(url.format(id))
    soup = BeautifulSoup(report.text, 'html.parser')
    soup_query = soup.find_all('td')
    if soup_query:
        status = soup_query[4].string
        date = soup_query[1].string
    else:
        status, date = None, None
    return status, date


def sheet_update(
    sheet: GOOGLE_SPREADSHEET_INSTANCE,
    spreadsheetId: str,
    range: str,
    data: str = '',
    valueInputOption: str = 'USER_ENTERED',
):
    """
    Functional version of google sheets api method.
    Made to free up code space.
    Original method: 'service.spreadsheets().values().update'
    """
    sheet.values().update(
        spreadsheetId=spreadsheetId,
        range=range,
        valueInputOption=valueInputOption,
        body={'values': [[f'{data}']]}
    ).execute()


def sheet_get(
    sheet: GOOGLE_SPREADSHEET_INSTANCE,
    spreadsheetId: str, range: str
) -> None:
    """
    Functional version of google sheets api method.
    Made to free up code space.
    Original method: 'service.spreadsheets().values().get'
    """
    sheet.values().get(
        spreadsheetId=spreadsheetId,
        range=range,
    ).execute()


def sheet_batch_update(
    sheet: GOOGLE_SPREADSHEET_INSTANCE,
    spreadsheetId: str,
    body: Dict[Union[str, int]]
) -> None:
    """
    Functional version of google sheets api method.
    Made to free up code space.
    Original method: 'service.spreadsheets().values().batchUpdate'
    """
    sheet.values().batchUpdate(
        spreadsheetId=spreadsheetId, body=body
    ).execute()


def apply_credentials() -> Credentials:
    """
    Check and verify google api credentials
    """
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, 'w') as token:
            token.write(creds.to_json())
    return creds


def get_givc_status_and_upload_date(
    givc: requests.Session,
    ids: List
) -> Dict[str, List]:
    """
    Iterate over list of ids with 'process_org()' method.
    Returns dict in following format:\n
    {
        'org1_id': [status, date],
        'org2_id': [status, date],
        ...
    }
    """
    data = {}
    counter = 1
    for id in ids:
        organisation_data = process_org(givc, id)
        data[id] = list(organisation_data)
        print(f"working on {id}, {counter}/{len(ids)}", end='\r')
        counter += 1
    return data


def initialize_sheet_class(credentials) -> GOOGLE_SPREADSHEET_INSTANCE:
    """
    Functional version of google sheets api method.
    Made to free up code space.
    Original method: 'build(args).spreadsheets()'
    """
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    return sheet


def body_for_values_batch_update(
        data_values: List,
        data_range: str,
        valueInputOption: str = 'RAW',
        data_majorDimension: str = 'COLUMNS',
) -> Dict:
    """
    Create body for method 'sheet_batch_update()'
    Returns dict in following format:\n
    {
        'valueInputOption': str,
        'data': [
            {
                'range': str,
                'majorDimension': str,
                'values': list
            }
        ]
    }
    """
    body = {
        'valueInputOption': valueInputOption,
        'data': [
            {
                'range': data_range,
                'majorDimension': data_majorDimension,
                'values': [
                    data_values,
                ]
            }
        ]
    }
    return body


def main():
    credentials = apply_credentials()
    givc = login_givc()
    sheet = initialize_sheet_class(credentials)

    organisation_codes = sheet_get(
        spreadsheetId=SPREADSHEET_ID,
        range=CODES_RANGE,
    )
    raw_codes = organisation_codes.get('values', [])
    codes = [i for j in raw_codes for i in j]

    while True:
        current_time = datetime.now().time()
        if current_time > START and current_time < END:
            data = get_givc_status_and_upload_date(givc, codes[:5])
            statuses = [status[0] for status in data.values()]
            dates = [date[1] for date in data.values()]

            status_body = body_for_values_batch_update(statuses, STATUS_RANGE)
            date_body = body_for_values_batch_update(dates, DATE_RANGE)

            sheet_batch_update(spreadsheetId=SPREADSHEET_ID, body=status_body)
            sheet_batch_update(spreadsheetId=SPREADSHEET_ID, body=date_body)
            sheet_update(
                sheet,
                SPREADSHEET_ID,
                UPDATE_TIME_RANGE,
                f'last update {datetime.now().strftime("%d.%m.%Y, %H:%M")}'
            )
            print('\ndone, sleeping for 10 min')
            sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
