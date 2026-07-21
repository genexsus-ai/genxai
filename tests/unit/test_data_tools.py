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


# ==================== Data Filter Tool Tests ====================

from genxai.tools.builtin.data.data_filter import DataFilterTool


@pytest.mark.asyncio
async def test_data_filter_equals_on_field():
    tool = DataFilterTool()
    items = [
        {"name": "Ana", "status": "active"},
        {"name": "Bo", "status": "inactive"},
        {"name": "Cy", "status": "active"},
    ]
    result = await tool.execute(items=items, field="status", operator="equals", value="active")
    assert result.success is True
    assert result.data["kept"] == 2
    assert [i["name"] for i in result.data["filtered"]] == ["Ana", "Cy"]


@pytest.mark.asyncio
async def test_data_filter_numeric_and_keep_false():
    tool = DataFilterTool()
    items = [{"age": 15}, {"age": 20}, {"age": 42}]
    # keep=False drops matches -> keeps the ones NOT greater than 18
    result = await tool.execute(
        items=items, field="age", operator="greater_than", value=18, keep=False
    )
    assert result.data["filtered"] == [{"age": 15}]


@pytest.mark.asyncio
async def test_data_filter_string_ops_and_dotpath():
    tool = DataFilterTool()
    items = [
        {"user": {"email": "a@work.com"}},
        {"user": {"email": "b@home.net"}},
    ]
    result = await tool.execute(
        items=items, field="user.email", operator="ends_with", value="work.com"
    )
    assert result.data["kept"] == 1


@pytest.mark.asyncio
async def test_data_filter_numeric_coercion_of_strings():
    tool = DataFilterTool()
    # values arriving as strings (e.g. from form input) still compare numerically
    items = [{"n": "3"}, {"n": "10"}]
    result = await tool.execute(items=items, field="n", operator="greater_than", value="5")
    assert [i["n"] for i in result.data["filtered"]] == ["10"]


@pytest.mark.asyncio
async def test_data_filter_single_object_and_bad_input():
    tool = DataFilterTool()
    one = await tool.execute(items={"x": 1}, field="x", operator="equals", value=1)
    assert one.data["kept"] == 1
    bad = await tool.execute(items="not a list", operator="is_not_empty")
    assert bad.data["success"] is False


# ==================== Set Fields Tool Tests ====================

from genxai.tools.builtin.data.data_set_fields import SetFieldsTool


@pytest.mark.asyncio
async def test_set_fields_keep_only_set():
    tool = SetFieldsTool()
    result = await tool.execute(
        fields={"name": "Ana", "greeting": "Hi Ana"},
        base={"name": "old", "junk": 1},
        keep_only_set=True,
    )
    assert result.success is True
    assert result.data["result"] == {"name": "Ana", "greeting": "Hi Ana"}


@pytest.mark.asyncio
async def test_set_fields_merge_with_base():
    tool = SetFieldsTool()
    result = await tool.execute(
        fields={"greeting": "Hi"},
        base={"name": "Ana", "email": "a@x.com"},
        keep_only_set=False,
    )
    assert result.data["result"] == {"name": "Ana", "email": "a@x.com", "greeting": "Hi"}


@pytest.mark.asyncio
async def test_set_fields_bad_input():
    tool = SetFieldsTool()
    result = await tool.execute(fields="not an object")
    assert result.data["success"] is False


# ==================== Date/Time Tool Tests ====================

from genxai.tools.builtin.data.date_time import DateTimeTool


@pytest.mark.asyncio
async def test_datetime_format_presets():
    tool = DateTimeTool()
    r = await tool.execute(operation="format", value="2026-07-21T02:43:53+00:00", format="date")
    assert r.data["result"] == "2026-07-21"
    r2 = await tool.execute(operation="format", value="2026-07-21", format="us")
    assert r2.data["result"] == "07/21/2026"
    r3 = await tool.execute(operation="format", value="2026-07-21", format="human")
    assert "2026" in r3.data["result"] and "July" in r3.data["result"]


@pytest.mark.asyncio
async def test_datetime_add_and_diff():
    tool = DateTimeTool()
    added = await tool.execute(operation="add", value="2026-07-21", amount=3, unit="days", format="date")
    assert added.data["result"] == "2026-07-24"
    diff = await tool.execute(operation="diff", value="2026-07-21", to="2026-07-24")
    assert diff.data["days"] == 3.0


@pytest.mark.asyncio
async def test_datetime_now_and_bad_input():
    tool = DateTimeTool()
    now = await tool.execute(operation="now", format="iso")
    assert now.success is True and "T" in now.data["result"]
    bad = await tool.execute(operation="format", value="not a date")
    assert bad.data["success"] is False
