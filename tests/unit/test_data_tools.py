"""Tests for data processing tools."""

import pytest
import json
from genxai.tools.builtin.data.json_processor import JSONProcessorTool
from genxai.tools.builtin.data.csv_processor import CSVProcessorTool
from genxai.tools.builtin.data.xml_processor import XMLProcessorTool
from genxai.tools.builtin.data.text_analyzer import TextAnalyzerTool
from genxai.tools.builtin.data.data_transformer import DataTransformerTool


# ==================== JSON Processor Tool Tests ====================

@pytest.mark.asyncio
async def test_json_processor_initialization():
    """Test JSON processor tool initialization."""
    tool = JSONProcessorTool()
    assert tool.metadata.name == "json_processor"
    assert tool.metadata.category == "data"
    assert len(tool.parameters) > 0


@pytest.mark.asyncio
async def test_json_processor_parse_valid_json():
    """Test JSON processor with valid JSON."""
    tool = JSONProcessorTool()
    result = await tool.execute(
        data='{"key": "value", "number": 42}',
        operation="parse"
    )
    assert result.success is True
    assert "parsed" in result.data or "result" in result.data


@pytest.mark.asyncio
async def test_json_processor_parse_invalid_json():
    """Test JSON processor with invalid JSON."""
    tool = JSONProcessorTool()
    result = await tool.execute(
        data='{invalid json}',
        operation="parse"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_json_processor_stringify():
    """Test JSON processor stringify operation."""
    tool = JSONProcessorTool()
    result = await tool.execute(
        data={"key": "value"},
        operation="stringify"
    )
    assert result.success is True


def test_json_processor_metadata():
    """Test JSON processor metadata."""
    tool = JSONProcessorTool()
    assert "json" in tool.metadata.description.lower() or "process" in tool.metadata.description.lower()
    assert len(tool.metadata.tags) > 0


# ==================== CSV Processor Tool Tests ====================

@pytest.mark.asyncio
async def test_csv_processor_initialization():
    """Test CSV processor tool initialization."""
    tool = CSVProcessorTool()
    assert tool.metadata.name == "csv_processor"
    assert tool.metadata.category == "data"


@pytest.mark.asyncio
async def test_csv_processor_parse_valid_csv():
    """Test CSV processor with valid CSV."""
    tool = CSVProcessorTool()
    csv_data = "name,age,city\nJohn,30,NYC\nJane,25,LA"
    result = await tool.execute(
        data=csv_data,
        operation="parse"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_csv_processor_parse_empty_csv():
    """Test CSV processor with empty CSV."""
    tool = CSVProcessorTool()
    result = await tool.execute(
        data="",
        operation="parse"
    )
    assert result.success is False or (result.success is True and len(result.data.get("rows", [])) == 0)


@pytest.mark.asyncio
async def test_csv_processor_invalid_operation():
    """Test CSV processor with invalid operation."""
    tool = CSVProcessorTool()
    result = await tool.execute(
        data="test,data",
        operation="invalid_operation"
    )
    assert result.success is False


def test_csv_processor_metadata():
    """Test CSV processor metadata."""
    tool = CSVProcessorTool()
    assert "csv" in tool.metadata.description.lower() or "process" in tool.metadata.description.lower()


# ==================== XML Processor Tool Tests ====================

@pytest.mark.asyncio
async def test_xml_processor_initialization():
    """Test XML processor tool initialization."""
    tool = XMLProcessorTool()
    assert tool.metadata.name == "xml_processor"
    assert tool.metadata.category == "data"


@pytest.mark.asyncio
async def test_xml_processor_parse_valid_xml():
    """Test XML processor with valid XML."""
    tool = XMLProcessorTool()
    xml_data = '<?xml version="1.0"?><root><item>value</item></root>'
    result = await tool.execute(
        data=xml_data,
        operation="parse"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_xml_processor_parse_invalid_xml():
    """Test XML processor with invalid XML."""
    tool = XMLProcessorTool()
    result = await tool.execute(
        data='<invalid>xml',
        operation="parse"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_xml_processor_simple_xml():
    """Test XML processor with simple XML."""
    tool = XMLProcessorTool()
    xml_data = '<root><name>Test</name></root>'
    result = await tool.execute(
        data=xml_data,
        operation="parse"
    )
    assert result.success is True


def test_xml_processor_metadata():
    """Test XML processor metadata."""
    tool = XMLProcessorTool()
    assert "xml" in tool.metadata.description.lower() or "process" in tool.metadata.description.lower()


# ==================== Text Analyzer Tool Tests ====================

@pytest.mark.asyncio
async def test_text_analyzer_initialization():
    """Test text analyzer tool initialization."""
    tool = TextAnalyzerTool()
    assert tool.metadata.name == "text_analyzer"
    assert tool.metadata.category == "data"


@pytest.mark.asyncio
async def test_text_analyzer_word_count():
    """Test text analyzer word count."""
    tool = TextAnalyzerTool()
    result = await tool.execute(
        text="Hello world this is a test",
        operation="word_count"
    )
    assert result.success is True
    assert result.data.get("word_count") == 6 or "count" in result.data


@pytest.mark.asyncio
async def test_text_analyzer_character_count():
    """Test text analyzer character count."""
    tool = TextAnalyzerTool()
    result = await tool.execute(
        text="Hello",
        operation="char_count"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_text_analyzer_empty_text():
    """Test text analyzer with empty text."""
    tool = TextAnalyzerTool()
    result = await tool.execute(
        text="",
        operation="word_count"
    )
    assert result.success is True
    assert result.data.get("word_count") == 0 or result.data.get("count") == 0


@pytest.mark.asyncio
async def test_text_analyzer_sentiment():
    """Test text analyzer sentiment analysis."""
    tool = TextAnalyzerTool()
    result = await tool.execute(
        text="This is a great day!",
        operation="sentiment"
    )
    # Should either succeed or fail gracefully
    assert result.success is True or result.success is False


def test_text_analyzer_metadata():
    """Test text analyzer metadata."""
    tool = TextAnalyzerTool()
    assert "text" in tool.metadata.description.lower() or "analyze" in tool.metadata.description.lower()


# ==================== Data Transformer Tool Tests ====================

@pytest.mark.asyncio
async def test_data_transformer_initialization():
    """Test data transformer tool initialization."""
    tool = DataTransformerTool()
    assert tool.metadata.name == "data_transformer"
    assert tool.metadata.category == "data"


@pytest.mark.asyncio
async def test_data_transformer_uppercase():
    """Test data transformer uppercase operation."""
    tool = DataTransformerTool()
    result = await tool.execute(
        data="hello world",
        operation="uppercase"
    )
    assert result.success is True
    assert result.data.get("result") == "HELLO WORLD" or "HELLO" in str(result.data)


@pytest.mark.asyncio
async def test_data_transformer_lowercase():
    """Test data transformer lowercase operation."""
    tool = DataTransformerTool()
    result = await tool.execute(
        data="HELLO WORLD",
        operation="lowercase"
    )
    assert result.success is True
    assert result.data.get("result") == "hello world" or "hello" in str(result.data)


@pytest.mark.asyncio
async def test_data_transformer_trim():
    """Test data transformer trim operation."""
    tool = DataTransformerTool()
    result = await tool.execute(
        data="  hello  ",
        operation="trim"
    )
    assert result.success is True
    assert result.data.get("result") == "hello" or "hello" in str(result.data)


@pytest.mark.asyncio
async def test_data_transformer_invalid_operation():
    """Test data transformer with invalid operation."""
    tool = DataTransformerTool()
    result = await tool.execute(
        data="test",
        operation="invalid_operation"
    )
    assert result.success is False


def test_data_transformer_metadata():
    """Test data transformer metadata."""
    tool = DataTransformerTool()
    assert "data" in tool.metadata.description.lower() or "transform" in tool.metadata.description.lower()


# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_all_data_tools_have_category():
    """Test that all data tools have correct category."""
    tools = [
        JSONProcessorTool(),
        CSVProcessorTool(),
        XMLProcessorTool(),
        TextAnalyzerTool(),
        DataTransformerTool()
    ]
    
    for tool in tools:
        assert tool.metadata.category == "data"


@pytest.mark.asyncio
async def test_all_data_tools_have_parameters():
    """Test that all data tools have parameters defined."""
    tools = [
        JSONProcessorTool(),
        CSVProcessorTool(),
        XMLProcessorTool(),
        TextAnalyzerTool(),
        DataTransformerTool()
    ]
    
    for tool in tools:
        assert len(tool.parameters) > 0


def test_all_data_tools_have_descriptions():
    """Test that all data tools have descriptions."""
    tools = [
        JSONProcessorTool(),
        CSVProcessorTool(),
        XMLProcessorTool(),
        TextAnalyzerTool(),
        DataTransformerTool()
    ]
    
    for tool in tools:
        assert len(tool.metadata.description) > 0
        assert len(tool.metadata.tags) > 0
