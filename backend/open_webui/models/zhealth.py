import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from open_webui.internal.db import (
    Base,
    init_supa_table,
    create_schema_in_supabase,
)


SCHEMA_NAME = "zhealth"


class ZHealthRequest(Base):
    __tablename__ = "request"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    client = Column(String, nullable=False, default="zhealth")
    endpoint = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    model_id = Column(String, nullable=True)

    request_payload = Column(JSON, nullable=True)
    request_meta = Column(JSON, nullable=True)
    citations = Column(JSON, nullable=True)

    response_payload = Column(JSON, nullable=True)
    response_content = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    streaming = Column(Boolean, default=False, nullable=False)
    error = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)


class ZHealthEvent(Base):
    __tablename__ = "event"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    request_id = Column(PG_UUID(as_uuid=True), nullable=False)
    user_id = Column(String, nullable=True)
    chat_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    type = Column(String, nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


# Ensure schema and tables exist in Supabase
try:
    create_schema_in_supabase(SCHEMA_NAME)
    init_supa_table([ZHealthRequest.__table__, ZHealthEvent.__table__])
except Exception:
    # Avoid import-time hard failures; runtime calls will attempt inserts and log warnings
    pass

