"""File writer tool for writing content to files."""

from typing import Any, Dict
import logging
import os

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class FileWriterTool(Tool):
    """Write content to files with various encoding options."""

    def __init__(self) -> None:
        """Initialize file writer tool."""
        metadata = ToolMetadata(
            name="file_writer",
            description="Write text content to files with encoding support",
            category=ToolCategory.FILE,
            tags=["file", "write", "io", "save", "output"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="path",
                type="string",
                description="Path where file should be written",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write to file",
                required=True,
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding",
                required=False,
                default="utf-8",
                enum=["utf-8", "ascii", "latin-1", "utf-16"],
            ),
            ToolParameter(
                name="mode",
                type="string",
                description="Write mode",
                required=False,
                default="write",
                enum=["write", "append"],
            ),
            ToolParameter(
                name="create_dirs",
                type="boolean",
                description="Create parent directories if they don't exist",
                required=False,
                default=True,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        mode: str = "write",
        create_dirs: bool = True,
    ) -> Dict[str, Any]:
        """Execute file writing.

        Args:
            file_path: Path to write file
            content: Content to write
            encoding: File encoding
            mode: Write mode (write or append)
            create_dirs: Create directories flag

        Returns:
            Dictionary containing write results
        """
        result: Dict[str, Any] = {
            "path": path,
            "success": False,
        }

        try:
            # Create parent directories if needed
            if create_dirs:
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                    result["created_directories"] = True

            # Determine write mode
            write_mode = "w" if mode == "write" else "a"

            # Write file
            with open(path, write_mode, encoding=encoding) as f:
                f.write(content)

            # Get file info
            file_size = os.path.getsize(path)
            
            result.update({
                "success": True,
                "bytes_written": len(content.encode(encoding)),
                "file_size": file_size,
                "encoding": encoding,
                "mode": mode,
            })

        except PermissionError:
            result["error"] = f"Permission denied: {path}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"File write completed: success={result['success']}")
        return result
