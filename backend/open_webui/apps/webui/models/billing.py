import time
import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, ForeignKey
from open_webui.apps.webui.internal.db import Base, get_db

class MessageUsage(Base):
    __tablename__ = "message_usage"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"))
    timestamp = Column(BigInteger)  # Epoch timestamp of the message
    
class MessageUsageModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    timestamp: int

class MessageUsageTable:
    def add_message(self, user_id: str) -> Optional[MessageUsageModel]:
        """Record a new message usage"""
        with get_db() as db:
            usage = MessageUsageModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                timestamp=int(time.time())
            )
            
            result = MessageUsage(**usage.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)
            return MessageUsageModel.model_validate(result) if result else None

    def get_message_count_in_period(
        self,
        user_id: str,
        start_timestamp: int,
        end_timestamp: int
    ) -> int:
        """Get count of messages for a user within a time period"""
        with get_db() as db:
            return db.query(MessageUsage).filter(
                MessageUsage.user_id == user_id,
                MessageUsage.timestamp >= start_timestamp,
                MessageUsage.timestamp <= end_timestamp
            ).count()

# Create global instance
MessageUsages = MessageUsageTable()