"""Task API routes"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.exceptions import EventNotFoundException, NotFoundException
from app.common.permissions import CurrentUser
from app.common.schemas import ErrorResponse
from app.events.selectors import get_event_by_id
from app.tasks.models import Task
from app.tasks.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.tasks.services import create_task, delete_task, update_task

router = APIRouter()


@router.post(
    "/events/{event_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task for event",
    description="Create a new task for an event. Requires organizer permissions.",
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
async def create_task_endpoint(
    event_id: uuid.UUID,
    task_data: TaskCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Create a task for an event"""
    event = await get_event_by_id(session, event_id)

    if not event:
        raise EventNotFoundException(event_id)

    task = await create_task(session, event, task_data, current_user)
    return task


@router.get(
    "/events/{event_id}/tasks",
    response_model=list[TaskResponse],
    summary="List event tasks",
    description="Get all tasks for an event",
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
    },
)
async def list_event_tasks(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """List all tasks for an event"""

    event = await get_event_by_id(session, event_id)
    if not event:
        raise EventNotFoundException(event_id)

    result = await session.execute(
        select(Task).where(Task.event_id == event_id).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return tasks


@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update a task. Organizers and assignees can update.",
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
async def update_task_endpoint(
    task_id: uuid.UUID,
    task_data: TaskUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update a task"""
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise NotFoundException("Task not found")

    task = await update_task(session, task, task_data, current_user)
    return task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task. Requires organizer permissions.",
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
async def delete_task_endpoint(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete a task"""
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise NotFoundException("Task not found")

    await delete_task(session, task, current_user)
    return None
