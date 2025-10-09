from sqlalchemy import Column, String, Integer, DateTime, Text, UUID, text
from datetime import datetime, timedelta
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import uuid
import json

from open_webui.internal.db import Base, JSONField, get_supabase_db, init_supa_table
from pydantic import BaseModel, ConfigDict
import logging

log = logging.getLogger(__name__)

####################
# Zhealth Log DB Schema
####################


class ZhealthLog(Base):
    __tablename__ = 'zhealth_logs'

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
    log_metadata = Column(JSONField, nullable=True)
    
    # Error tracking
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ZhealthLogModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: str
    user_email: str | None = None
    request_timestamp: datetime
    model_id: str | None = None
    request_messages: list | None = None
    request_params: dict | None = None
    response_timestamp: datetime | None = None
    response_content: str | None = None
    response_model: str | None = None
    response_tokens: dict | None = None
    citations: list | None = None
    sources: list | None = None
    middleware_events: list | None = None
    log_metadata: dict | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


####################
# Forms
####################


class ZhealthLogForm(BaseModel):
    user_id: str
    user_email: str | None = None
    model_id: str | None = None
    request_messages: list | None = None
    request_params: dict | None = None
    log_metadata: dict | None = None


class ZhealthLogsTable:
    def __init__(self):
        self._init_table()
        # Thread pool for non-blocking Supabase write operations
        # Multiple workers allow concurrent updates for different requests
        self.supa_executor = ThreadPoolExecutor(
            max_workers=4, 
            thread_name_prefix="supa_zhealth_worker"
        )

    def __del__(self):
        """Cleanup thread pool on deletion"""
        self.supa_executor.shutdown(wait=False)

    def _init_table(self):
        """Initialize the zhealth_logs table in Supabase"""
        try:
            init_supa_table([ZhealthLog.__table__])
            log.info("Zhealth table initialized successfully")
        except Exception as e:
            log.warning(f"Failed to initialize zhealth table: {e}")
            # Don't raise - allow the app to continue even if zhealth logging isn't available
    
    def create_log(
        self,
        user_id: str,
        user_email: str | None = None,
        model_id: str | None = None,
        request_messages: list | None = None,
        request_params: dict | None = None,
        log_metadata: dict | None = None
    ) -> Optional[ZhealthLogModel]:
        """
        Create a new zhealth log entry (synchronous).
        
        This must be synchronous because we need the log_id returned immediately
        to use throughout the request lifecycle.
        """
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
                    log_metadata=log_metadata,
                    middleware_events=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                log.info(f"Created zhealth log entry: {log_entry.id}")
                return ZhealthLogModel.model_validate(log_entry)
        except Exception as e:
            log.error(f"Failed to create zhealth log: {e}")
            return None
    
    def update_log(
        self,
        log_id: uuid.UUID,
        response_content: str | None = None,
        response_model: str | None = None,
        response_tokens: dict | None = None,
        citations: list | None = None,
        sources: list | None = None,
        middleware_events: list | None = None,
        error: str | None = None
    ):
        """
        Update an existing zhealth log entry (non-blocking, fire-and-forget).
        
        This runs in a background thread to avoid blocking the async event loop.
        Multiple updates for different log_ids can run concurrently.
        
        Note: If called multiple times for the same log_id, the last update to 
        commit wins. In practice, each endpoint typically calls this once with 
        all final data, so race conditions are rare.
        """
        def _do_update():
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
                log.error(f"Failed to update zhealth log {log_id}: {e}")
        
        try:
            self.supa_executor.submit(_do_update)
        except Exception as e:
            log.error(f"Failed to submit zhealth update to thread pool: {e}")
    
    def add_middleware_event(self, log_id: uuid.UUID, event: dict):
        """
        Add a middleware event to an existing log (non-blocking, fire-and-forget).
        
        This runs in a background thread to avoid blocking the async event loop.
        """
        def _do_add_event():
            try:
                with get_supabase_db() as db:
                    log_entry = db.query(ZhealthLog).filter(ZhealthLog.id == log_id).first()
                    if log_entry:
                        if log_entry.middleware_events is None:
                            log_entry.middleware_events = []
                        log_entry.middleware_events.append(event)
                        log_entry.updated_at = datetime.utcnow()
                        db.commit()
                        log.debug(f"Added middleware event to log {log_id}")
            except Exception as e:
                log.error(f"Failed to add middleware event to log {log_id}: {e}")
        
        try:
            self.supa_executor.submit(_do_add_event)
        except Exception as e:
            log.error(f"Failed to submit middleware event to thread pool: {e}")
    
    def get_log_by_id(self, log_id: uuid.UUID) -> Optional[ZhealthLogModel]:
        """Get a log entry by ID"""
        try:
            with get_supabase_db() as db:
                log_entry = db.query(ZhealthLog).filter(ZhealthLog.id == log_id).first()
                if log_entry:
                    return ZhealthLogModel.model_validate(log_entry)
                return None
        except Exception as e:
            log.error(f"Failed to get zhealth log: {e}")
            return None

    def get_logs_by_user_id(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> list[ZhealthLogModel]:
        """Get all log entries for a user"""
        try:
            with get_supabase_db() as db:
                logs = (
                    db.query(ZhealthLog)
                    .filter(ZhealthLog.user_id == user_id)
                    .order_by(ZhealthLog.created_at.desc())
                    .offset(skip)
                    .limit(limit)
                    .all()
                )
                return [ZhealthLogModel.model_validate(log) for log in logs]
        except Exception as e:
            log.error(f"Failed to get logs for user {user_id}: {e}")
            return []

    def get_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 50
    ) -> list[ZhealthLogModel]:
        """Get log entries within a date range"""
        try:
            with get_supabase_db() as db:
                logs = (
                    db.query(ZhealthLog)
                    .filter(ZhealthLog.created_at >= start_date)
                    .filter(ZhealthLog.created_at <= end_date)
                    .order_by(ZhealthLog.created_at.desc())
                    .offset(skip)
                    .limit(limit)
                    .all()
                )
                return [ZhealthLogModel.model_validate(log) for log in logs]
        except Exception as e:
            log.error(f"Failed to get logs by date range: {e}")
            return []

    def get_logs_with_errors(
        self, 
        skip: int = 0, 
        limit: int = 50
    ) -> list[ZhealthLogModel]:
        """Get all log entries that have errors"""
        try:
            with get_supabase_db() as db:
                logs = (
                    db.query(ZhealthLog)
                    .filter(ZhealthLog.error.isnot(None))
                    .order_by(ZhealthLog.created_at.desc())
                    .offset(skip)
                    .limit(limit)
                    .all()
                )
                return [ZhealthLogModel.model_validate(log) for log in logs]
        except Exception as e:
            log.error(f"Failed to get logs with errors: {e}")
            return []

    def delete_log_by_id(self, log_id: uuid.UUID) -> bool:
        """Delete a log entry by ID"""
        try:
            with get_supabase_db() as db:
                db.query(ZhealthLog).filter(ZhealthLog.id == log_id).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Failed to delete zhealth log: {e}")
            return False

    def delete_logs_by_user_id(self, user_id: str) -> bool:
        """Delete all log entries for a user"""
        try:
            with get_supabase_db() as db:
                db.query(ZhealthLog).filter(ZhealthLog.user_id == user_id).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Failed to delete logs for user {user_id}: {e}")
            return False

    def delete_old_logs(self, days: int = 90) -> bool:
        """Delete log entries older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            with get_supabase_db() as db:
                db.query(ZhealthLog).filter(ZhealthLog.created_at < cutoff_date).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Failed to delete old logs: {e}")
            return False


ZhealthLogs = ZhealthLogsTable()
