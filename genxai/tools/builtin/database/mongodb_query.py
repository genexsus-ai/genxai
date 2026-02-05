"""MongoDB query tool for NoSQL database operations."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class MongoDBQueryTool(Tool):
    """Query and manipulate MongoDB collections."""

    def __init__(self) -> None:
        """Initialize MongoDB query tool."""
        metadata = ToolMetadata(
            name="mongodb_query",
            description="Query MongoDB collections with find, insert, update, delete operations",
            category=ToolCategory.DATABASE,
            tags=["mongodb", "nosql", "database", "query", "document"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="operation",
                type="string",
                description="MongoDB operation",
                required=True,
                enum=["find", "find_one", "insert", "update", "delete", "count"],
            ),
            ToolParameter(
                name="connection_string",
                type="string",
                description="MongoDB connection string",
                required=True,
            ),
            ToolParameter(
                name="database",
                type="string",
                description="Database name",
                required=True,
            ),
            ToolParameter(
                name="collection",
                type="string",
                description="Collection name",
                required=True,
            ),
            ToolParameter(
                name="filter",
                type="object",
                description="Query filter (for find, update, delete, count)",
                required=False,
            ),
            ToolParameter(
                name="document",
                type="object",
                description="Document to insert or update data",
                required=False,
            ),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum number of documents to return",
                required=False,
                default=100,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        operation: str,
        connection_string: str,
        database: str,
        collection: str,
        filter: Optional[Dict[str, Any]] = None,
        document: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Execute MongoDB operation.

        Args:
            operation: Operation to perform
            connection_string: MongoDB connection string
            database: Database name
            collection: Collection name
            filter: Query filter
            document: Document data
            limit: Result limit

        Returns:
            Dictionary containing operation results
        """
        try:
            from pymongo import MongoClient
            from pymongo.errors import PyMongoError
        except ImportError:
            raise ImportError(
                "pymongo package not installed. Install with: pip install pymongo"
            )

        result: Dict[str, Any] = {
            "operation": operation,
            "database": database,
            "collection": collection,
            "success": False,
        }

        try:
            # Connect to MongoDB
            client = MongoClient(connection_string)
            db = client[database]
            coll = db[collection]

            if operation == "find":
                query_filter = filter or {}
                cursor = coll.find(query_filter).limit(limit)
                documents = list(cursor)
                
                # Convert ObjectId to string
                for doc in documents:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                
                result.update({
                    "documents": documents,
                    "count": len(documents),
                    "success": True,
                })

            elif operation == "find_one":
                query_filter = filter or {}
                doc = coll.find_one(query_filter)
                
                if doc and "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                
                result.update({
                    "document": doc,
                    "found": doc is not None,
                    "success": True,
                })

            elif operation == "insert":
                if not document:
                    raise ValueError("document parameter required for insert operation")
                
                insert_result = coll.insert_one(document)
                result.update({
                    "inserted_id": str(insert_result.inserted_id),
                    "success": True,
                })

            elif operation == "update":
                if not filter:
                    raise ValueError("filter parameter required for update operation")
                if not document:
                    raise ValueError("document parameter required for update operation")
                
                update_result = coll.update_many(filter, {"$set": document})
                result.update({
                    "matched_count": update_result.matched_count,
                    "modified_count": update_result.modified_count,
                    "success": True,
                })

            elif operation == "delete":
                if not filter:
                    raise ValueError("filter parameter required for delete operation")
                
                delete_result = coll.delete_many(filter)
                result.update({
                    "deleted_count": delete_result.deleted_count,
                    "success": True,
                })

            elif operation == "count":
                query_filter = filter or {}
                count = coll.count_documents(query_filter)
                result.update({
                    "count": count,
                    "success": True,
                })

            client.close()

        except PyMongoError as e:
            result["error"] = f"MongoDB error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"MongoDB {operation} completed: success={result['success']}")
        return result
