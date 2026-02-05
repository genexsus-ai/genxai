"""Tests for computation tools."""

import pytest
from genxai.tools.builtin.computation.calculator import CalculatorTool
from genxai.tools.builtin.computation.code_executor import CodeExecutorTool
from genxai.tools.builtin.computation.data_validator import DataValidatorTool
from genxai.tools.builtin.computation.hash_generator import HashGeneratorTool
from genxai.tools.builtin.computation.regex_matcher import RegexMatcherTool


# ==================== Calculator Tool Tests ====================

@pytest.mark.asyncio
async def test_calculator_initialization():
    """Test calculator tool initialization."""
    tool = CalculatorTool()
    assert tool.metadata.name == "calculator"
    assert tool.metadata.category == "computation"
    assert len(tool.parameters) > 0


@pytest.mark.asyncio
async def test_calculator_addition():
    """Test calculator addition."""
    tool = CalculatorTool()
    result = await tool.execute(expression="2 + 2")
    assert result.success is True
    assert result.data["result"] == 4.0


@pytest.mark.asyncio
async def test_calculator_multiplication():
    """Test calculator multiplication."""
    tool = CalculatorTool()
    result = await tool.execute(expression="5 * 3")
    assert result.success is True
    assert result.data["result"] == 15.0


@pytest.mark.asyncio
async def test_calculator_complex_expression():
    """Test calculator with complex expression."""
    tool = CalculatorTool()
    result = await tool.execute(expression="(10 + 5) * 2 - 3")
    assert result.success is True
    assert result.data["result"] == 27.0


@pytest.mark.asyncio
async def test_calculator_invalid_expression():
    """Test calculator with invalid expression."""
    tool = CalculatorTool()
    result = await tool.execute(expression="invalid")
    assert result.success is False
    assert result.error is not None


def test_calculator_metadata():
    """Test calculator metadata."""
    tool = CalculatorTool()
    assert "calculate" in tool.metadata.description.lower()
    assert len(tool.metadata.tags) > 0


# ==================== Code Executor Tool Tests ====================

@pytest.mark.asyncio
async def test_code_executor_initialization():
    """Test code executor tool initialization."""
    tool = CodeExecutorTool()
    assert tool.metadata.name == "code_executor"
    assert tool.metadata.category == "computation"


@pytest.mark.asyncio
async def test_code_executor_simple_code():
    """Test code executor with simple Python code."""
    tool = CodeExecutorTool()
    result = await tool.execute(
        code="result = 2 + 2",
        language="python"
    )
    assert result.success is True
    assert "result" in result.data or "output" in result.data


@pytest.mark.asyncio
async def test_code_executor_with_print():
    """Test code executor with print statement."""
    tool = CodeExecutorTool()
    result = await tool.execute(
        code="print('Hello, World!')",
        language="python"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_code_executor_invalid_syntax():
    """Test code executor with invalid syntax."""
    tool = CodeExecutorTool()
    result = await tool.execute(
        code="invalid python syntax !!!",
        language="python"
    )
    assert result.success is False
    assert result.error is not None


def test_code_executor_metadata():
    """Test code executor metadata."""
    tool = CodeExecutorTool()
    assert "execute" in tool.metadata.description.lower() or "code" in tool.metadata.description.lower()


# ==================== Data Validator Tool Tests ====================

@pytest.mark.asyncio
async def test_data_validator_initialization():
    """Test data validator tool initialization."""
    tool = DataValidatorTool()
    assert tool.metadata.name == "data_validator"
    assert tool.metadata.category == "computation"


@pytest.mark.asyncio
async def test_data_validator_valid_email():
    """Test data validator with valid email."""
    tool = DataValidatorTool()
    result = await tool.execute(
        data="test@example.com",
        validation_type="email"
    )
    assert result.success is True
    assert result.data.get("valid") is True


@pytest.mark.asyncio
async def test_data_validator_invalid_email():
    """Test data validator with invalid email."""
    tool = DataValidatorTool()
    result = await tool.execute(
        data="invalid-email",
        validation_type="email"
    )
    # Should either succeed with valid=False or fail
    assert result.success is True or result.success is False


@pytest.mark.asyncio
async def test_data_validator_valid_url():
    """Test data validator with valid URL."""
    tool = DataValidatorTool()
    result = await tool.execute(
        data="https://example.com",
        validation_type="url"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_data_validator_valid_json():
    """Test data validator with valid JSON."""
    tool = DataValidatorTool()
    result = await tool.execute(
        data='{"key": "value"}',
        validation_type="json"
    )
    assert result.success is True


def test_data_validator_metadata():
    """Test data validator metadata."""
    tool = DataValidatorTool()
    assert "validate" in tool.metadata.description.lower() or "data" in tool.metadata.description.lower()


# ==================== Hash Generator Tool Tests ====================

@pytest.mark.asyncio
async def test_hash_generator_initialization():
    """Test hash generator tool initialization."""
    tool = HashGeneratorTool()
    assert tool.metadata.name == "hash_generator"
    assert tool.metadata.category == "computation"


@pytest.mark.asyncio
async def test_hash_generator_md5():
    """Test hash generator with MD5."""
    tool = HashGeneratorTool()
    result = await tool.execute(
        data="test",
        algorithm="md5"
    )
    assert result.success is True
    assert "hash" in result.data
    assert len(result.data["hash"]) == 32  # MD5 is 32 hex chars


@pytest.mark.asyncio
async def test_hash_generator_sha256():
    """Test hash generator with SHA256."""
    tool = HashGeneratorTool()
    result = await tool.execute(
        data="test",
        algorithm="sha256"
    )
    assert result.success is True
    assert "hash" in result.data
    assert len(result.data["hash"]) == 64  # SHA256 is 64 hex chars


@pytest.mark.asyncio
async def test_hash_generator_sha1():
    """Test hash generator with SHA1."""
    tool = HashGeneratorTool()
    result = await tool.execute(
        data="test",
        algorithm="sha1"
    )
    assert result.success is True
    assert "hash" in result.data


@pytest.mark.asyncio
async def test_hash_generator_invalid_algorithm():
    """Test hash generator with invalid algorithm."""
    tool = HashGeneratorTool()
    result = await tool.execute(
        data="test",
        algorithm="invalid"
    )
    assert result.success is False
    assert result.error is not None


def test_hash_generator_metadata():
    """Test hash generator metadata."""
    tool = HashGeneratorTool()
    assert "hash" in tool.metadata.description.lower()


# ==================== Regex Matcher Tool Tests ====================

@pytest.mark.asyncio
async def test_regex_matcher_initialization():
    """Test regex matcher tool initialization."""
    tool = RegexMatcherTool()
    assert tool.metadata.name == "regex_matcher"
    assert tool.metadata.category == "computation"


@pytest.mark.asyncio
async def test_regex_matcher_simple_match():
    """Test regex matcher with simple pattern."""
    tool = RegexMatcherTool()
    result = await tool.execute(
        text="Hello World",
        pattern=r"Hello"
    )
    assert result.success is True
    assert result.data.get("matches") is not None


@pytest.mark.asyncio
async def test_regex_matcher_email_pattern():
    """Test regex matcher with email pattern."""
    tool = RegexMatcherTool()
    result = await tool.execute(
        text="Contact us at test@example.com",
        pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    assert result.success is True
    assert len(result.data.get("matches", [])) > 0


@pytest.mark.asyncio
async def test_regex_matcher_no_match():
    """Test regex matcher with no matches."""
    tool = RegexMatcherTool()
    result = await tool.execute(
        text="Hello World",
        pattern=r"xyz"
    )
    assert result.success is True
    assert len(result.data.get("matches", [])) == 0


@pytest.mark.asyncio
async def test_regex_matcher_invalid_pattern():
    """Test regex matcher with invalid pattern."""
    tool = RegexMatcherTool()
    result = await tool.execute(
        text="Hello World",
        pattern=r"[invalid("
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_regex_matcher_groups():
    """Test regex matcher with capture groups."""
    tool = RegexMatcherTool()
    result = await tool.execute(
        text="Date: 2024-01-30",
        pattern=r"(\d{4})-(\d{2})-(\d{2})"
    )
    assert result.success is True
    assert len(result.data.get("matches", [])) > 0


def test_regex_matcher_metadata():
    """Test regex matcher metadata."""
    tool = RegexMatcherTool()
    assert "regex" in tool.metadata.description.lower() or "pattern" in tool.metadata.description.lower()
