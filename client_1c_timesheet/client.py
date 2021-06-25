# -*- coding: utf-8 -*-
import datetime
from client_1c_timesheet.api import APIServer, APIServer404
from client_1c_timesheet.decorators import request_rate_watchdog
from client_1c_timesheet.models import TimeGroup, Organization, Employee, TimeSheetLine, TimeSheetRecord, User, Project, Task, TimeEntry, ClockifyDatetime, Tag, Client, HourlyRate
from functools import lru_cache
from typing import List, Dict

class APISession:
    """Models the interaction of one user with one workspace. Caches current user, workspace and projects.

    To make basic interactions quicker this class makes two simplifying assumptions:
    * All actions pertain to one user, the owner of the api_key
    * All actions pertain to only one workspace, the users default workspace

    """

    def __init__(self, api_server: APIServer, auth: (str, str) ):
        """
        Parameters
        ----------
        api_server: APIServer
            Server to use for communication
        auth: (str, str)
            basic auth: user and pass for 1C server
        """
        self.auth = auth
        self.api = API1C(api_server=api_server)


    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_time_groups(self) -> List[TimeGroup]:
        return self.api.get_time_groups(auth=self.auth)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_organizations(self) -> List[Organization]:
        return self.api.get_organizations(auth=self.auth)


    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_employees(self) -> List[Employee]:
        return self.api.get_employees(auth=self.auth)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_time_sheet_lines(self) -> List[TimeSheetLine]:
        return self.api.get_time_sheet_lines(auth=self.auth)

'''@request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def make_workspace(self, workspace_name: str) -> Workspace:
        return self.api.make_workspace(api_key=self.api_key, workspace_name=workspace_name)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_user(self):
        return self.api.get_user(api_key=self.api_key)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_users(self, workspace, page_size=200) -> List[User]:
        return self.api.get_users(api_key=self.api_key, workspace=workspace, page_size=page_size)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_projects(self, workspace, page_size=200) -> Project:
        return self.api.get_projects(api_key=self.api_key, workspace=workspace, page_size=page_size)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_clients(self, workspace, page_size=200):
        return self.api.get_clients(api_key=self.api_key, workspace=workspace, page_size=page_size)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_tasks(self, workspace, project, page_size=200):
        return self.api.get_tasks(api_key=self.api_key, workspace=workspace,
                                  project=project, page_size=page_size)

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_tags(self, workspace, page_size=200) -> List[Tag]:
        return self.api.get_tags(api_key=self.api_key, workspace=workspace, page_size=page_size)

    @lru_cache()
    def get_projects_with_tasks(self, workspace, page_size=200) -> Dict[Project, List[Task]]:
        """Get all Projects and Tasks for the given workspace, include None if Projects
        are not obligatory when entering time entry in Clockify, the same for Tasks. It is
        regulated by forceProjects and forceTasks in Workspace respectively

        Parameters
        ----------
        workspace: Workspace

        Returns
        -------
        Dict with Projects and Tasks in the workspace
        """
        projects = self.get_projects(workspace=workspace, page_size=page_size)
        projects_with_tasks = {} if workspace.forceProjects else {None: [None]}
        for project in projects:
            if workspace.forceTasks:
                projects_with_tasks[project] = self.get_tasks(workspace=workspace,
                                                              project=project, page_size=page_size)
            else:
                projects_with_tasks[project] = [None] + self.get_tasks(workspace=workspace,
                                                                       project=project, page_size=page_size)
        return projects_with_tasks

    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_time_entries(self, workspace, user, start_datetime, end_datetime, page_size=200):
        return self.api.get_time_entries(api_key=self.api_key,
                                         workspace=workspace,
                                         user=user,
                                         start_datetime=start_datetime,
                                         end_datetime=end_datetime,
                                         page_size=page_size)

    #ToDo for Local TimeSheet...
    @lru_cache()
    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def get_time_entries_local(self, workspace, user, start_datetime, end_datetime, page_size=200):

        return self.api.get_time_entries(api_key=self.api_key,
                                         workspace=workspace,
                                         user=user,
                                         start_datetime=start_datetime,
                                         end_datetime=end_datetime,
                                         page_size=page_size)


    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def add_time_entry_object(self, time_entry: TimeEntry):
        """Add the given time entry to the default workspace

        Parameters
        ----------
        time_entry: TimeEntry
            The time entry to add

        Returns
        -------
        TimeEntry
            The created time entry

        """
        return self.api.add_time_entry(api_key=self.api_key,
                                       workspace=self.get_default_workspace(),
                                       time_entry=time_entry)

    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def add_time_entry(self, start_time, user=None, end_time=None, description=None, project=None):
        """Add a time entry to default workspace. If no end time is given stopwatch mode is activated.

        This will stop any previously running stopwatch

        Parameters
        ----------
        start_time: datetime, UTC
            Set start of time entry to this
        user: User
            current user is supposed
        end_time: datetime, UTC, optional
            Set end of time entry to this. If not given, activate stopwatch mode. Defaults to None
        description: str, optional
            Description of this time entry. Defaults to None
        project: Project, optional
            Set the project that this time entry belongs to. Defaults to None

        Returns
        -------
        TimeEntry
            The created time entry

        """
        time_entry = TimeEntry(obj_id=None,
                               start=start_time,
                               description=description,
                               user=user,
                               project=project,
                               end=end_time)

        return self.add_time_entry_object(time_entry=time_entry)

    @request_rate_watchdog(APIServer.RATE_LIMIT_REQUESTS_PER_SECOND)
    def stop_timer(self, stop_time=None):
        """Halt the current timer

        Parameters
        ----------
        stop_time: datetime, UTC, optional
            Set the end date of the timed entry to this. Defaults to None, meaning time will be set to utcnow()
        Returns
        -------
        TimeEntry:
            The entry that was stopped
        None:
            When there was no timer running

        """
        if not stop_time:
            stop_time = self.now()

        return self.api.set_active_time_entry_end(
                    api_key=self.api_key,
                    workspace=self.get_default_workspace(),
                    user=self.get_user(),
                    end_time=stop_time
                )

    @staticmethod
    def now():
        """

        Returns
        -------
        datetime.datetime

        """
        return datetime.datetime.utcnow()
'''

class API1C:
    """A 1C API in the python world. Returns python objects. Does not know about http requests

    Notes
    -----
    For lower level (http) interactions, see api.APIServer

    """

    def __init__(self, api_server: APIServer):
        """

        Parameters
        ----------
        api_server: APIServer
        Server to use for communication"""

        self.api_server = api_server

    def get_time_groups(self, auth) -> List[TimeGroup]:
        """Get all time groups for the given account

        Parameters
        ----------
        auth: (str, str)
            1C basic auth

        Returns
        -------
        List[TimeGroup]"""
        response = self.api_server.get(path="Catalog_ВидыИспользованияРабочегоВремени", auth=auth)
        return [TimeGroup.init_from_dict(x) for x in response]

    def get_organizations(self, auth) -> List[Organization]:
        """Get all organizations for the given account

        Parameters
        ----------
        auth: (str, str)
            1C basic auth

        Returns
        -------
        List[Organization]"""
        response = self.api_server.get(path="Catalog_Организации", auth=auth)
        return [Organization.init_from_dict(x) for x in response]

    def get_employees(self, auth) -> List[Employee]:
        """Get all employees for the given account

        Parameters
        ----------
        auth: (str, str)
            1C basic auth

        Returns
        -------
        List[Employee]"""
        response = self.api_server.get(path="Catalog_Сотрудники", auth=auth)
        return [Employee.init_from_dict(x) for x in response]

    def get_time_sheet_lines(self, auth) -> List[TimeSheetLine]:
        """Get all time sheet lines from documents time sheet for the given account

        Parameters
        ----------
        auth: (str, str)
            1C basic auth

        Returns
        -------
        List[TimeSheetLine]"""
        response = self.api_server.get(path="Document_ТабельУчетаРабочегоВремени", auth=auth)
        return [TimeSheetLine.init_from_dict(x) for y in response for x in y["ДанныеОВремени"]]


    def get_user(self, api_key):
        """Get the user for the given api key

        Parameters
        ----------
        api_key: str
            Clockify Api key

        Returns
        -------
        User
        """
        response = self.api_server.get(path="/user", api_key=api_key)
        return User.init_from_dict(response)

    def get_users(self, api_key, workspace, page_size) -> List[User]:
        """Get users for the given workspace

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get users in this workspace
        page_size: int
            Number of records in one response
        Returns
        -------
        List[User]
        """
        params = {'page-size': page_size}
        response = self.api_server.get(path=f"/workspaces/{workspace.obj_id}/users", api_key=api_key, params=params)
        return [User.init_from_dict(x) for x in response]

    '''def make_project(self, api_key: str, project_name: str, client: Client = None,
                     additional_data: {str:str}=None)-> Project:
        """Post and create in Clockify project using project name with the given api key,
        for the given workspace

        Parameters
        ----------
        api_key: str
            Clockify Api key
        project_name: str
            The name of the workspace to be created

        Returns
        -------
        Project
        """
        response = self.api_server.post(path="/workspaces", api_key=api_key, data={"name": workspace_name})
        return Workspace.init_from_dict(response)

    def get_projects(self, api_key, workspace, page_size) -> List[Project]:
        """Get all projects for given workspace

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get projects in this workspace
        page_size: int
            Number of records in one response

        Returns
        -------
        List[Project]

        """
        params = {'page-size': page_size}
        response = self.api_server.get(
            path=f"/workspaces/{workspace.obj_id}/projects", api_key=api_key, params=params
        )
        return [Project.init_from_dict(x) for x in response]

    def get_clients(self, api_key, workspace, page_size) -> List[Client]:
        """Get all clients for given workspace

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get clients in this workspace
        page_size: int
            Number of records in one response

        Returns
        -------
        List[Client]

        """
        params = {'page-size': page_size}
        response = self.api_server.get(
            path=f"/workspaces/{workspace.obj_id}/clients",
            api_key=api_key,
            params=params
        )
        return [Client.init_from_dict(x) for x in response]

    def get_tasks(self, api_key, workspace, project, page_size) -> List[Task]:
        """Get all tasks for given project

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
        project: Project
            Get tasks in this project
        page_size: int
            Number of records in one response

        Returns
        -------
        List[Task]

        """
        params = {'page-size': page_size}
        response = self.api_server.get(
            path=f"/workspaces/{workspace.obj_id}/projects/{project.obj_id}/tasks",
            api_key=api_key,
            params=params
        )
        return [Task.init_from_dict(x) for x in response]

    def get_tags(self, api_key, workspace, page_size) -> List[Tag]:
        """Get all tags for given workspace

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get tags in this workspace
        page_size: int
            Number of records in one response

        Returns
        -------
        List[Tag]

        """
        params = {'page-size': page_size}
        response = self.api_server.get(
            path=f"/workspaces/{workspace.obj_id}/tags",
            api_key=api_key,
            params=params
        )
        return [Tag.init_from_dict(x) for x in response]

    def substitute_api_id_entities(self, time_entries, users=None, projects_with_tasks: {Project: [Task]}= None,
                                   tags=None) -> List[TimeEntry]:
        """Fill time entries with links to users, projects with tasks and tags instead of simple API_ID entities

        Parameters
        ----------
        time_entries : List[TimeEntry]
            a list of time entries to work on
        users: List[User]
            a list of users to set a link to
        projects_with_tasks : Dict[Project, List [Task]]
            a dict of projects and lists of tasks to set a link to
        tags : List[Tag]
            a list of tags to set a link to
        page_size: int
            Number of records in one response

        Returns
        -------
        List[TimeEntry]

        """

        if users:
            users_dict = {user: user for user in users}
        if projects_with_tasks:
            projects_dict = {project: project for project in projects_with_tasks.keys()}
            tasks_dict = {}
            for project in projects_with_tasks.keys():
                tasks_dict.update({task: task for task in projects_with_tasks[project]})
        if tags:
            tags_dict = {tag: tag for tag in tags}
        modified_time_entries = []
        for time_entry in time_entries:
            if users and time_entry.user in users_dict.keys():
                time_entry.user = users_dict[time_entry.user]
            if projects_with_tasks and time_entry.project in projects_dict.keys():
                time_entry.project = projects_dict[time_entry.project]
            if projects_with_tasks and time_entry.task in tasks_dict.keys():
                time_entry.task = tasks_dict[time_entry.task]
            if tags and time_entry.tags:
                t_e_tags = []
                for tag in time_entry.tags:
                    if tag.__hash__() in [t_e_t.__hash__() for t_e_t in time_entry.tags]:
                        t_e_tags.append(tags_dict[tag])
                time_entry.tags = t_e_tags
            modified_time_entries.append(time_entry)
        return modified_time_entries

    def get_time_entries(self, api_key: str, workspace: Workspace, user: User,
                         start_datetime, end_datetime, page_size) -> List[TimeEntry]:
        """Get all time entries for given workspace, user within datetime UTC interval

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get time entries in this workspace
        user : User
            Get time entries for this user
        start_datetime : datetime, UTC
            start datetime for query
        end_datetime : datetime, UTC
            end datetime for query
        page_size: int
            Number of records in one response

        Returns
        -------
        List[TimeEntry]

        """

        params = {'start': ClockifyDatetime(start_datetime).clockify_datetime,
                  'end': ClockifyDatetime(end_datetime).clockify_datetime,
                  'page-size': page_size}
        response = self.api_server.get(
            path=f"/workspaces/{workspace.obj_id}/user/{user.obj_id}/time-entries",
            api_key=api_key,
            params=params
        )
        return [TimeEntry.init_from_dict(te) for te in response]

    def add_time_entry(self, api_key: str, workspace: Workspace, time_entry: TimeEntry):
        """

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get projects in this workspace
        time_entry: TimeEntry
            The time entry to add

        Returns
        -------
        TimeEntry
            The created time entry

        """

        result = self.api_server.post(
            path=f"/workspaces/{workspace.obj_id}/time-entries",
            api_key=api_key,
            data=time_entry.to_dict(),
        )

        return TimeEntry.init_from_dict(result)

    def set_active_time_entry_end(
        self, api_key: str, workspace: Workspace, user: User, end_time: datetime
    ):
        """Set the end time for the currently active entry

        Parameters
        ----------
        api_key: str
            Clockify Api key
        workspace: Workspace
            Get projects in this workspace
        user: User
            The use for which to end the active time entry
        end_time: datetime
            Set the end time to this

        Returns
        -------
        TimeEntry
            The updated time entry, if an active one was found
        None
            If there was no active time entry (if a stopwatch was not running)

        """
        try:
            result = self.api_server.patch(
                path=f"/workspaces/{workspace.obj_id}/user/{user.obj_id}/time-entries/",
                api_key=api_key,
                data={"end": str(ClockifyDatetime(end_time))},
            )
        except APIServer404:
            return None

        return TimeEntry.init_from_dict(result)'''
