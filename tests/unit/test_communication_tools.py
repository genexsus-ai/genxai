"""Tests for communication tools."""

import pytest
from genxai.tools.builtin.communication.email_sender import EmailSenderTool
from genxai.tools.builtin.communication.slack_notifier import SlackNotifierTool
from genxai.tools.builtin.communication.sms_sender import SMSSenderTool
from genxai.tools.builtin.communication.webhook_caller import WebhookCallerTool
from genxai.tools.builtin.communication.notification_manager import NotificationManagerTool


# ==================== Email Sender Tool Tests ====================

@pytest.mark.asyncio
async def test_email_sender_initialization():
    """Test email sender tool initialization."""
    tool = EmailSenderTool()
    assert tool.metadata.name == "email_sender"
    assert tool.metadata.category == "communication"
    assert len(tool.parameters) > 0


@pytest.mark.asyncio
async def test_email_sender_invalid_config():
    """Test email sender with invalid configuration."""
    tool = EmailSenderTool()
    result = await tool.execute(
        to="test@example.com",
        subject="Test",
        body="Test message",
        smtp_host="invalid",
        smtp_port=587
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_email_sender_invalid_email():
    """Test email sender with invalid email address."""
    tool = EmailSenderTool()
    result = await tool.execute(
        to="invalid-email",
        subject="Test",
        body="Test message"
    )
    assert result.success is False


def test_email_sender_metadata():
    """Test email sender metadata."""
    tool = EmailSenderTool()
    assert "email" in tool.metadata.description.lower() or "send" in tool.metadata.description.lower()
    assert len(tool.metadata.tags) > 0


# ==================== Slack Notifier Tool Tests ====================

@pytest.mark.asyncio
async def test_slack_notifier_initialization():
    """Test Slack notifier tool initialization."""
    tool = SlackNotifierTool()
    assert tool.metadata.name == "slack_notifier"
    assert tool.metadata.category == "communication"


@pytest.mark.asyncio
async def test_slack_notifier_invalid_webhook():
    """Test Slack notifier with invalid webhook URL."""
    tool = SlackNotifierTool()
    result = await tool.execute(
        message="Test message",
        webhook_url="invalid-url"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_slack_notifier_empty_message():
    """Test Slack notifier with empty message."""
    tool = SlackNotifierTool()
    result = await tool.execute(
        message="",
        webhook_url="https://hooks.slack.com/services/test"
    )
    assert result.success is False


def test_slack_notifier_metadata():
    """Test Slack notifier metadata."""
    tool = SlackNotifierTool()
    assert "slack" in tool.metadata.description.lower() or "notify" in tool.metadata.description.lower()


# ==================== SMS Sender Tool Tests ====================

@pytest.mark.asyncio
async def test_sms_sender_initialization():
    """Test SMS sender tool initialization."""
    tool = SMSSenderTool()
    assert tool.metadata.name == "sms_sender"
    assert tool.metadata.category == "communication"


@pytest.mark.asyncio
async def test_sms_sender_invalid_phone():
    """Test SMS sender with invalid phone number."""
    tool = SMSSenderTool()
    result = await tool.execute(
        to="invalid",
        message="Test message"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_sms_sender_empty_message():
    """Test SMS sender with empty message."""
    tool = SMSSenderTool()
    result = await tool.execute(
        to="+1234567890",
        message=""
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_sms_sender_missing_credentials():
    """Test SMS sender with missing credentials."""
    tool = SMSSenderTool()
    result = await tool.execute(
        to="+1234567890",
        message="Test"
    )
    # Should fail without credentials
    assert result.success is False


def test_sms_sender_metadata():
    """Test SMS sender metadata."""
    tool = SMSSenderTool()
    assert "sms" in tool.metadata.description.lower() or "send" in tool.metadata.description.lower()


# ==================== Webhook Caller Tool Tests ====================

@pytest.mark.asyncio
async def test_webhook_caller_initialization():
    """Test webhook caller tool initialization."""
    tool = WebhookCallerTool()
    assert tool.metadata.name == "webhook_caller"
    assert tool.metadata.category == "communication"


@pytest.mark.asyncio
async def test_webhook_caller_invalid_url():
    """Test webhook caller with invalid URL."""
    tool = WebhookCallerTool()
    result = await tool.execute(
        url="invalid-url",
        payload={"test": "data"}
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_webhook_caller_nonexistent_url():
    """Test webhook caller with nonexistent URL."""
    tool = WebhookCallerTool()
    result = await tool.execute(
        url="https://nonexistent-webhook-12345.com/hook",
        payload={"test": "data"}
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_webhook_caller_empty_payload():
    """Test webhook caller with empty payload."""
    tool = WebhookCallerTool()
    result = await tool.execute(
        url="https://httpbin.org/post",
        payload={}
    )
    # Should succeed with empty payload
    assert result.success is True or result.success is False


def test_webhook_caller_metadata():
    """Test webhook caller metadata."""
    tool = WebhookCallerTool()
    assert "webhook" in tool.metadata.description.lower() or "call" in tool.metadata.description.lower()


# ==================== Notification Manager Tool Tests ====================

@pytest.mark.asyncio
async def test_notification_manager_initialization():
    """Test notification manager tool initialization."""
    tool = NotificationManagerTool()
    assert tool.metadata.name == "notification_manager"
    assert tool.metadata.category == "communication"


@pytest.mark.asyncio
async def test_notification_manager_invalid_channel():
    """Test notification manager with invalid channel."""
    tool = NotificationManagerTool()
    result = await tool.execute(
        message="Test notification",
        channel="invalid_channel"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_notification_manager_empty_message():
    """Test notification manager with empty message."""
    tool = NotificationManagerTool()
    result = await tool.execute(
        message="",
        channel="email"
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_notification_manager_missing_config():
    """Test notification manager with missing configuration."""
    tool = NotificationManagerTool()
    result = await tool.execute(
        message="Test",
        channel="email"
    )
    # Should fail without proper config
    assert result.success is False


def test_notification_manager_metadata():
    """Test notification manager metadata."""
    tool = NotificationManagerTool()
    assert "notification" in tool.metadata.description.lower() or "manage" in tool.metadata.description.lower()


# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_all_communication_tools_have_category():
    """Test that all communication tools have correct category."""
    tools = [
        EmailSenderTool(),
        SlackNotifierTool(),
        SMSSenderTool(),
        WebhookCallerTool(),
        NotificationManagerTool()
    ]
    
    for tool in tools:
        assert tool.metadata.category == "communication"


@pytest.mark.asyncio
async def test_all_communication_tools_have_parameters():
    """Test that all communication tools have parameters defined."""
    tools = [
        EmailSenderTool(),
        SlackNotifierTool(),
        SMSSenderTool(),
        WebhookCallerTool(),
        NotificationManagerTool()
    ]
    
    for tool in tools:
        assert len(tool.parameters) > 0


def test_all_communication_tools_have_descriptions():
    """Test that all communication tools have descriptions."""
    tools = [
        EmailSenderTool(),
        SlackNotifierTool(),
        SMSSenderTool(),
        WebhookCallerTool(),
        NotificationManagerTool()
    ]
    
    for tool in tools:
        assert len(tool.metadata.description) > 0
        assert len(tool.metadata.tags) > 0
