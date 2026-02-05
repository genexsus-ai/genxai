"""Image processor tool for analyzing and manipulating images."""

from typing import Any, Dict, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class ImageProcessorTool(Tool):
    """Process and analyze images (resize, format conversion, metadata extraction)."""

    def __init__(self) -> None:
        """Initialize image processor tool."""
        metadata = ToolMetadata(
            name="image_processor",
            description="Analyze image properties, resize, convert formats, and extract metadata",
            category=ToolCategory.FILE,
            tags=["image", "processing", "resize", "convert", "metadata"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to image file",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=True,
                enum=["analyze", "resize", "convert", "thumbnail"],
            ),
            ToolParameter(
                name="width",
                type="number",
                description="Target width (for resize/thumbnail)",
                required=False,
            ),
            ToolParameter(
                name="height",
                type="number",
                description="Target height (for resize/thumbnail)",
                required=False,
            ),
            ToolParameter(
                name="output_format",
                type="string",
                description="Output format (for convert)",
                required=False,
                enum=["JPEG", "PNG", "GIF", "BMP", "WEBP"],
            ),
            ToolParameter(
                name="output_path",
                type="string",
                description="Output file path (for resize/convert/thumbnail)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        file_path: str,
        operation: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        output_format: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute image processing.

        Args:
            file_path: Path to image file
            operation: Operation to perform
            width: Target width
            height: Target height
            output_format: Output format
            output_path: Output file path

        Returns:
            Dictionary containing processing results
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError(
                "Pillow package not installed. Install with: pip install Pillow"
            )

        result: Dict[str, Any] = {
            "file_path": file_path,
            "operation": operation,
            "success": False,
        }

        try:
            # Open image
            img = Image.open(file_path)

            if operation == "analyze":
                # Extract image information
                result.update({
                    "format": img.format,
                    "mode": img.mode,
                    "size": {"width": img.width, "height": img.height},
                    "aspect_ratio": round(img.width / img.height, 2),
                })

                # Extract EXIF data if available
                if hasattr(img, "_getexif") and img._getexif():
                    exif_data = img._getexif()
                    result["exif"] = {k: str(v) for k, v in exif_data.items() if v}

                result["success"] = True

            elif operation == "resize":
                if not width or not height:
                    raise ValueError("width and height required for resize operation")
                
                if not output_path:
                    raise ValueError("output_path required for resize operation")

                # Resize image
                resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
                resized_img.save(output_path)

                result.update({
                    "original_size": {"width": img.width, "height": img.height},
                    "new_size": {"width": width, "height": height},
                    "output_path": output_path,
                    "success": True,
                })

            elif operation == "convert":
                if not output_format:
                    raise ValueError("output_format required for convert operation")
                
                if not output_path:
                    raise ValueError("output_path required for convert operation")

                # Convert format
                if img.mode == "RGBA" and output_format == "JPEG":
                    # Convert RGBA to RGB for JPEG
                    img = img.convert("RGB")

                img.save(output_path, format=output_format)

                result.update({
                    "original_format": img.format,
                    "new_format": output_format,
                    "output_path": output_path,
                    "success": True,
                })

            elif operation == "thumbnail":
                if not width or not height:
                    raise ValueError("width and height required for thumbnail operation")
                
                if not output_path:
                    raise ValueError("output_path required for thumbnail operation")

                # Create thumbnail (maintains aspect ratio)
                img_copy = img.copy()
                img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                img_copy.save(output_path)

                result.update({
                    "original_size": {"width": img.width, "height": img.height},
                    "thumbnail_size": {"width": img_copy.width, "height": img_copy.height},
                    "output_path": output_path,
                    "success": True,
                })

        except FileNotFoundError:
            result["error"] = f"File not found: {file_path}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Image {operation} completed: success={result['success']}")
        return result
