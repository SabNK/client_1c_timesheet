import requests
from functools import wraps
from time import sleep

from client_1c_timesheet.exceptions import Client1CException


def except_connection_error(func):
    """decorator to translate any requests connectionerror to APIException.

    Made this to have all common exceptions derive from ClockifyClientException
    """

    def decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise Client1CException(f'Requests connection error: {e}')

    return decorated

def request_rate_watchdog(rate_limit_requests_per_second):
    """decorator to maintain rate limit requests, by providing a sleep before request

       use for any APISession methods
    """
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            sleep(1 / rate_limit_requests_per_second)
            return func(*args, **kwargs)
        return inner
    return decorator
