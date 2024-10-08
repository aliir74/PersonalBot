from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from notion_client import Client

from settings import NOTION_INTEGRATION_TOKEN

DUE_DATE_PROPERTY_NAME = "Due"


class TaskStatus(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class TaskPriority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass
class TaskProperties:
    completed_on: datetime
    task_name: str
    status: TaskStatus
    due: datetime
    priority: TaskPriority
    project_id: str

    def __init__(self, properties: dict):
        if properties["Completed on"]["date"] is not None:
            self.completed_on = datetime.fromisoformat(
                properties["Completed on"]["date"]
            )
        else:
            self.completed_on = None
        self.task_name = properties["Task name"]["title"][0]["text"]["content"]
        if properties["Due"]["date"]["end"] is not None:
            self.due = datetime.fromisoformat(properties["Due"]["date"]["end"])
        else:
            self.due = None

        self.project_id = properties["Project"]["relation"][0]["id"]
        self.priority = self._parse_priority(properties)
        self.status = self._parse_status(properties)

    def _parse_priority(self, properties: dict) -> TaskPriority:
        raw_priority = properties["Priority"]["select"]["name"]
        if raw_priority == "Low":
            return TaskPriority.LOW
        elif raw_priority == "Medium":
            return TaskPriority.MEDIUM
        elif raw_priority == "High":
            return TaskPriority.HIGH
        else:
            raise ValueError(f"Invalid priority: {raw_priority}")

    def _parse_status(self, properties: dict) -> TaskStatus:
        raw_status = properties["Status"]["status"]["name"]
        if raw_status == "Not Started":
            return TaskStatus.NOT_STARTED
        elif raw_status == "In Progress":
            return TaskStatus.IN_PROGRESS
        elif raw_status == "Completed":
            return TaskStatus.COMPLETED
        else:
            raise ValueError(f"Invalid status: {raw_status}")


@dataclass
class Task:
    object: str
    id: str
    created_time: datetime
    last_edited_time: datetime
    archived: bool
    in_trash: bool
    icon: str | None
    cover: str | None
    url: str
    properties: TaskProperties

    def __init__(self, task: dict):
        self.object = task["object"]
        self.id = task["id"]
        self.created_time = datetime.fromisoformat(task["created_time"])
        self.last_edited_time = datetime.fromisoformat(task["last_edited_time"])
        self.archived = bool(task["archived"])
        self.in_trash = bool(task["in_trash"])
        if (
            task.get("icon")
            and task["icon"].get("external")
            and task["icon"]["external"].get("url")
        ):
            self.icon = task["icon"]["external"]["url"]
        else:
            self.icon = None
        if (
            task.get("cover")
            and task["cover"].get("external")
            and task["cover"]["external"].get("url")
        ):
            self.cover = task["cover"]["external"]["url"]
        else:
            self.cover = None
        self.url = task["url"]
        self.properties = TaskProperties(task["properties"])


def get_client() -> Client:
    return Client(auth=NOTION_INTEGRATION_TOKEN)


def get_tasks_due(due_date: datetime = None) -> list[Task]:
    if due_date is None:
        due_date = datetime.now().date()

    response = get_client().databases.query(
        database_id="111a06ee07ab81f3bb5bed5b9a8dcb09",
        filter={
            "property": DUE_DATE_PROPERTY_NAME,
            "date": {"equals": due_date.isoformat()},
        },
    )
    return [Task(task).properties.task_name for task in response["results"]]
