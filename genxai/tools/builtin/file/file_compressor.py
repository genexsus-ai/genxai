"""File compressor tool for compressing and decompressing files."""

from typing import Any, Dict, List, Optional
import logging
import os
import zipfile
import tarfile
import gzip
import shutil

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class FileCompressorTool(Tool):
    """Compress and decompress files using various formats (ZIP, TAR, GZIP)."""

    def __init__(self) -> None:
        """Initialize file compressor tool."""
        metadata = ToolMetadata(
            name="file_compressor",
            description="Compress and decompress files and directories using ZIP, TAR, or GZIP",
            category=ToolCategory.FILE,
            tags=["compression", "zip", "tar", "gzip", "archive"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=True,
                enum=["compress", "decompress", "list"],
            ),
            ToolParameter(
                name="source_path",
                type="string",
                description="Source file or directory path",
                required=True,
            ),
            ToolParameter(
                name="output_path",
                type="string",
                description="Output archive path (for compress) or extraction directory (for decompress)",
                required=False,
            ),
            ToolParameter(
                name="format",
                type="string",
                description="Compression format",
                required=False,
                default="zip",
                enum=["zip", "tar", "tar.gz", "gzip"],
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        operation: str,
        source_path: str,
        output_path: Optional[str] = None,
        format: str = "zip",
    ) -> Dict[str, Any]:
        """Execute file compression/decompression.

        Args:
            operation: Operation to perform
            source_path: Source path
            output_path: Output path
            format: Compression format

        Returns:
            Dictionary containing operation results
        """
        result: Dict[str, Any] = {
            "operation": operation,
            "format": format,
            "success": False,
        }

        try:
            if operation == "compress":
                if not output_path:
                    raise ValueError("output_path required for compress operation")

                if format == "zip":
                    result.update(self._compress_zip(source_path, output_path))
                elif format in ["tar", "tar.gz"]:
                    result.update(self._compress_tar(source_path, output_path, format))
                elif format == "gzip":
                    result.update(self._compress_gzip(source_path, output_path))

            elif operation == "decompress":
                if not output_path:
                    raise ValueError("output_path required for decompress operation")

                if format == "zip":
                    result.update(self._decompress_zip(source_path, output_path))
                elif format in ["tar", "tar.gz"]:
                    result.update(self._decompress_tar(source_path, output_path))
                elif format == "gzip":
                    result.update(self._decompress_gzip(source_path, output_path))

            elif operation == "list":
                if format == "zip":
                    result.update(self._list_zip(source_path))
                elif format in ["tar", "tar.gz"]:
                    result.update(self._list_tar(source_path))

            result["success"] = True

        except FileNotFoundError:
            result["error"] = f"File not found: {source_path}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"File {operation} ({format}) completed: success={result['success']}")
        return result

    def _compress_zip(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """Compress to ZIP format."""
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isfile(source_path):
                zipf.write(source_path, os.path.basename(source_path))
                file_count = 1
            else:
                file_count = 0
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_path)
                        zipf.write(file_path, arcname)
                        file_count += 1

        return {
            "output_path": output_path,
            "file_count": file_count,
            "compressed_size": os.path.getsize(output_path),
        }

    def _compress_tar(self, source_path: str, output_path: str, format: str) -> Dict[str, Any]:
        """Compress to TAR format."""
        mode = "w:gz" if format == "tar.gz" else "w"
        
        with tarfile.open(output_path, mode) as tar:
            tar.add(source_path, arcname=os.path.basename(source_path))

        return {
            "output_path": output_path,
            "compressed_size": os.path.getsize(output_path),
        }

    def _compress_gzip(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """Compress to GZIP format."""
        with open(source_path, "rb") as f_in:
            with gzip.open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        return {
            "output_path": output_path,
            "original_size": os.path.getsize(source_path),
            "compressed_size": os.path.getsize(output_path),
            "compression_ratio": round(
                os.path.getsize(output_path) / os.path.getsize(source_path), 2
            ),
        }

    def _decompress_zip(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """Decompress ZIP format."""
        with zipfile.ZipFile(source_path, "r") as zipf:
            zipf.extractall(output_path)
            file_count = len(zipf.namelist())

        return {
            "output_path": output_path,
            "file_count": file_count,
        }

    def _decompress_tar(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """Decompress TAR format."""
        with tarfile.open(source_path, "r:*") as tar:
            tar.extractall(output_path)
            file_count = len(tar.getmembers())

        return {
            "output_path": output_path,
            "file_count": file_count,
        }

    def _decompress_gzip(self, source_path: str, output_path: str) -> Dict[str, Any]:
        """Decompress GZIP format."""
        with gzip.open(source_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        return {
            "output_path": output_path,
            "decompressed_size": os.path.getsize(output_path),
        }

    def _list_zip(self, source_path: str) -> Dict[str, Any]:
        """List contents of ZIP archive."""
        with zipfile.ZipFile(source_path, "r") as zipf:
            files = [
                {
                    "name": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                }
                for info in zipf.filelist
            ]

        return {
            "file_count": len(files),
            "files": files,
        }

    def _list_tar(self, source_path: str) -> Dict[str, Any]:
        """List contents of TAR archive."""
        with tarfile.open(source_path, "r:*") as tar:
            files = [
                {
                    "name": member.name,
                    "size": member.size,
                    "type": "directory" if member.isdir() else "file",
                }
                for member in tar.getmembers()
            ]

        return {
            "file_count": len(files),
            "files": files,
        }
