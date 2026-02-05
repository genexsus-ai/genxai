"""Database models for tools."""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class ToolModel(Base):
    """Database model for tools."""
    
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    tags = Column(JSON, default=[])
    version = Column(String, default="1.0.0")
    author = Column(String, default="GenXAI User")
    
    # Tool type: "code_based" or "template_based"
    tool_type = Column(String, nullable=False)
    
    # For code-based tools
    code = Column(Text, nullable=True)
    parameters = Column(JSON, default=[])
    
    # For template-based tools
    template_name = Column(String, nullable=True)
    template_config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "tool_type": self.tool_type,
            "code": self.code,
            "parameters": self.parameters,
            "template_name": self.template_name,
            "template_config": self.template_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
