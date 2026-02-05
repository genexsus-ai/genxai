"""Tests for message bus."""

import pytest
import asyncio
from typing import Any
from genxai.core.communication.message_bus import MessageBus, Message


def test_message_creation():
    """Test creating a message."""
    msg = Message(
        id="test_1",
        sender="agent1",
        recipient="agent2",
        content="Hello",
        message_type="greeting"
    )
    assert msg.id == "test_1"
    assert msg.sender == "agent1"
    assert msg.recipient == "agent2"
    assert msg.content == "Hello"
    assert msg.message_type == "greeting"


def test_message_bus_initialization():
    """Test message bus initialization."""
    bus = MessageBus()
    assert bus is not None
    assert len(bus._subscribers) == 0
    assert len(bus._message_history) == 0
    assert bus._message_count == 0


@pytest.mark.asyncio
async def test_send_message():
    """Test sending a message."""
    bus = MessageBus()
    
    # Create message
    msg = Message(
        id="",
        sender="agent1",
        recipient="agent2",
        content="Test message"
    )
    
    # Send message
    await bus.send(msg)
    
    # Verify message was sent
    assert bus._message_count == 1
    assert len(bus._message_history) == 1
    assert bus._message_history[0].content == "Test message"


@pytest.mark.asyncio
async def test_send_message_with_callback():
    """Test sending message with subscriber callback."""
    bus = MessageBus()
    received_messages = []
    
    # Define callback
    async def callback(msg: Message):
        received_messages.append(msg)
    
    # Subscribe agent2
    bus.subscribe("agent2", callback)
    
    # Send message to agent2
    msg = Message(
        id="",
        sender="agent1",
        recipient="agent2",
        content="Hello agent2"
    )
    await bus.send(msg)
    
    # Wait a bit for async callback
    await asyncio.sleep(0.1)
    
    # Verify callback was called
    assert len(received_messages) == 1
    assert received_messages[0].content == "Hello agent2"


@pytest.mark.asyncio
async def test_broadcast_message():
    """Test broadcasting a message."""
    bus = MessageBus()
    received_by_agent1 = []
    received_by_agent2 = []
    
    # Define callbacks
    async def callback1(msg: Message):
        received_by_agent1.append(msg)
    
    async def callback2(msg: Message):
        received_by_agent2.append(msg)
    
    # Subscribe agents
    bus.subscribe("agent1", callback1)
    bus.subscribe("agent2", callback2)
    
    # Broadcast message
    msg = Message(
        id="",
        sender="system",
        content="Broadcast to all"
    )
    await bus.broadcast(msg)
    
    # Wait for async callbacks
    await asyncio.sleep(0.1)
    
    # Verify both agents received
    assert len(received_by_agent1) == 1
    assert len(received_by_agent2) == 1


@pytest.mark.asyncio
async def test_broadcast_to_group():
    """Test broadcasting to a specific group."""
    bus = MessageBus()
    received_by_group = []
    received_by_other = []
    
    # Define callbacks
    async def group_callback(msg: Message):
        received_by_group.append(msg)
    
    async def other_callback(msg: Message):
        received_by_other.append(msg)
    
    # Subscribe agents (group_agent1 is in group, other_agent is not)
    bus.subscribe("group_agent1", group_callback)
    bus.subscribe("other_agent", other_callback)
    
    # Broadcast to group
    msg = Message(
        id="",
        sender="system",
        content="Group message"
    )
    await bus.broadcast(msg, group="group")
    
    # Wait for async callbacks
    await asyncio.sleep(0.1)
    
    # Verify only group agent received
    assert len(received_by_group) == 1
    assert len(received_by_other) == 0


def test_subscribe_agent():
    """Test subscribing an agent."""
    bus = MessageBus()
    
    async def callback(msg: Message):
        pass
    
    bus.subscribe("agent1", callback)
    
    assert "agent1" in bus._subscribers
    assert len(bus._subscribers["agent1"]) == 1


def test_unsubscribe_agent():
    """Test unsubscribing an agent."""
    bus = MessageBus()
    
    async def callback(msg: Message):
        pass
    
    # Subscribe then unsubscribe
    bus.subscribe("agent1", callback)
    bus.unsubscribe("agent1")
    
    assert "agent1" not in bus._subscribers


def test_unsubscribe_specific_callback():
    """Test unsubscribing a specific callback."""
    bus = MessageBus()
    
    async def callback1(msg: Message):
        pass
    
    async def callback2(msg: Message):
        pass
    
    # Subscribe two callbacks
    bus.subscribe("agent1", callback1)
    bus.subscribe("agent1", callback2)
    
    # Unsubscribe one
    bus.unsubscribe("agent1", callback1)
    
    assert "agent1" in bus._subscribers
    assert len(bus._subscribers["agent1"]) == 1


def test_get_history():
    """Test getting message history."""
    bus = MessageBus()
    
    # Send some messages
    asyncio.run(bus.send(Message(id="", sender="a1", recipient="a2", content="msg1")))
    asyncio.run(bus.send(Message(id="", sender="a2", recipient="a1", content="msg2")))
    
    # Get all history
    history = bus.get_history()
    assert len(history) == 2


def test_get_history_filtered():
    """Test getting filtered message history."""
    bus = MessageBus()
    
    # Send messages
    asyncio.run(bus.send(Message(id="", sender="a1", recipient="a2", content="msg1")))
    asyncio.run(bus.send(Message(id="", sender="a2", recipient="a3", content="msg2")))
    asyncio.run(bus.send(Message(id="", sender="a1", recipient="a3", content="msg3")))
    
    # Get history for agent1
    history = bus.get_history(agent_id="a1")
    assert len(history) == 2  # a1 sent 2 messages


def test_get_history_with_limit():
    """Test getting limited message history."""
    bus = MessageBus()
    
    # Send multiple messages
    for i in range(5):
        asyncio.run(bus.send(Message(id="", sender="a1", recipient="a2", content=f"msg{i}")))
    
    # Get last 3 messages
    history = bus.get_history(limit=3)
    assert len(history) == 3


def test_clear_history():
    """Test clearing message history."""
    bus = MessageBus()
    
    # Send messages
    asyncio.run(bus.send(Message(id="", sender="a1", recipient="a2", content="msg1")))
    asyncio.run(bus.send(Message(id="", sender="a2", recipient="a1", content="msg2")))
    
    # Clear history
    bus.clear_history()
    
    assert len(bus._message_history) == 0


def test_get_stats():
    """Test getting message bus statistics."""
    bus = MessageBus()
    
    # Subscribe agents
    bus.subscribe("agent1", lambda msg: None)
    bus.subscribe("agent2", lambda msg: None)
    
    # Send messages
    asyncio.run(bus.send(Message(id="", sender="a1", recipient="a2", content="msg1")))
    
    # Get stats
    stats = bus.get_stats()
    
    assert stats["total_messages"] == 1
    assert stats["subscribers"] == 2
    assert "agent1" in stats["subscriber_list"]
    assert "agent2" in stats["subscriber_list"]


def test_message_bus_repr():
    """Test message bus string representation."""
    bus = MessageBus()
    bus.subscribe("agent1", lambda msg: None)
    asyncio.run(bus.send(Message(id="", sender="a1", recipient="a2", content="msg")))
    
    repr_str = repr(bus)
    assert "MessageBus" in repr_str
    assert "messages=1" in repr_str
    assert "subscribers=1" in repr_str
