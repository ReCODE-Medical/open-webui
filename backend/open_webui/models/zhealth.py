from sqlalchemy import Column, String, Integer, DateTime, Text, UUID, text
from datetime import datetime
import uuid
import json

from open_webui.internal.db import Base, JSONField, get_supabase_db, init_supa_table
import logging

log = logging.getLogger(__name__)


class ZhealthLog(Base):
    __tablename__ = 'zhealth_logs'
    __table_args__ = {'schema': 'zhealth'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    user_email = Column(String, nullable=True)
    
    # Request data
    request_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    model_id = Column(String, nullable=True)
    request_messages = Column(JSONField, nullable=True)
    request_params = Column(JSONField, nullable=True)
    
    # Response data
    response_timestamp = Column(DateTime(timezone=True), nullable=True)
    response_content = Column(Text, nullable=True)
    response_model = Column(String, nullable=True)
    response_tokens = Column(JSONField, nullable=True)  # Usage stats
    
    # Citations and sources
    citations = Column(JSONField, nullable=True)
    sources = Column(JSONField, nullable=True)
    
    # Middleware events
    middleware_events = Column(JSONField, nullable=True)
    
    # Metadata
    metadata = Column(JSONField, nullable=True)
    
    # Error tracking
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ZhealthLogs:
    def __init__(self, db):
        self.db = db
    
    @staticmethod
    def create_log(
        user_id: str,
        user_email: str = None,
        model_id: str = None,
        request_messages: list = None,
        request_params: dict = None,
        metadata: dict = None
    ) -> ZhealthLog:
        """Create a new zhealth log entry"""
        try:
            with get_supabase_db() as db:
                log_entry = ZhealthLog(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    user_email=user_email,
                    request_timestamp=datetime.utcnow(),
                    model_id=model_id,
                    request_messages=request_messages,
                    request_params=request_params,
                    metadata=metadata,
                    middleware_events=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                log.info(f"Created zhealth log entry: {log_entry.id}")
                return log_entry
        except Exception as e:
            log.error(f"Failed to create zhealth log: {e}")
            raise
    
    @staticmethod
    def update_log(
        log_id: uuid.UUID,
        response_content: str = None,
        response_model: str = None,
        response_tokens: dict = None,
        citations: list = None,
        sources: list = None,
        middleware_events: list = None,
        error: str = None
    ):
        """Update an existing zhealth log entry with response data"""
        try:
            with get_supabase_db() as db:
                log_entry = db.query(ZhealthLog).filter(ZhealthLog.id == log_id).first()
                if log_entry:
                    log_entry.response_timestamp = datetime.utcnow()
                    if response_content is not None:
                        log_entry.response_content = response_content
                    if response_model is not None:
                        log_entry.response_model = response_model
                    if response_tokens is not None:
                        log_entry.response_tokens = response_tokens
                    if citations is not None:
                        log_entry.citations = citations
                    if sources is not None:
                        log_entry.sources = sources
                    if middleware_events is not None:
                        log_entry.middleware_events = middleware_events
                    if error is not None:
                        log_entry.error = error
                    log_entry.updated_at = datetime.utcnow()
                    db.commit()
                    log.info(f"Updated zhealth log entry: {log_id}")
                else:
                    log.warning(f"Zhealth log entry not found: {log_id}")
        except Exception as e:
            log.error(f"Failed to update zhealth log: {e}")
            raise
    
    @staticmethod
    def add_middleware_event(log_id: uuid.UUID, event: dict):
        """Add a middleware event to an existing log"""
        try:
            with get_supabase_db() as db:
                log_entry = db.query(ZhealthLog).filter(ZhealthLog.id == log_id).first()
                if log_entry:
                    if log_entry.middleware_events is None:
                        log_entry.middleware_events = []
                    log_entry.middleware_events.append(event)
                    log_entry.updated_at = datetime.utcnow()
                    db.commit()
        except Exception as e:
            log.error(f"Failed to add middleware event: {e}")
    
    @staticmethod
    def get_log_by_id(log_id: uuid.UUID) -> ZhealthLog:
        """Get a log entry by ID"""
        try:
            with get_supabase_db() as db:
                return db.query(ZhealthLog).filter(ZhealthLog.id == log_id).first()
        except Exception as e:
            log.error(f"Failed to get zhealth log: {e}")
            return None


# Initialize the table when the module is imported
def init_zhealth_table():
    """Initialize the zhealth schema and table in Supabase"""
    try:
        with get_supabase_db() as db:
            # First, create the schema if it doesn't exist
            db.execute(text("CREATE SCHEMA IF NOT EXISTS zhealth"))
            db.commit()
            log.info("Zhealth schema created/verified")
        
        # Then create the table
        init_supa_table([ZhealthLog.__table__])
        log.info("Zhealth table initialized successfully")
    except Exception as e:
        log.warning(f"Failed to initialize zhealth table: {e}")
        # Don't raise - allow the app to continue even if zhealth logging isn't available

try:
    init_zhealth_table()
except Exception as e:
    log.warning(f"Could not initialize zhealth on import: {e}")