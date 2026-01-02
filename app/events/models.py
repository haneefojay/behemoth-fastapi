import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class EventStatus(str, enum.Enum):
    """Event status enumeration"""

    DRAFT = "draft"
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


event_organizers = Table(
    "event_organizers",
    DBBase.metadata,
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("added_at", DateTime, default=datetime.utcnow, nullable=False),
)


class Event(DBBase):
    """Event model with full-text search support"""

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True, index=True)
    status = Column(
        Enum(EventStatus), nullable=False, default=EventStatus.DRAFT, index=True
    )
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    capacity = Column(Integer, nullable=False, default=100)
    current_attendees = Column(Integer, nullable=False, default=0)
    created_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


    search_vector = Column(TSVECTOR)

    # Relationships
    created_by = relationship(
        "User", back_populates="created_events", foreign_keys=[created_by_id]
    )
    organizers = relationship(
        "User", secondary=event_organizers, back_populates="organized_events"
    )
    tasks = relationship("Task", back_populates="event", cascade="all, delete-orphan")
    attendees = relationship(
        "Attendee", back_populates="event", cascade="all, delete-orphan"
    )

    # Indexes for full-text search and common queries
    __table_args__ = (
        Index("ix_events_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_events_status_start_date", "status", "start_date"),
        UniqueConstraint("title", "start_date", "location", name="uq_event_title_date_loc"),
    )

    def __repr__(self):
        return f"<Event {self.title} ({self.status.value})>"

    @property
    def is_full(self) -> bool:
        """Check if event is at capacity"""
        return self.current_attendees >= self.capacity

    @property
    def available_spots(self) -> int:
        """Get number of available spots"""
        return max(0, self.capacity - self.current_attendees)
