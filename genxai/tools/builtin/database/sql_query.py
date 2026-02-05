"""SQL query tool for executing database queries."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class SQLQueryTool(Tool):
    """Execute SQL queries on databases with safety controls."""

    def __init__(self) -> None:
        """Initialize SQL query tool."""
        metadata = ToolMetadata(
            name="sql_query",
            description="Execute SQL queries on databases (PostgreSQL, MySQL, SQLite)",
            category=ToolCategory.DATABASE,
            tags=["sql", "database", "query", "postgres", "mysql", "sqlite"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="query",
                type="string",
                description="SQL query to execute",
                required=True,
            ),
            ToolParameter(
                name="connection_string",
                type="string",
                description="Database connection string (e.g., postgresql://user:pass@host/db)",
                required=True,
            ),
            ToolParameter(
                name="read_only",
                type="boolean",
                description="Restrict to read-only queries (SELECT only)",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="max_rows",
                type="number",
                description="Maximum number of rows to return",
                required=False,
                default=1000,
                min_value=1,
                max_value=10000,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        query: str,
        connection_string: str,
        read_only: bool = True,
        max_rows: int = 1000,
    ) -> Dict[str, Any]:
        """Execute SQL query.

        Args:
            query: SQL query
            connection_string: Database connection string
            read_only: Read-only mode flag
            max_rows: Maximum rows to return

        Returns:
            Dictionary containing query results
        """
        engine = None
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.exc import SQLAlchemyError
        except ImportError:
            raise ImportError(
                "sqlalchemy package not installed. Install with: pip install sqlalchemy"
            )

        result: Dict[str, Any] = {
            "query": query,
            "read_only": read_only,
            "success": False,
        }

        try:
            # Validate read-only mode
            if read_only:
                query_upper = query.strip().upper()
                if not query_upper.startswith("SELECT"):
                    raise ValueError(
                        "Only SELECT queries allowed in read-only mode"
                    )
                # Check for dangerous keywords
                dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
                if any(keyword in query_upper for keyword in dangerous_keywords):
                    raise ValueError(
                        f"Query contains forbidden keywords in read-only mode"
                    )

            # Create engine
            engine = create_engine(connection_string)

            # Execute query
            with engine.connect() as connection:
                query_result = connection.execute(text(query))
                
                # Fetch results for SELECT queries
                if query_upper.startswith("SELECT"):
                    rows = query_result.fetchmany(max_rows)
                    columns = list(query_result.keys())
                    
                    # Convert to list of dictionaries
                    data = [dict(zip(columns, row)) for row in rows]
                    
                    result.update({
                        "data": data,
                        "columns": columns,
                        "row_count": len(data),
                        "truncated": len(data) == max_rows,
                    })
                else:
                    # For non-SELECT queries
                    result.update({
                        "rows_affected": query_result.rowcount,
                    })
                
                result["success"] = True

        except SQLAlchemyError as e:
            result["error"] = f"Database error: {str(e)}"
        except ValueError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        finally:
            if engine is not None:
                engine.dispose()

        logger.info(f"SQL query executed: success={result['success']}")
        return result
