"""Database inspector tool for examining database schemas."""

from typing import Any, Dict, List
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class DatabaseInspectorTool(Tool):
    """Inspect database schemas, tables, and metadata."""

    def __init__(self) -> None:
        """Initialize database inspector tool."""
        metadata = ToolMetadata(
            name="database_inspector",
            description="Inspect database schemas, tables, columns, and indexes",
            category=ToolCategory.DATABASE,
            tags=["database", "schema", "inspect", "metadata", "tables"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="connection_string",
                type="string",
                description="Database connection string",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="Inspection operation",
                required=True,
                enum=["list_tables", "describe_table", "list_indexes", "database_info"],
            ),
            ToolParameter(
                name="table_name",
                type="string",
                description="Table name (for describe_table and list_indexes)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        connection_string: str,
        operation: str,
        table_name: str = None,
    ) -> Dict[str, Any]:
        """Execute database inspection.

        Args:
            connection_string: Database connection string
            operation: Inspection operation
            table_name: Table name

        Returns:
            Dictionary containing inspection results
        """
        engine = None
        try:
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.exc import SQLAlchemyError
        except ImportError:
            raise ImportError(
                "sqlalchemy package not installed. Install with: pip install sqlalchemy"
            )

        result: Dict[str, Any] = {
            "operation": operation,
            "success": False,
        }

        try:
            # Create engine and inspector
            engine = create_engine(connection_string)
            inspector = inspect(engine)

            if operation == "list_tables":
                tables = inspector.get_table_names()
                result.update({
                    "tables": tables,
                    "count": len(tables),
                    "success": True,
                })

            elif operation == "describe_table":
                if not table_name:
                    raise ValueError("table_name required for describe_table operation")
                
                columns = inspector.get_columns(table_name)
                column_info = [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default")) if col.get("default") else None,
                        "primary_key": col.get("primary_key", False),
                    }
                    for col in columns
                ]
                
                result.update({
                    "table": table_name,
                    "columns": column_info,
                    "column_count": len(column_info),
                    "success": True,
                })

            elif operation == "list_indexes":
                if not table_name:
                    raise ValueError("table_name required for list_indexes operation")
                
                indexes = inspector.get_indexes(table_name)
                index_info = [
                    {
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx.get("unique", False),
                    }
                    for idx in indexes
                ]
                
                result.update({
                    "table": table_name,
                    "indexes": index_info,
                    "index_count": len(index_info),
                    "success": True,
                })

            elif operation == "database_info":
                tables = inspector.get_table_names()
                views = inspector.get_view_names()
                
                result.update({
                    "tables": tables,
                    "table_count": len(tables),
                    "views": views,
                    "view_count": len(views),
                    "dialect": engine.dialect.name,
                    "success": True,
                })

        except SQLAlchemyError as e:
            result["error"] = f"Database error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)
        finally:
            if engine is not None:
                engine.dispose()

        logger.info(f"Database inspection ({operation}) completed: success={result['success']}")
        return result
