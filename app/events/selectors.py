"""Event selectors for querying and filtering"""

import uuid
from typing import List

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.types import PaginationParamsType
from app.events.models import Event, EventStatus, event_organizers
from app.events.schemas import EventFilterParams


async def get_event_by_id(session: AsyncSession, event_id: uuid.UUID) -> Event | None:
    """Get event by ID with eager loading

    Args:
        session: Database session
        event_id: Event ID

    Returns:
        Event instance or None
    """
    result = await session.execute(
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.organizers), selectinload(Event.created_by))
    )
    return result.scalar_one_or_none()


async def get_events(
    session: AsyncSession,
    filters: EventFilterParams | None = None,
    pagination: PaginationParamsType | None = None,
    search_query: str | None = None,
) -> tuple[List[Event], int]:
    """Get events with filtering, search, and pagination

    Args:
        session: Database session
        filters: Filter parameters
        pagination: Pagination parameters
        search_query: Full-text search query

    Returns:
        Tuple of (events list, total count)
    """

    query = select(Event).options(
        selectinload(Event.organizers), selectinload(Event.created_by)
    )


    conditions = []

    if filters:
        if filters.status:
            conditions.append(Event.status == filters.status)

        if filters.location:
            conditions.append(Event.location.ilike(f"%{filters.location}%"))

        if filters.start_date_from:
            conditions.append(Event.start_date >= filters.start_date_from)

        if filters.start_date_to:
            conditions.append(Event.start_date <= filters.start_date_to)

        if filters.has_capacity is not None:
            if filters.has_capacity:
                conditions.append(Event.current_attendees < Event.capacity)
            else:
                conditions.append(Event.current_attendees >= Event.capacity)

        if filters.organizer_id:
            query = query.join(
                event_organizers, Event.id == event_organizers.c.event_id
            ).where(event_organizers.c.user_id == filters.organizer_id)

        if filters.is_archived is not None:
            conditions.append(Event.is_archived == filters.is_archived)
        else:
            conditions.append(Event.is_archived == False)
    else:
        conditions.append(Event.is_archived == False)

    if search_query:

        query = query.where(Event.search_vector.match(search_query))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    sort_mapping = {
        "date": Event.start_date,
        "popularity": Event.current_attendees,
        "title": Event.title,
        "created_at": Event.created_at,
    }
    sort_attr = sort_mapping.get(pagination.sort_by, Event.start_date) if pagination else Event.start_date

    if pagination and pagination.order_by == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    if pagination:
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
    result = await session.execute(query)
    events = list(result.scalars().all())

    return events, total


async def get_user_events(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParamsType | None = None,
    is_archived: bool = False,
) -> tuple[List[Event], int]:
    """Get events created by or organized by a user

    Args:
        session: Database session
        user_id: User ID
        pagination: Pagination parameters
        is_archived: Whether to fetch archived events

    Returns:
        Tuple of (events list, total count)
    """
    query = (
        select(Event)
        .outerjoin(event_organizers, Event.id == event_organizers.c.event_id)
        .where(
            or_(
                Event.created_by_id == user_id,
                event_organizers.c.user_id == user_id,
            )
        )
    )

    if is_archived:
        query = query.where(Event.is_archived == True)
    else:
        query = query.where(Event.is_archived == False)

    query = (
        query
        .options(selectinload(Event.organizers), selectinload(Event.created_by))
        .distinct()
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    sort_mapping = {
        "date": Event.start_date,
        "popularity": Event.current_attendees,
        "title": Event.title,
        "created_at": Event.created_at,
    }
    sort_attr = sort_mapping.get(pagination.sort_by, Event.start_date) if pagination else Event.start_date

    if pagination and pagination.order_by == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    if pagination:
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)

    result = await session.execute(query)
    events = list(result.scalars().all())

    return events, total
