from typing import TypedDict

from pydantic import BaseModel


class Task(BaseModel):
    description: str
    result: str = ""
    status: str = "pending"  # pending | running | done | failed


class AgentState(TypedDict):
    run_id: str
    objective: str
    tasks: list[Task]
    current_task_index: int
    status: str   # running | completed | failed
    error: str
    total_input_tokens: int
    total_output_tokens: int
