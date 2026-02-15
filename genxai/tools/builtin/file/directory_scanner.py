"""Directory scanner tool for scanning and analyzing directory structures."""

from typing import Any, Dict, List
import logging
import os
from pathlib import Path

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class DirectoryScannerTool(Tool):
    """Scan directories and analyze file structures."""

    def __init__(self) -> None:
        """Initialize directory scanner tool."""
        metadata = ToolMetadata(
            name="directory_scanner",
            description="Scan directories, list files, and analyze directory structures",
            category=ToolCategory.FILE,
            tags=["directory", "scan", "files", "structure", "analysis"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="path",
                type="string",
                description="Path to directory to scan",
                required=True,
            ),
            ToolParameter(
                name="recursive",
                type="boolean",
                description="Whether to scan recursively",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="include_hidden",
                type="boolean",
                description="Whether to include hidden files",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="file_pattern",
                type="string",
                description="File pattern to match (e.g., '*.py', '*.txt')",
                required=False,
                pattern=r"^\*?\.\w+$",
            ),
            ToolParameter(
                name="max_depth",
                type="number",
                description="Maximum depth for recursive scan",
                required=False,
                default=10,
                min_value=1,
                max_value=50,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        path: str,
        recursive: bool = True,
        include_hidden: bool = False,
        file_pattern: str = None,
        max_depth: int = 10,
    ) -> Dict[str, Any]:
        """Execute directory scanning.

        Args:
            directory_path: Directory to scan
            recursive: Recursive scan flag
            include_hidden: Include hidden files flag
            file_pattern: File pattern to match
            max_depth: Maximum depth

        Returns:
            Dictionary containing scan results
        """
        result: Dict[str, Any] = {
            "path": path,
            "success": False,
        }

        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Directory not found: {path}")

            if not os.path.isdir(path):
                raise ValueError(f"Path is not a directory: {path}")

            # Scan directory
            files = []
            directories = []
            total_size = 0

            if recursive:
                for root, dirs, filenames in os.walk(path):
                    # Calculate depth
                    depth = root[len(path):].count(os.sep)
                    if depth >= max_depth:
                        dirs.clear()  # Don't recurse deeper
                        continue

                    # Filter hidden directories
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]

                    # Process directories
                    for dirname in dirs:
                        dir_path = os.path.join(root, dirname)
                        directories.append({
                            "name": dirname,
                            "path": dir_path,
                            "relative_path": os.path.relpath(dir_path, path),
                            "depth": depth + 1,
                        })

                    # Process files
                    for filename in filenames:
                        # Filter hidden files
                        if not include_hidden and filename.startswith('.'):
                            continue

                        # Filter by pattern
                        if file_pattern:
                            if not Path(filename).match(file_pattern):
                                continue

                        file_path = os.path.join(root, filename)
                        file_stat = os.stat(file_path)
                        file_size = file_stat.st_size
                        total_size += file_size

                        files.append({
                            "name": filename,
                            "path": file_path,
                            "relative_path": os.path.relpath(file_path, path),
                            "size": file_size,
                            "extension": Path(filename).suffix,
                            "modified_time": file_stat.st_mtime,
                            "depth": depth,
                        })
            else:
                # Non-recursive scan
                for item in os.listdir(path):
                    # Filter hidden items
                    if not include_hidden and item.startswith('.'):
                        continue

                    item_path = os.path.join(path, item)

                    if os.path.isdir(item_path):
                        directories.append({
                            "name": item,
                            "path": item_path,
                            "relative_path": item,
                            "depth": 0,
                        })
                    else:
                        # Filter by pattern
                        if file_pattern and not Path(item).match(file_pattern):
                            continue

                        file_stat = os.stat(item_path)
                        file_size = file_stat.st_size
                        total_size += file_size

                        files.append({
                            "name": item,
                            "path": item_path,
                            "relative_path": item,
                            "size": file_size,
                            "extension": Path(item).suffix,
                            "modified_time": file_stat.st_mtime,
                            "depth": 0,
                        })

            # Calculate statistics
            file_types = {}
            for file in files:
                ext = file["extension"] or "no_extension"
                if ext not in file_types:
                    file_types[ext] = {"count": 0, "total_size": 0}
                file_types[ext]["count"] += 1
                file_types[ext]["total_size"] += file["size"]

            result.update({
                "files": files,
                "directories": directories,
                "file_count": len(files),
                "directory_count": len(directories),
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "success": True,
            })

        except FileNotFoundError as e:
            result["error"] = str(e)
        except PermissionError:
            result["error"] = f"Permission denied: {path}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Directory scan completed: success={result['success']}")
        return result
