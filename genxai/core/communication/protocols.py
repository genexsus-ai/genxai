"""Communication protocols for agent interaction."""

from enum import Enum
from typing import Protocol as TypingProtocol, Any, Dict, List


class CommunicationProtocol(str, Enum):
    """Communication protocols for agents."""

    POINT_TO_POINT = "point_to_point"
    BROADCAST = "broadcast"
    REQUEST_REPLY = "request_reply"
    PUB_SUB = "pub_sub"
    NEGOTIATION = "negotiation"
    VOTING = "voting"
    AUCTION = "auction"


class MessageHandler(TypingProtocol):
    """Protocol for message handlers."""

    async def handle_message(self, message: Any) -> None:
        """Handle incoming message.

        Args:
            message: Message to handle
        """
        ...


class CollaborationProtocol(TypingProtocol):
    """Protocol for collaboration strategies."""

    async def run(self, inputs: List[Any], metadata: Dict[str, Any]) -> Any:
        ...
