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
    employees = an_api_session.get_employees()
    assert len(employees) == 3
    assert employees[1].name == "Боширов Сергей Сергеевич"
    assert employees[2].organization == "a2edb898-b4db-11eb-7297-000c298d5e5b"
    time_sheet_lines = an_api_session.get_time_sheet_lines()
    assert time_sheet_lines[0].number == '4'
    assert time_sheet_lines[6].time_sheet_records[0].get_hours() == 8.3

