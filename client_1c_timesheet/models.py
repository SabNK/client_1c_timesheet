""" Models the objects with which the clockify API works.
Models as simply as possible, omitting any fields not used by this package
TODO complete class and methods documentation
"""

from typing import Type, List
from abc import ABC, abstractmethod
import datetime

import dateutil
import dateutil.parser as date_parser

from client_1c_timesheet.exceptions import Client1CException

class ClockifyDatetime:
    """For converting between python datetime and clockify datetime string

    ClockifyDatetime is always timezone aware. If initialized with a naive datetime, local time is assumed
    """

    clockify_datetime_format = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self, datetime_in):
        """Create

        Parameters
        ----------
        datetime_in: datetime
            Set this date time. If no timezone is set, will assume local timezone
        """
        if not datetime_in.tzinfo:
            datetime_in = datetime_in.replace(tzinfo=dateutil.tz.tzlocal())
        self.datetime = datetime_in

    @property
    def datetime_utc(self):
        """This datetime in the UTC time zone"""
        return self.datetime.astimezone(dateutil.tz.UTC)

    @property
    def datetime_local(self):
        """This datetime as local time"""
        return self.datetime.astimezone(dateutil.tz.tzlocal())

    @property
    def clockify_datetime(self):
        """This datetime a clockify-format string"""
        return self.datetime_utc.strftime(self.clockify_datetime_format)

    @classmethod
    def init_from_string(cls, clockify_date_string):
        return cls(date_parser.parse(clockify_date_string))

    def __str__(self):
        return self.clockify_datetime

class APIObject(ABC):
    """An root for objects that is used in the clockify API and its children
    can be intiated from API response"""

    def __str__(self):
        return f"{self.__class__.__name__} "

    @classmethod
    def get_item(cls, dict_in: dict, key: str, raise_error: bool = True) -> object:
        """ Get item from dict, raise exception or return None if not found

        Parameters
        ----------
        dict_in: dict
            dict to search in
        key: str
            dict key
        raise_error: bool,
                    optional
            If True raises error when key not found. Otherwise returns None. Defaults to True

        Raises
        ------
        ObjectParseException
            When key is not found in dict and raise_error is False

        Returns
        -------
        object
            Dict item at key
        None
            If item not found and raise_error is True

        """
        try:
            return dict_in[key]
        except KeyError:
            msg = f"Could not find key '{key}' in '{dict_in}'"
            if raise_error:
                raise ObjectParseException(msg)

    @classmethod
    def get_datetime(cls, dict_in, key, raise_error=True):
        """ Try to find key in dict and parse to datetime

        Parameters
        ----------
        dict_in: dict
            dict to search in
        key: str
            dict key
        raise_error: bool
                    ,optional
            If True raises error when key not found. Otherwise returns None. Defaults to True

        Raises
        ------
        ObjectParseException
            When key is not found in dict (if raise_error is True) or could not be parsed to datetime.
            Exception is always raised when value cannot be parsed

        Returns
        -------
        datetime
            parsed date from dict[key]
        None
            If item not found and raise_error is True
        """
        date_str = cls.get_item(dict_in, key, raise_error=raise_error)
        if not date_str:
            return None
        try:
            return ClockifyDatetime.init_from_string(date_str).datetime
        except ValueError as e:
            msg = f"Error parsing {date_str} to datetime: '{e}'"
            raise ObjectParseException(msg)

    @classmethod
    @abstractmethod
    def init_from_dict(cls, dict_in):
        """ Create an instance of this class from the expected json dict returned from Clockify API

        Parameters
        ----------
        dict_in: dict
            As returned from Clockify API

        Raises
        ------
        ObjectParseException
            If dict_in does not contain all required field for creating an object

        Returns
        -------
        Type[APIObject]
            instance of this class, initialized to the values in dict_in

        """
        return

#TODO currency converter feature
class HourlyRate(APIObject):
    """Feature of users per project and per workspace and default for project and workspace"""

    def __init__(self, amount: float, currency: str):
        self.amount = amount
        self.currency = currency

    def __str__(self):
        return super().__str__() + f"{self.amount} {self.currency}"

    @classmethod
    def init_from_dict(cls, dict_in) -> 'HourlyRate':
        dict_hourlyRate = cls.get_item(dict_in=dict_in, key='hourlyRate')
        #to prevent from get.item from None
        if dict_hourlyRate:
            return cls(amount=cls.get_item(dict_hourlyRate, key='amount')/100,
                   currency=cls.get_item(dict_hourlyRate, key='currency'))
        #else:
            #return None

class APIObjectID(APIObject):
    """An object that can be returned by the clockify API, has its ID, one level above json dicts."""
    def __init__(self, obj_id):
        """
        Parameters
        ----------
        obj_id: str
            object id hash
        """
        self.obj_id = obj_id


    def __eq__(self, other):
        """Some objects may be omitted in Clockify time entry (the regulation is forceProjects,
        forceTasks, forceTags), so we introduced comparison to None

        Parameters
        ----------
        other: None or APIObjectID
        """

        if other:
            return self.obj_id == other.obj_id
        else:
            return False

    def __ne__(self, other):
        """
        Parameters
        ----------
        other: None or APIObjectID"""
        return not self.__eq__(other)

    def __hash__(self):
        """using Clockify hash stored in obj_id"""
        return self.obj_id.__hash__()

    def __str__(self):
        return super().__str__() + f"({self.obj_id}) "

    @classmethod
    def init_from_dict(cls, dict_in) -> Type[APIObject]:
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'))

class UserGroup(APIObjectID):
    """Group of Users - is used to assign multiple users to project
    TO DO: implement class
    """

    def __init__(self, obj_id, users):
        super().__init__(obj_id=obj_id)
        self.users = users

    @classmethod
    def init_from_dict(cls, dict_in):
        pass

class NamedAPIObject(APIObjectID):
    """An object of clockify API, with name and ID"""
    def __init__(self, obj_id, name):
        """
        Parameters
        ----------
        obj_id: str
            object id hash
        name: str
            human readable string
        """
        super().__init__(obj_id=obj_id)
        self.name = name

    def __str__(self):
        return super().__str__() + f"'{self.name}' "

    @classmethod
    def init_from_dict(cls, dict_in):
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'),
            name=cls.get_item(dict_in=dict_in, key='Description'))


class TimeGroup(NamedAPIObject):
    def __init__(self, obj_id, name: str, letter: str, digit: str):
        super().__init__(obj_id=obj_id, name=name)
        self.letter = letter
        self.digit = digit

    @classmethod
    def init_from_dict(cls, dict_in):
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'),
                   name=cls.get_item(dict_in=dict_in, key='Description'),
                   letter=cls.get_item(dict_in=dict_in, key='БуквенныйКод'),
                   digit=cls.get_item(dict_in=dict_in, key='ЦифровойКод'),
                   )


class Organization(NamedAPIObject):
    pass


class Employee(NamedAPIObject):
    def __init__(self, obj_id, name: str, person: APIObjectID, organization: APIObjectID):
        super().__init__(obj_id=obj_id, name=name)
        self.person = person
        self.organization = organization

    @classmethod
    def init_from_dict(cls, dict_in):
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'),
                   name=cls.get_item(dict_in=dict_in, key='Description'),
                   person=cls.get_item(dict_in=dict_in, key='ФизическоеЛицо_Key'),
                   organization=cls.get_item(dict_in=dict_in, key='ГоловнаяОрганизация_Key'),
                   )


class TimeSheetRecord:
    def __init__(self, hours: float, time_group: APIObjectID, territory: APIObjectID,
                 working_conditions: APIObjectID, work_shift: bool):
        self._hours = int(hours*10)
        self.time_group = time_group
        self.territory = territory
        self.working_conditions = working_conditions
        self.work_shift = work_shift

    def get_hours(self):
        return self._hours/10


class TimeSheetLine(APIObjectID):
    def __init__(self, obj_id, number: str, employee: APIObjectID, time_sheet_records: List[TimeSheetRecord]):
        """
        Parameters
        ----------
        obj_id: str
            object id hash
        number: str
            line number in the timesheet
        employee: APIObjectID
            ref_key of the employee (to be substituted by employee with full data if needed)
        time_sheet_records: List[TimeSheetRecord]
            31 time sheet records with hours, time_groups and etc.
        """
        super().__init__(obj_id=obj_id)
        self.number = number
        self.employee = employee
        self.time_sheet_records = time_sheet_records

    @classmethod
    def init_from_dict(cls, dict_in):
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'),
                   number=cls.get_item(dict_in=dict_in, key='LineNumber'),
                   employee=APIObjectID(cls.get_item(dict_in=dict_in, key='Сотрудник_Key')),
                   time_sheet_records=[TimeSheetRecord(
                       hours=cls.get_item(dict_in=dict_in, key="Часов" + str(i)),
                       time_group=cls.get_item(dict_in=dict_in, key="ВидВремени" + str(i) + "_Key"),
                       territory=cls.get_item(dict_in=dict_in, key="Территория" + str(i) + "_Key"),
                       working_conditions=cls.get_item(dict_in=dict_in, key="УсловияТруда" + str(i) + "_Key"),
                       work_shift=cls.get_item(dict_in=dict_in, key="ПереходящаяЧастьСмены" + str(i)),)
                       for i in range(1, 31)],
                   )





class User(NamedAPIObject):
    def __init__(self, obj_id, name, email, hourly_rates: {APIObjectID: HourlyRate}):
        super().__init__(obj_id=obj_id, name=name)
        self.email = email
        self.hourly_rates = hourly_rates

    def __str__(self):
        return super().__str__() + f"email:{self.email}"

    @classmethod
    def init_from_dict(cls, dict_in):
        obj_id = cls.get_item(dict_in=dict_in, key='id')
        name = cls.get_item(dict_in=dict_in, key='name')
        email = cls.get_item(dict_in=dict_in, key='email')
        hourly_rates = {}
        #TODO rewrite using get_item
        for membership in dict_in['memberships']:
            if membership['hourlyRate']:
                api_id_project_or_workspace = APIObjectID(cls.get_item(dict_in=membership, key='targetId'))
                hourly_rates[api_id_project_or_workspace] = HourlyRate.init_from_dict(membership)
        return cls(obj_id=obj_id, name=name, email=email, hourly_rates=hourly_rates)

    def get_hourly_rate(self, workspace, project) -> 'HourlyRate':
        if project in self.hourly_rates.keys() and self.hourly_rates[project]:
            return self.hourly_rates[project]
        elif project in project.hourly_rates.keys() and project.hourly_rates[project]:
            return project.hourly_rates[project]
        elif workspace in self.hourly_rates.keys() and self.hourly_rates[workspace]:
            return self.hourly_rates[workspace]
        else:
            return workspace.hourly_rate

class Client(NamedAPIObject):
    pass

class Project(NamedAPIObject):
    def __init__(self, obj_id, name: str, client: Client, hourly_rates: {APIObjectID: HourlyRate}):
        super().__init__(obj_id=obj_id, name=name)
        self.client = client
        self.hourly_rates = hourly_rates

    def __str__(self):
        return super().__str__() + f"for client {self.client}"

    @classmethod
    def init_from_dict(cls, dict_in):
        obj_id = cls.get_item(dict_in=dict_in, key='id')
        name = cls.get_item(dict_in=dict_in, key='name')
        api_id_client = APIObjectID(cls.get_item(dict_in=dict_in, key='clientId'))
        api_id_project = APIObjectID(obj_id)
        hourly_rates = {api_id_project: HourlyRate.init_from_dict(dict_in)}
        for membership in dict_in['memberships']:
            if membership['hourlyRate']:
                api_id_user = APIObjectID(cls.get_item(dict_in=membership, key='userId'))
                hourly_rates[api_id_user] = HourlyRate.init_from_dict(membership)
        return cls(obj_id=obj_id, name=name, client=api_id_client, hourly_rates=hourly_rates)

    def get_hourly_rate(self, workspace, user) -> 'HourlyRate':
        if user in self.hourly_rates.keys() and self.hourly_rates[user]:
            return self.hourly_rates[user]
        elif self in self.hourly_rates.keys() and self.hourly_rates[self]:
            return self.hourly_rates[self]
        elif workspace in user.hourly_rates.keys() and user.hourly_rates[workspace]:
            return user.hourly_rates[workspace]
        else:
            return workspace.hourly_rate



class Task(NamedAPIObject):
    pass

class Tag(NamedAPIObject):
    pass

class TimeEntry(APIObjectID):

    def __init__(self, obj_id: str, start, user: str, description='', project=None, task=None, tags=None, end=None):
        """
        Parameters
        ----------
        obj_id: str
            object id hash
        start: datetime
            Start of time entry
        description: str, optional
            Human readable description of this time entry. Defaults to empty string
        project: Project,
                optional
            Project associated with this entry. Defaults to None
        end: DateTime,
                optional
            End of time entry. Defaults to None, meaning timer mode is activated
        """
        super().__init__(obj_id=obj_id)
        self.start = start
        self.user = user
        self.description = description
        self.project = project
        self.task = task
        self.tags = tags
        self.end = end

    def __str__(self):
        return super().__str__() + f"- '{self.truncate(self.description)}'"

    @staticmethod
    def truncate(msg, length=30):
        if msg[length:]:
            return msg[:(length-3)] + "..."
        else:
            return msg

    @classmethod
    def init_from_dict(cls, dict_in):
        # required parameters
        interval = cls.get_item(dict_in, 'timeInterval')
        obj_id = cls.get_item(dict_in=dict_in, key='id')
        start = cls.get_datetime(dict_in=interval, key='start')
        user_id = cls.get_item(dict_in=dict_in, key='userId', raise_error=False)
        api_id_user = APIObjectID(obj_id=user_id)

        # optional parameters
        description = cls.get_item(dict_in=dict_in, key='description', raise_error=False)
        project_id = cls.get_item(dict_in=dict_in, key='projectId', raise_error=False)
        api_id_project = APIObjectID(obj_id=project_id) if project_id else None
        task_id = cls.get_item(dict_in=dict_in, key='taskId', raise_error=False)
        api_id_task = APIObjectID(obj_id=task_id) if task_id else None
        tag_ids = cls.get_item(dict_in=dict_in, key='tagIds', raise_error=False)
        api_id_tags = [APIObjectID(obj_id=t_i) for t_i in tag_ids] if tag_ids else None
        end = cls.get_datetime(dict_in=interval, key='end', raise_error=False)

        return cls(obj_id=obj_id,
                   start=start,
                   description=description,
                   user=api_id_user,
                   project=api_id_project,
                   task=api_id_task,
                   tags=api_id_tags,
                   end=end
                   )

    def to_dict(self):
        """As dict that can be sent to API"""
        as_dict = {"id": self.obj_id,
                   "start": str(ClockifyDatetime(self.start)),
                   "description": self.description,
                   "userId": self.user.obj_id
                   }
        if self.end:
            as_dict["end"] = str(ClockifyDatetime(self.end))
        if self.project:
            as_dict["projectId"] = self.project.obj_id
        if self.task:
            as_dict["taskId"] = self.task.obj_id
        if self.tags:
            as_dict["tagIds"] = [t.obj_id for t in self.tags]
        return {x: y for x, y in as_dict.items() if y}  # remove items with None value

class ObjectParseException(Client1CException):
    pass
