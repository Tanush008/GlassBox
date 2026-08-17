"""CRUD endpoints for tasks."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status

from .. import database
from ..models import Task, TaskCreate, TaskUpdate
from ..utils import new_id, paginate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=Task)
def create_task(owner_id: str, payload: TaskCreate):
    task = Task(
        id=new_id(),
        owner_id=owner_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        created_at=datetime.utcnow(),
    )
    database.tasks_by_id[task.id] = task
    return task


@router.get("", response_model=List[Task])
def list_tasks(owner_id: str, page: int = 1, page_size: int = 20):
    owned = [t for t in database.tasks_by_id.values() if t.owner_id == owner_id]
    owned.sort(key=lambda t: t.priority, reverse=True)
    page_items, _total = paginate(owned, page, page_size)
    return page_items


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: str, payload: TaskUpdate):
    task = database.tasks_by_id.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    data = payload.model_dump(exclude_unset=True)
    updated = task.model_copy(update=data)
    database.tasks_by_id[task_id] = updated
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    if task_id not in database.tasks_by_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    del database.tasks_by_id[task_id]
