"""SMS sender tool for sending text messages."""

from typing import Any, Dict
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class SMSSenderTool(Tool):
    """Send SMS messages via Twilio API."""

    def __init__(self) -> None:
        """Initialize SMS sender tool."""
        metadata = ToolMetadata(
            name="sms_sender",
            description="Send SMS text messages via Twilio",
            category=ToolCategory.COMMUNICATION,
            tags=["sms", "text", "message", "twilio", "communication"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="to_number",
                type="string",
                description="Recipient phone number (E.164 format: +1234567890)",
                required=True,
            ),
            ToolParameter(
                name="from_number",
                type="string",
                description="Sender phone number (Twilio number)",
                required=True,
            ),
            ToolParameter(
                name="message",
                type="string",
                description="SMS message text",
                required=True,
            ),
            ToolParameter(
                name="account_sid",
                type="string",
                description="Twilio Account SID",
                required=True,
            ),
            ToolParameter(
                name="auth_token",
                type="string",
                description="Twilio Auth Token",
                required=True,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        to_number: str,
        from_number: str,
        message: str,
        account_sid: str,
        auth_token: str,
    ) -> Dict[str, Any]:
        """Execute SMS sending.

        Args:
            to_number: Recipient phone number
            from_number: Sender phone number
            message: SMS message
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token

        Returns:
            Dictionary containing send results
        """
        try:
            from twilio.rest import Client
            from twilio.base.exceptions import TwilioRestException
        except ImportError:
            raise ImportError(
                "twilio package not installed. Install with: pip install twilio"
            )

        result: Dict[str, Any] = {
            "to": to_number,
            "from": from_number,
            "success": False,
        }

        try:
            # Create Twilio client
            client = Client(account_sid, auth_token)

            # Send SMS
            sms_message = client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )

            result.update({
                "success": True,
                "message_sid": sms_message.sid,
                "status": sms_message.status,
                "price": sms_message.price,
                "price_unit": sms_message.price_unit,
            })

        except TwilioRestException as e:
            result["error"] = f"Twilio error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"SMS send completed: success={result['success']}")
        return result
