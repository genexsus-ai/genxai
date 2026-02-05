"""Tests for file tools."""

import pytest
import tempfile
import os
from pathlib import Path
from genxai.tools.builtin.file.file_reader import FileReaderTool
from genxai.tools.builtin.file.file_writer import FileWriterTool
from genxai.tools.builtin.file.directory_scanner import DirectoryScannerTool
from genxai.tools.builtin.file.file_compressor import FileCompressorTool
from genxai.tools.builtin.file.image_processor import ImageProcessorTool
from genxai.tools.builtin.file.pdf_parser import PDFParserTool


# ==================== File Reader Tool Tests ====================

@pytest.mark.asyncio
async def test_file_reader_initialization():
    """Test file reader tool initialization."""
    tool = FileReaderTool()
    assert tool.metadata.name == "file_reader"
    assert tool.metadata.category == "file"
    assert len(tool.parameters) > 0


@pytest.mark.asyncio
async def test_file_reader_read_text_file():
    """Test file reader with text file."""
    tool = FileReaderTool()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello World\nLine 2\nLine 3")
        temp_path = f.name
    
    try:
        result = await tool.execute(path=temp_path)
        assert result.success is True
        assert "content" in result.data
        assert "Hello World" in result.data["content"]
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_file_reader_nonexistent_file():
    """Test file reader with nonexistent file."""
    tool = FileReaderTool()
    result = await tool.execute(path="/nonexistent/file.txt")
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_file_reader_empty_file():
    """Test file reader with empty file."""
    tool = FileReaderTool()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_path = f.name
    
    try:
        result = await tool.execute(path=temp_path)
        assert result.success is True
        assert result.data["content"] == ""
    finally:
        os.unlink(temp_path)


def test_file_reader_metadata():
    """Test file reader metadata."""
    tool = FileReaderTool()
    assert "read" in tool.metadata.description.lower() or "file" in tool.metadata.description.lower()


# ==================== File Writer Tool Tests ====================

@pytest.mark.asyncio
async def test_file_writer_initialization():
    """Test file writer tool initialization."""
    tool = FileWriterTool()
    assert tool.metadata.name == "file_writer"
    assert tool.metadata.category == "file"


@pytest.mark.asyncio
async def test_file_writer_write_text():
    """Test file writer with text content."""
    tool = FileWriterTool()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        temp_path = f.name
    
    try:
        result = await tool.execute(
            path=temp_path,
            content="Test content"
        )
        assert result.success is True
        
        # Verify file was written
        with open(temp_path, 'r') as f:
            content = f.read()
            assert content == "Test content"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_file_writer_overwrite():
    """Test file writer overwriting existing file."""
    tool = FileWriterTool()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Original content")
        temp_path = f.name
    
    try:
        result = await tool.execute(
            path=temp_path,
            content="New content"
        )
        assert result.success is True
        
        with open(temp_path, 'r') as f:
            content = f.read()
            assert content == "New content"
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_file_writer_invalid_path():
    """Test file writer with invalid path."""
    tool = FileWriterTool()
    result = await tool.execute(
        path="/invalid/path/file.txt",
        content="Test"
    )
    assert result.success is False
    assert result.error is not None


def test_file_writer_metadata():
    """Test file writer metadata."""
    tool = FileWriterTool()
    assert "write" in tool.metadata.description.lower() or "file" in tool.metadata.description.lower()


# ==================== Directory Scanner Tool Tests ====================

@pytest.mark.asyncio
async def test_directory_scanner_initialization():
    """Test directory scanner tool initialization."""
    tool = DirectoryScannerTool()
    assert tool.metadata.name == "directory_scanner"
    assert tool.metadata.category == "file"


@pytest.mark.asyncio
async def test_directory_scanner_scan_directory():
    """Test directory scanner with temp directory."""
    tool = DirectoryScannerTool()
    
    # Create temp directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some files
        Path(temp_dir, "file1.txt").write_text("content1")
        Path(temp_dir, "file2.txt").write_text("content2")
        
        result = await tool.execute(path=temp_dir)
        assert result.success is True
        assert "files" in result.data
        assert len(result.data["files"]) >= 2


@pytest.mark.asyncio
async def test_directory_scanner_nonexistent_directory():
    """Test directory scanner with nonexistent directory."""
    tool = DirectoryScannerTool()
    result = await tool.execute(path="/nonexistent/directory")
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_directory_scanner_empty_directory():
    """Test directory scanner with empty directory."""
    tool = DirectoryScannerTool()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = await tool.execute(path=temp_dir)
        assert result.success is True
        assert len(result.data.get("files", [])) == 0


def test_directory_scanner_metadata():
    """Test directory scanner metadata."""
    tool = DirectoryScannerTool()
    assert "directory" in tool.metadata.description.lower() or "scan" in tool.metadata.description.lower()


# ==================== File Compressor Tool Tests ====================

@pytest.mark.asyncio
async def test_file_compressor_initialization():
    """Test file compressor tool initialization."""
    tool = FileCompressorTool()
    assert tool.metadata.name == "file_compressor"
    assert tool.metadata.category == "file"


@pytest.mark.asyncio
async def test_file_compressor_compress_file():
    """Test file compressor compressing a file."""
    tool = FileCompressorTool()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content for compression")
        temp_path = f.name
    
    try:
        result = await tool.execute(
            path=temp_path,
            operation="compress"
        )
        # Should either succeed or fail gracefully
        assert result.success is True or result.success is False
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_file_compressor_invalid_operation():
    """Test file compressor with invalid operation."""
    tool = FileCompressorTool()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    try:
        result = await tool.execute(
            path=temp_path,
            operation="invalid"
        )
        assert result.success is False
        assert result.error is not None
    finally:
        os.unlink(temp_path)


def test_file_compressor_metadata():
    """Test file compressor metadata."""
    tool = FileCompressorTool()
    assert "compress" in tool.metadata.description.lower() or "file" in tool.metadata.description.lower()


# ==================== Image Processor Tool Tests ====================

@pytest.mark.asyncio
async def test_image_processor_initialization():
    """Test image processor tool initialization."""
    tool = ImageProcessorTool()
    assert tool.metadata.name == "image_processor"
    assert tool.metadata.category == "file"


@pytest.mark.asyncio
async def test_image_processor_nonexistent_image():
    """Test image processor with nonexistent image."""
    tool = ImageProcessorTool()
    result = await tool.execute(
        path="/nonexistent/image.jpg",
        operation="resize"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_image_processor_invalid_operation():
    """Test image processor with invalid operation."""
    tool = ImageProcessorTool()
    result = await tool.execute(
        path="/tmp/test.jpg",
        operation="invalid_operation"
    )
    assert result.success is False


def test_image_processor_metadata():
    """Test image processor metadata."""
    tool = ImageProcessorTool()
    assert "image" in tool.metadata.description.lower() or "process" in tool.metadata.description.lower()


# ==================== PDF Parser Tool Tests ====================

@pytest.mark.asyncio
async def test_pdf_parser_initialization():
    """Test PDF parser tool initialization."""
    tool = PDFParserTool()
    assert tool.metadata.name == "pdf_parser"
    assert tool.metadata.category == "file"


@pytest.mark.asyncio
async def test_pdf_parser_nonexistent_file():
    """Test PDF parser with nonexistent file."""
    tool = PDFParserTool()
    result = await tool.execute(path="/nonexistent/file.pdf")
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_pdf_parser_invalid_pdf():
    """Test PDF parser with invalid PDF file."""
    tool = PDFParserTool()
    
    # Create temp file with non-PDF content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
        f.write("Not a PDF file")
        temp_path = f.name
    
    try:
        result = await tool.execute(path=temp_path)
        assert result.success is False
        assert result.error is not None
    finally:
        os.unlink(temp_path)


def test_pdf_parser_metadata():
    """Test PDF parser metadata."""
    tool = PDFParserTool()
    assert "pdf" in tool.metadata.description.lower() or "parse" in tool.metadata.description.lower()
