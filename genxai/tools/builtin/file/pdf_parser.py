"""PDF parser tool for extracting text and metadata from PDF files."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class PDFParserTool(Tool):
    """Extract text, metadata, and structure from PDF documents."""

    def __init__(self) -> None:
        """Initialize PDF parser tool."""
        metadata = ToolMetadata(
            name="pdf_parser",
            description="Extract text, metadata, and structure from PDF files",
            category=ToolCategory.FILE,
            tags=["pdf", "parser", "document", "extraction", "text"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to PDF file",
                required=True,
            ),
            ToolParameter(
                name="extract_text",
                type="boolean",
                description="Whether to extract text content",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="extract_metadata",
                type="boolean",
                description="Whether to extract PDF metadata",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="page_range",
                type="string",
                description="Page range to extract (e.g., '1-5' or 'all')",
                required=False,
                default="all",
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        file_path: str,
        extract_text: bool = True,
        extract_metadata: bool = True,
        page_range: str = "all",
    ) -> Dict[str, Any]:
        """Execute PDF parsing.

        Args:
            file_path: Path to PDF file
            extract_text: Extract text flag
            extract_metadata: Extract metadata flag
            page_range: Page range to extract

        Returns:
            Dictionary containing extracted data
        """
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 package not installed. Install with: pip install PyPDF2"
            )

        result: Dict[str, Any] = {
            "file_path": file_path,
            "success": False,
        }

        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Get page count
                num_pages = len(pdf_reader.pages)
                result["page_count"] = num_pages

                # Extract metadata
                if extract_metadata:
                    metadata = pdf_reader.metadata
                    if metadata:
                        result["metadata"] = {
                            "title": metadata.get("/Title", ""),
                            "author": metadata.get("/Author", ""),
                            "subject": metadata.get("/Subject", ""),
                            "creator": metadata.get("/Creator", ""),
                            "producer": metadata.get("/Producer", ""),
                            "creation_date": str(metadata.get("/CreationDate", "")),
                            "modification_date": str(metadata.get("/ModDate", "")),
                        }

                # Determine pages to extract
                if page_range == "all":
                    pages_to_extract = range(num_pages)
                else:
                    # Parse page range (e.g., "1-5")
                    if "-" in page_range:
                        start, end = page_range.split("-")
                        pages_to_extract = range(int(start) - 1, min(int(end), num_pages))
                    else:
                        page_num = int(page_range) - 1
                        pages_to_extract = [page_num] if 0 <= page_num < num_pages else []

                # Extract text
                if extract_text:
                    pages_text = []
                    for page_num in pages_to_extract:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        pages_text.append({
                            "page_number": page_num + 1,
                            "text": text,
                            "char_count": len(text),
                        })
                    
                    result["pages"] = pages_text
                    result["total_text"] = "\n\n".join([p["text"] for p in pages_text])
                    result["extracted_pages"] = len(pages_text)

                result["success"] = True

        except FileNotFoundError:
            result["error"] = f"File not found: {file_path}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"PDF parsing completed: success={result['success']}")
        return result
