import os
from typing import List

import requests
from dotenv import load_dotenv

from meeting_assistant_flow.types import MeetingTask

load_dotenv()

CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID")


def _require_clickup_vars():
    missing = [v for v, k in [("CLICKUP_API_TOKEN", CLICKUP_API_TOKEN), ("CLICKUP_LIST_ID", CLICKUP_LIST_ID)] if not k]
    if missing:
        raise EnvironmentError(
            f"Missing required ClickUp env vars: {', '.join(missing)}. "
            "See .env.example for reference."
        )


def create_clickup_task(task_name: str, task_description: str):
    """
    Create a new task in ClickUp for the given task.
    """
    _require_clickup_vars()
    url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"

    headers = {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {
        "name": task_name,
        "description": task_description,
        "status": "to do",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code in (200, 201):
        print(f"Task '{task_name}' successfully created in ClickUp.")
    else:
        print(f"Failed to create task '{task_name}' in ClickUp.")
        print(response.text)

    return response


def save_tasks_to_clickup(tasks: List[MeetingTask]):
    """
    Save a list of MeetingTask objects to ClickUp.
    """
    for task in tasks:
        if task.name and task.description:
            create_clickup_task(task.name, task.description)
        else:
            print("Task is missing a name or description. Skipping...")
