"""Communication layer for agent-to-agent messaging."""

from genxai.core.communication.message_bus import MessageBus, Message
from genxai.core.communication.protocols import CommunicationProtocol

__all__ = ["MessageBus", "Message", "CommunicationProtocol"]
