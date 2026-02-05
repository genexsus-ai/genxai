"""Service for tool persistence and management."""

import os
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

from genxai.tools.persistence.models import Base, ToolModel
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory
from genxai.tools.registry import ToolRegistry
from genxai.tools.dynamic import DynamicTool
from genxai.tools.templates import create_tool_from_template

logger = logging.getLogger(__name__)

# Database setup - now in genxai/data/
DB_PATH = Path(__file__).parent.parent.parent / "data" / "tools.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


class ToolService:
    """Service for managing tool persistence."""
    
    @staticmethod
    def get_db() -> Session:
        """Get database session."""
        db = SessionLocal()
        try:
            return db
        finally:
            pass
    
    @staticmethod
    def save_tool(
        name: str,
        description: str,
        category: str,
        tags: List[str],
        version: str,
        author: str,
        tool_type: str,
        code: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        template_name: Optional[str] = None,
        template_config: Optional[Dict[str, Any]] = None,
    ) -> ToolModel:
        """Save tool to database.
        
        Args:
            name: Tool name
            description: Tool description
            category: Tool category
            tags: Tool tags
            version: Tool version
            author: Tool author
            tool_type: "code_based" or "template_based"
            code: Python code (for code-based tools)
            parameters: Tool parameters (for code-based tools)
            template_name: Template name (for template-based tools)
            template_config: Template configuration (for template-based tools)
            
        Returns:
            Created ToolModel instance
        """
        db = SessionLocal()
        try:
            tool_model = ToolModel(
                name=name,
                description=description,
                category=category,
                tags=tags,
                version=version,
                author=author,
                tool_type=tool_type,
                code=code,
                parameters=parameters or [],
                template_name=template_name,
                template_config=template_config,
            )
            
            db.add(tool_model)
            db.commit()
            db.refresh(tool_model)
            
            logger.info(f"Saved tool to database: {name}")
            
            # Optionally export to file
            # ToolService._export_to_file(tool_model)
            
            return tool_model
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save tool: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_tool(name: str) -> Optional[ToolModel]:
        """Get tool from database by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolModel instance or None
        """
        db = SessionLocal()
        try:
            return db.query(ToolModel).filter(ToolModel.name == name).first()
        finally:
            db.close()
    
    @staticmethod
    def list_tools() -> List[ToolModel]:
        """List all tools from database.
        
        Returns:
            List of ToolModel instances
        """
        db = SessionLocal()
        try:
            return db.query(ToolModel).all()
        finally:
            db.close()
    
    @staticmethod
    def update_tool_code(name: str, code: str) -> bool:
        """Update tool code in database.
        
        Args:
            name: Tool name
            code: New Python code
            
        Returns:
            True if updated, False if not found
        """
        db = SessionLocal()
        try:
            tool = db.query(ToolModel).filter(ToolModel.name == name).first()
            if tool and tool.tool_type == "code_based":
                tool.code = code
                db.commit()
                logger.info(f"Updated tool code in database: {name}")
                
                # Update file if exists
                # ToolService._export_to_file(tool)
                
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update tool code: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def delete_tool(name: str) -> bool:
        """Delete tool from database.
        
        Args:
            name: Tool name
            
        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            tool = db.query(ToolModel).filter(ToolModel.name == name).first()
            if tool:
                db.delete(tool)
                db.commit()
                logger.info(f"Deleted tool from database: {name}")
                
                # Delete file if exists
                # ToolService._delete_file(name)
                
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete tool: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def load_tool_to_registry(tool_model: ToolModel) -> Tool:
        """Load tool from database model to registry.
        
        Args:
            tool_model: ToolModel instance
            
        Returns:
            Tool instance
        """
        try:
            category = ToolCategory(tool_model.category)
            
            if tool_model.tool_type == "code_based":
                # Create code-based tool
                metadata = ToolMetadata(
                    name=tool_model.name,
                    description=tool_model.description,
                    category=category,
                    tags=tool_model.tags,
                    version=tool_model.version,
                    author=tool_model.author,
                )
                
                parameters = [
                    ToolParameter(
                        name=p["name"],
                        type=p["type"],
                        description=p["description"],
                        required=p.get("required", True),
                        default=p.get("default"),
                        enum=p.get("enum"),
                        min_value=p.get("min_value"),
                        max_value=p.get("max_value"),
                        pattern=p.get("pattern"),
                    )
                    for p in tool_model.parameters
                ]
                
                tool = DynamicTool(metadata, parameters, tool_model.code)
                
            elif tool_model.tool_type == "template_based":
                # Create template-based tool
                tool = create_tool_from_template(
                    name=tool_model.name,
                    description=tool_model.description,
                    category=category,
                    tags=tool_model.tags,
                    template=tool_model.template_name,
                    config=tool_model.template_config or {},
                )
            else:
                raise ValueError(f"Unknown tool type: {tool_model.tool_type}")
            
            # Register in registry
            ToolRegistry.register(tool)
            logger.info(f"Loaded tool to registry: {tool_model.name}")
            
            return tool
            
        except Exception as e:
            logger.error(f"Failed to load tool {tool_model.name}: {e}")
            raise
    
    @staticmethod
    def load_all_tools():
        """Load all tools from database to registry."""
        tools = ToolService.list_tools()
        loaded_count = 0
        
        for tool_model in tools:
            try:
                ToolService.load_tool_to_registry(tool_model)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load tool {tool_model.name}: {e}")
        
        logger.info(f"Loaded {loaded_count}/{len(tools)} tools from database")
    
    @staticmethod
    def _export_to_file(tool_model: ToolModel):
        """Export tool to file system (optional backup).
        
        Args:
            tool_model: ToolModel instance
        """
        try:
            custom_dir = Path(__file__).parent.parent / "custom"
            custom_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = custom_dir / f"{tool_model.name}.py"
            
            if tool_model.tool_type == "code_based":
                content = f'''"""
Auto-generated tool: {tool_model.name}
Description: {tool_model.description}
Category: {tool_model.category}
Created: {tool_model.created_at}
"""

# Tool code
{tool_model.code}
'''
                file_path.write_text(content)
                logger.info(f"Exported tool to file: {file_path}")
                
        except Exception as e:
            logger.warning(f"Failed to export tool to file: {e}")
    
    @staticmethod
    def _delete_file(name: str):
        """Delete tool file if exists.
        
        Args:
            name: Tool name
        """
        try:
            custom_dir = Path(__file__).parent.parent / "custom"
            file_path = custom_dir / f"{name}.py"
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted tool file: {file_path}")
                
        except Exception as e:
            logger.warning(f"Failed to delete tool file: {e}")
