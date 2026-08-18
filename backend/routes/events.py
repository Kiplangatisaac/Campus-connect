from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models.user import User
from ..models.event import Event, EventAttendee, EventStatus, RSVPStatus
from ..schemas.event import (
    EventCreate, EventUpdate, EventResponse,
    EventAttendeeResponse, EventRSVP, EventSearch
)
from ..dependencies import get_current_user, require_admin

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=list[EventResponse])
async def list_events(
    query: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    is_online: Optional[bool] = Query(None),
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Event).where(Event.status != EventStatus.DRAFT)

    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(or_(Event.title.ilike(search_term), Event.description.ilike(search_term)))

    if start_date:
        stmt = stmt.where(Event.start_time >= start_date)

    if end_date:
        stmt = stmt.where(Event.start_time <= end_date)

    if is_online is not None:
        stmt = stmt.where(Event.is_online == is_online)

    if status_filter:
        stmt = stmt.where(Event.status == status_filter)

    stmt = stmt.order_by(Event.start_time.asc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    events = result.scalars().all()

    responses = []
    for event in events:
        attendee_count = await db.scalar(
            select(func.count(EventAttendee.id)).where(
                EventAttendee.event_id == event.id,
                EventAttendee.status == RSVPStatus.GOING
            )
        )
        organizer = await db.get(User, event.organizer_id)
        responses.append(EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            image_url=event.image_url,
            start_time=event.start_time,
            end_time=event.end_time,
            organizer_id=event.organizer_id,
            organizer_name=organizer.full_name if organizer else "Unknown",
            max_attendees=event.max_attendees,
            status=event.status,
            is_online=event.is_online,
            meeting_url=event.meeting_url,
            latitude=event.latitude,
            longitude=event.longitude,
            attendee_count=attendee_count or 0,
            created_at=event.created_at,
            updated_at=event.updated_at,
        ))

    return responses


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time")

    event = Event(
        title=data.title,
        description=data.description,
        location=data.location,
        image_url=data.image_url,
        start_time=data.start_time,
        end_time=data.end_time,
        organizer_id=current_user.id,
        max_attendees=data.max_attendees,
        is_online=data.is_online,
        meeting_url=data.meeting_url,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)

    attendee = EventAttendee(
        event_id=event.id,
        user_id=current_user.id,
        status=RSVPStatus.GOING,
    )
    db.add(attendee)
    await db.flush()

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        location=event.location,
        image_url=event.image_url,
        start_time=event.start_time,
        end_time=event.end_time,
        organizer_id=event.organizer_id,
        organizer_name=current_user.full_name,
        max_attendees=event.max_attendees,
        status=event.status,
        is_online=event.is_online,
        meeting_url=event.meeting_url,
        latitude=event.latitude,
        longitude=event.longitude,
        attendee_count=1,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    attendee_count = await db.scalar(
        select(func.count(EventAttendee.id)).where(
            EventAttendee.event_id == event.id,
            EventAttendee.status == RSVPStatus.GOING
        )
    )

    organizer = await db.get(User, event.organizer_id)

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        location=event.location,
        image_url=event.image_url,
        start_time=event.start_time,
        end_time=event.end_time,
        organizer_id=event.organizer_id,
        organizer_name=organizer.full_name if organizer else "Unknown",
        max_attendees=event.max_attendees,
        status=event.status,
        is_online=event.is_online,
        meeting_url=event.meeting_url,
        latitude=event.latitude,
        longitude=event.longitude,
        attendee_count=attendee_count or 0,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.organizer_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    await db.flush()
    await db.refresh(event)

    organizer = await db.get(User, event.organizer_id)
    attendee_count = await db.scalar(
        select(func.count(EventAttendee.id)).where(
            EventAttendee.event_id == event.id,
            EventAttendee.status == RSVPStatus.GOING
        )
    )

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        location=event.location,
        image_url=event.image_url,
        start_time=event.start_time,
        end_time=event.end_time,
        organizer_id=event.organizer_id,
        organizer_name=organizer.full_name if organizer else "Unknown",
        max_attendees=event.max_attendees,
        status=event.status,
        is_online=event.is_online,
        meeting_url=event.meeting_url,
        latitude=event.latitude,
        longitude=event.longitude,
        attendee_count=attendee_count or 0,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.organizer_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    event.status = EventStatus.CANCELLED
    await db.flush()


@router.post("/{event_id}/rsvp", response_model=EventAttendeeResponse)
async def rsvp_event(
    event_id: int,
    data: EventRSVP,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.status == EventStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is cancelled")

    existing_rsvp = await db.execute(
        select(EventAttendee).where(
            EventAttendee.event_id == event_id,
            EventAttendee.user_id == current_user.id
        )
    )
    existing = existing_rsvp.scalar_one_or_none()

    if existing:
        existing.status = data.status
        await db.flush()
        await db.refresh(existing)

        return EventAttendeeResponse(
            id=existing.id,
            user_id=current_user.id,
            username=current_user.username,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            status=existing.status,
            created_at=existing.created_at,
        )

    if data.status == RSVPStatus.GOING and event.max_attendees:
        attendee_count = await db.scalar(
            select(func.count(EventAttendee.id)).where(
                EventAttendee.event_id == event_id,
                EventAttendee.status == RSVPStatus.GOING
            )
        )
        if attendee_count and attendee_count >= event.max_attendees:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is full")

    attendee = EventAttendee(
        event_id=event_id,
        user_id=current_user.id,
        status=data.status,
    )
    db.add(attendee)
    await db.flush()
    await db.refresh(attendee)

    return EventAttendeeResponse(
        id=attendee.id,
        user_id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        status=attendee.status,
        created_at=attendee.created_at,
    )


@router.get("/{event_id}/attendees", response_model=list[EventAttendeeResponse])
async def list_attendees(
    event_id: int,
    status_filter: Optional[RSVPStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EventAttendee, User)
        .join(User, EventAttendee.user_id == User.id)
        .where(EventAttendee.event_id == event_id)
    )

    if status_filter:
        stmt = stmt.where(EventAttendee.status == status_filter)

    stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        EventAttendeeResponse(
            id=attendee.id,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            status=attendee.status,
            created_at=attendee.created_at,
        )
        for attendee, user in rows
    ]


@router.get("/calendar/export", response_model=list[EventResponse])
async def export_calendar(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Event)
        .join(EventAttendee)
        .where(
            EventAttendee.user_id == current_user.id,
            EventAttendee.status == RSVPStatus.GOING,
            Event.status != EventStatus.CANCELLED,
        )
    )

    if start_date:
        stmt = stmt.where(Event.start_time >= start_date)
    if end_date:
        stmt = stmt.where(Event.start_time <= end_date)

    stmt = stmt.order_by(Event.start_time.asc())

    result = await db.execute(stmt)
    events = result.scalars().all()

    responses = []
    for event in events:
        organizer = await db.get(User, event.organizer_id)
        responses.append(EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            image_url=event.image_url,
            start_time=event.start_time,
            end_time=event.end_time,
            organizer_id=event.organizer_id,
            organizer_name=organizer.full_name if organizer else "Unknown",
            max_attendees=event.max_attendees,
            status=event.status,
            is_online=event.is_online,
            meeting_url=event.meeting_url,
            latitude=event.latitude,
            longitude=event.longitude,
            created_at=event.created_at,
            updated_at=event.updated_at,
        ))

    return responses
