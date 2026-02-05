"""File reader tool for reading file contents."""

from typing import Any
from pathlib import Path
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class FileReaderTool(Tool):
    """Tool for reading file contents."""

    def __init__(self) -> None:
        """Initialize file reader tool."""
        metadata = ToolMetadata(
            name="file_reader",
            description="Read contents from a file",
            category=ToolCategory.FILE,
            tags=["file", "read", "io", "text"],
        )

        parameters = [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file to read",
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding (default: utf-8)",
                required=False,
                default="utf-8",
            ),
            ToolParameter(
                name="max_size",
                type="number",
                description="Maximum file size in bytes (default: 10MB)",
                required=False,
                default=10 * 1024 * 1024,  # 10MB
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self, path: str, encoding: str = "utf-8", max_size: int = 10 * 1024 * 1024
    ) -> Any:
        """Read file contents.

        Args:
            path: File path
            encoding: File encoding
            max_size: Maximum file size in bytes

        Returns:
            File contents and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large
        """
        file_path = Path(path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check if it's a file
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > max_size:
            raise ValueError(
                f"File too large: {file_size} bytes (max: {max_size} bytes)"
            )

        try:
            # Read file contents
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            logger.info(f"Read file: {path} ({file_size} bytes)")

            return {
                "path": str(file_path),
                "content": content,
                "size": file_size,
                "encoding": encoding,
                "lines": len(content.splitlines()),
            }

        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {path}: {e}")
            raise ValueError(f"Failed to decode file with encoding {encoding}: {e}")
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise
