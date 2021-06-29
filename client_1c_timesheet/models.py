""" Models the objects with which the 1C API works.
Models as simply as possible, omitting any fields not used by this package
TODO complete class and methods documentation
"""

from typing import Type, List
from abc import ABC, abstractmethod
from datetime import datetime, date

import dateutil
import dateutil.parser as date_parser

from client_1c_timesheet.exceptions import Client1CException


class Client1CDatetime:
    """For converting between python datetime and clockify datetime string

    ClockifyDatetime is always timezone aware. If initialized with a naive datetime, local time is assumed
    """

    datetime_format = "%Y-%m-%dT%H:%M:%SZ"

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
    """A root for objects that is used in the 1C API (odata.metadata) and its children
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

    @abstractmethod
    def to_dict(self):
        """As dict that can be sent to API"""
        return


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
        """Some objects may be omitted in 1C API so we introduced comparison to None

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
        """using API hash stored in obj_id"""
        return self.obj_id.__hash__()

    def __str__(self):
        return super().__str__() + f"({self.obj_id}) "

    @classmethod
    def init_from_dict(cls, dict_in) -> Type[APIObject]:
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'))

    def to_dict(self):
        """As dict that can be sent to API"""
        return {"Ref_Key": self.obj_id}


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

    def to_dict(self):
        return super().to_dict() | {"Description": self.name}


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

    def to_dict(self):
        as_dict = super().to_dict() | {'БуквенныйКод': self.letter, 'ЦифровойКод': self.digit}
        return {x: y for x, y in as_dict.items() if y}  # remove items with None value


class Organization(NamedAPIObject):
    pass


class Person(NamedAPIObject):
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
                   person=APIObjectID(cls.get_item(dict_in=dict_in, key='ФизическоеЛицо_Key')),
                   organization=APIObjectID(cls.get_item(dict_in=dict_in, key='ГоловнаяОрганизация_Key')),
                   )

    def to_dict(self):
        as_dict = super().to_dict() | \
                  {"ФизическоеЛицо_Key": self.person.obj_id, "ГоловнаяОрганизация_Key": self.organization.obj_id}
        return {x: y for x, y in as_dict.items() if y}  # remove items with None value


class TimeSheetRecord:
    def __init__(self, day: int, hours: float, time_group: APIObjectID, territory: APIObjectID,
                 working_conditions: APIObjectID, work_shift: bool):
        self.day = day
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
                       day=day,
                       hours=cls.get_item(dict_in=dict_in, key=f'Часов{day}'),
                       time_group=APIObjectID(cls.get_item(dict_in=dict_in, key=f'ВидВремени{day}_Key')),
                       territory=APIObjectID(cls.get_item(dict_in=dict_in, key=f'Территория{day}_Key')),
                       working_conditions=APIObjectID(cls.get_item(dict_in=dict_in,
                                                                   key=f'УсловияТруда{day}_Key')),
                       work_shift=cls.get_item(dict_in=dict_in, key=f'ПереходящаяЧастьСмены{day}'))
                       for day in range(1, 32)],
                   )

    def to_dict(self):
        tsr_dict = {tsr.day: tsr for tsr in self.time_sheet_records}
        as_dict = super().to_dict() | \
              {'LineNumber': self.number, 'Сотрудник_Key': self.employee.obj_id} | \
              {f'Часов{day}': tsr.get_hours() for day, tsr in tsr_dict.items()} | \
              {f'ВидВремени{day}_Key': tsr.time_group.obj_id for day, tsr in tsr_dict.items()} | \
              {f'Территория{day}_Key': tsr.territory.obj_id for day, tsr in tsr_dict.items()} | \
              {f'УсловияТруда{day}_Key': tsr.working_conditions.obj_id for day, tsr in tsr_dict.items()} | \
              {f'ПереходящаяЧастьСмены{day}': tsr.work_shift for day, tsr in tsr_dict.items()}
        return as_dict
        #        {x: y for x, y in as_dict.items() if y}  # remove items with None value


class TimeSheet(APIObjectID):
    def __init__(self, obj_id,
                 period: date,
                 organization: APIObjectID,
                 date_start: date,
                 date_end: date,
                 time_sheet_lines: List[TimeSheetLine],
                 number: str = None,
                 datetime_stamp: datetime = None,
                 orgunit: APIObjectID = None):
        """
        Parameters
        ----------
        obj_id: str
            object id hash
        period: datetime.date
            period of timesheet - by fact - month, but start date of the reported month
            (in 1C - month - so it is datetime of 2021-06-01T00:00:00)
        organization: APIObjectID
            ref_key of the organization (to be substituted by object of Class Organization with full data if needed)
        date_start: datetime.date
            start date of the period (within the month of period)
        date_end: datetime.date
            end date of the period (see above date_start)
        time_sheet_lines: List[TimeSheetLine]
            lines with timesheet records for each employee (might be several lines per employee)
        number: str
            unique number of the timesheet, might be omitted, to be set up in 1C
        datetime_stamp: datetime
            date time stamp of the document TimeSheet, might be omitted, to be set up in 1C
        orgunit: APIObjectID
            ref_key of the organization unit (to be substituted by object of Class OrgUnit with full data if needed)
        """
        super().__init__(obj_id=obj_id)
        #ToDo implement TypeError and ValueError for None and some strange years (e.g. 1970) with dates
        self.period = period
        self.organization = organization
        self.date_start = date_start
        self.date_end = date_end
        self.time_sheet_lines = time_sheet_lines
        self.number = number if number else None
        self.datetime_stamp = datetime_stamp if datetime_stamp else None
        self.orgunit = orgunit if orgunit else None

    @classmethod
    def init_from_dict(cls, dict_in):
        return cls(obj_id=cls.get_item(dict_in=dict_in, key='Ref_Key'),
                   period=datetime.fromisoformat(cls.get_item(dict_in=dict_in, key='ПериодРегистрации')).date(),
                   organization=APIObjectID(cls.get_item(dict_in=dict_in, key='Организация_Key')),
                   date_start=datetime.fromisoformat(cls.get_item(dict_in=dict_in, key='ДатаНачалаПериода')).date(),
                   date_end=datetime.fromisoformat(cls.get_item(dict_in=dict_in, key='ДатаОкончанияПериода')).date(),
                   time_sheet_lines=[TimeSheetLine.init_from_dict(dict_in=d) for d in dict_in['ДанныеОВремени']],
                   number=cls.get_item(dict_in=dict_in, key='Number'),
                   datetime_stamp=datetime.fromisoformat(cls.get_item(dict_in=dict_in, key='Date')),
                   orgunit=APIObjectID(cls.get_item(dict_in=dict_in, key='Подразделение_Key')),
                   )

    def to_dict(self):
        date_start_str = datetime.combine(self.date_start, datetime.min.time()).isoformat() if self.date_start else None
        date_end_str = datetime.combine(self.date_end, datetime.min.time()).isoformat() if self.date_end else None
        datetime_stamp_str = self.datetime_stamp.isoformat() if self.datetime_stamp else None
        period_str = datetime.combine(self.period, datetime.min.time()).isoformat() if self.period else None
        orgunit_str = self.orgunit.obj_id if self.orgunit else None
        as_dict = super().to_dict() | \
                  {'Number': self.number, 'Date': datetime_stamp_str, "ПериодРегистрации": period_str,
                   'Организация_Key': self.organization.obj_id, 'Подразделение_Key': orgunit_str,
                   'ДатаНачалаПериода': date_start_str, 'ДатаОкончанияПериода': date_end_str,
                   'ДанныеОВремени': [x.to_dict() for x in self.time_sheet_lines]
                   }
        return {x: y for x, y in as_dict.items() if y}  # remove items with None value


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
