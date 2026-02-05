"""Message bus for agent-to-agent communication."""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Message for agent communication."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    sender: str
    recipient: Optional[str] = None  # None for broadcast
    content: Any
    message_type: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    reply_to: Optional[str] = None



class MessageBus:
    """Central message bus for agent communication."""

    def __init__(self) -> None:
        """Initialize message bus."""
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_history: List[Message] = []
        self._message_count = 0

    async def send(self, message: Message) -> None:
        """Send a message to a specific recipient.

        Args:
            message: Message to send
        """
        self._message_count += 1
        message.id = f"msg_{self._message_count}"
        self._message_history.append(message)

        logger.info(f"Message sent: {message.sender} -> {message.recipient}")

        # Deliver to recipient's subscribers
        if message.recipient and message.recipient in self._subscribers:
            for callback in self._subscribers[message.recipient]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error delivering message to {message.recipient}: {e}")

    async def broadcast(self, message: Message, group: Optional[str] = None) -> None:
        """Broadcast a message to all subscribers or a group.

        Args:
            message: Message to broadcast
            group: Optional group name to broadcast to
        """
        self._message_count += 1
        message.id = f"msg_{self._message_count}"
        message.recipient = None  # Broadcast has no specific recipient
        self._message_history.append(message)

        logger.info(f"Message broadcast from {message.sender} to group: {group or 'all'}")

        # Deliver to all subscribers (or group subscribers)
        for agent_id, callbacks in self._subscribers.items():
            if group and not agent_id.startswith(f"{group}_"):
                continue

            for callback in callbacks:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {agent_id}: {e}")

    async def request_reply(
        self, message: Message, timeout: float = 30.0
    ) -> Optional[Message]:
        """Send a message and wait for reply.

        Args:
            message: Message to send
            timeout: Timeout in seconds

        Returns:
            Reply message or None if timeout
        """
        # Send message
        await self.send(message)

        # Wait for reply
        reply_event = asyncio.Event()
        reply_message: Optional[Message] = None

        async def reply_handler(msg: Message) -> None:
            nonlocal reply_message
            if msg.reply_to == message.id:
                reply_message = msg
                reply_event.set()

        # Subscribe to replies
        if message.sender:
            self.subscribe(message.sender, reply_handler)

        try:
            await asyncio.wait_for(reply_event.wait(), timeout=timeout)
            return reply_message
        except asyncio.TimeoutError:
            logger.warning(f"Request-reply timeout for message {message.id}")
            return None
        finally:
            if message.sender:
                self.unsubscribe(message.sender, reply_handler)

    def subscribe(self, agent_id: str, callback: Callable) -> None:
        """Subscribe an agent to receive messages.

        Args:
            agent_id: Agent identifier
            callback: Async callback function to handle messages
        """
        self._subscribers[agent_id].append(callback)
        logger.debug(f"Agent {agent_id} subscribed to message bus")

    def unsubscribe(self, agent_id: str, callback: Optional[Callable] = None) -> None:
        """Unsubscribe an agent from messages.

        Args:
            agent_id: Agent identifier
            callback: Specific callback to remove (None to remove all)
        """
        if agent_id in self._subscribers:
            if callback:
                self._subscribers[agent_id].remove(callback)
            else:
                del self._subscribers[agent_id]
            logger.debug(f"Agent {agent_id} unsubscribed from message bus")

    def get_history(
        self, agent_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history.

        Args:
            agent_id: Filter by agent (sender or recipient)
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        messages = self._message_history

        if agent_id:
            messages = [
                m
                for m in messages
                if m.sender == agent_id or m.recipient == agent_id
            ]

        if limit:
            messages = messages[-limit:]

        return messages

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()
        logger.info("Message history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_messages": self._message_count,
            "history_size": len(self._message_history),
            "subscribers": len(self._subscribers),
            "subscriber_list": list(self._subscribers.keys()),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"MessageBus(messages={self._message_count}, subscribers={len(self._subscribers)})"
