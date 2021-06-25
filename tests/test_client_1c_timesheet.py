#!/usr/bin/env python

"""Tests for `client_1c_timesheet` package."""

import pytest
import json
import os

from client_1c_timesheet.api import APIServer


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')

@pytest.fixture
def credentials():
    CREDENTIALS_FILE = os.path.abspath('../credentials/1c.json')
    with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as task:
        setup_dict = json.load(task)
    return setup_dict


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_api(credentials):
    url = credentials['url']
    auth = (credentials['user'], credentials['password'])
    api = APIServer(url)
    path = "Catalog_Контрагенты"
    assert api.get(path, auth)['odata.metadata'].endswith(path)
    data = {
            "ДатаНачалаПериода": "2021-06-01T00:00:00",
            "ДатаОкончанияПериода": "2021-06-30T00:00:00",
            "Организация_Key": "a2edb898-b4db-11eb-7297-000c298d5e5b",
            "ПериодВводаДанныхОВремени": "ТекущийМесяц"
    }
    #path = 'Document_ТабельУчетаРабочегоВремени'
    #assert api.post(path, auth, data)['odata.metadata'].endswith('@Element')
