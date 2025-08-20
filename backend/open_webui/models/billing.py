from sqlalchemy import Column, String, Integer, DateTime, UUID

from open_webui.internal.db import Base

class SupabaseMessageUsage(Base):
    __tablename__ = 'message_usage'

    id = Column(UUID(as_uuid=True), primary_key=True)
    auth0_id = Column(String, unique=True, nullable=False)
    subscription_id = Column(UUID(as_uuid=True), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    messages_used = Column(Integer, default=0, nullable=False)
    messages_limit = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
