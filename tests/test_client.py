import pytest
import os
import json
from client_1c_timesheet.api import APIServer, APIServerException, APIErrorResponse
from client_1c_timesheet.client import API1C, APISession

@pytest.fixture()
def credentials():
    CREDENTIALS_FILE = os.path.abspath('../credentials/1c.json')
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as task:
        setup_dict = json.load(task)
    return setup_dict

@pytest.fixture()
def a_server(credentials):
    return APIServer(credentials['url'])

@pytest.fixture()
def an_api(a_server):
    return API1C(api_server=a_server)

@pytest.fixture()
def an_api_session(credentials, a_server):
    return APISession(a_server, (credentials['user'], credentials['password']))

def test_api_calls_get(an_api_session):
    time_groups = an_api_session.get_time_groups()
    assert len(time_groups) == 40
    assert time_groups[0].name == 'Рабочее время'
    assert time_groups[1].digit == '01'
    organizations = an_api_session.get_organizations()
    assert len(organizations) == 2
    assert organizations[1].name == "АО ЧТЭ"
    assert organizations[1].to_dict()["Description"] == "АО ЧТЭ"
    employees = an_api_session.get_employees()
    assert len(employees) == 3
    assert employees[1].name == "Боширов Сергей Сергеевич"
    assert employees[2].organization.obj_id == "a2edb898-b4db-11eb-7297-000c298d5e5b"
    assert employees[2].to_dict()['ГоловнаяОрганизация_Key'] == "a2edb898-b4db-11eb-7297-000c298d5e5b"
    assert employees[1].to_dict()['Description'] == "Боширов Сергей Сергеевич"
    time_sheet_lines = an_api_session.get_time_sheet_lines()
    assert time_sheet_lines[0].number == '4'
    assert time_sheet_lines[6].time_sheet_records[0].get_hours() == 8.3
    assert time_sheet_lines[8].time_sheet_records[15].time_group.obj_id == "b398cab2-6ae7-11eb-8358-080027d91ffd"
    writetoafile('../credentials/test_TimeSheetLine_json', time_sheet_lines[3].to_dict())
    time_sheets = an_api_session.get_time_sheets()
    assert len(time_sheets) == 11
    with open("../credentials/output_filename", 'w', encoding='utf-8') as outfile:
        json.dump(time_sheets[1].to_dict(),
                  outfile,
                  ensure_ascii=False,
                  sort_keys=False,
                  indent=4,
                  separators=(',', ': ')
                  )

    writetoafile('../credentials/test_TimeSheet_json', time_sheets[1].to_dict())
    time_sheets[1].number = '0000-000045'
    new_time_sheet = an_api_session.add_time_sheet(time_sheets[1])
    with open("../credentials/new_time_sheet", 'w', encoding='utf-8') as outfile:
        json.dump(new_time_sheet.to_dict(),
                  outfile,
                  ensure_ascii=False,
                  sort_keys=False,
                  indent=4,
                  separators=(',', ': ')
                  )

def writetoafile(fname, data):
    with open(fname, 'w', encoding='utf-8') as fp:
        json.dump(data,
                  fp,
                  ensure_ascii=False,
                  sort_keys=False,
                  indent=4,
                  separators=(',', ': ')
                  )

