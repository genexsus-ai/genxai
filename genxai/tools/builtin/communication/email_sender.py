"""Email sender tool for sending emails via SMTP."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class EmailSenderTool(Tool):
    """Send emails via SMTP with support for HTML and attachments."""

    def __init__(self) -> None:
        """Initialize email sender tool."""
        metadata = ToolMetadata(
            name="email_sender",
            description="Send emails via SMTP with HTML support and attachments",
            category=ToolCategory.COMMUNICATION,
            tags=["email", "smtp", "communication", "notification", "message"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="to",
                type="string",
                description="Recipient email address",
                required=True,
            ),
            ToolParameter(
                name="subject",
                type="string",
                description="Email subject",
                required=True,
            ),
            ToolParameter(
                name="body",
                type="string",
                description="Email body content",
                required=True,
            ),
            ToolParameter(
                name="from_email",
                type="string",
                description="Sender email address",
                required=True,
            ),
            ToolParameter(
                name="smtp_host",
                type="string",
                description="SMTP server host",
                required=True,
            ),
            ToolParameter(
                name="smtp_port",
                type="number",
                description="SMTP server port",
                required=False,
                default=587,
            ),
            ToolParameter(
                name="username",
                type="string",
                description="SMTP username",
                required=False,
            ),
            ToolParameter(
                name="password",
                type="string",
                description="SMTP password",
                required=False,
            ),
            ToolParameter(
                name="html",
                type="boolean",
                description="Whether body is HTML",
                required=False,
                default=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        smtp_host: str,
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        html: bool = False,
    ) -> Dict[str, Any]:
        """Execute email sending.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            from_email: Sender email
            smtp_host: SMTP host
            smtp_port: SMTP port
            username: SMTP username
            password: SMTP password
            html: HTML flag

        Returns:
            Dictionary containing send results
        """
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
        except ImportError:
            raise ImportError(
                "aiosmtplib package not installed. Install with: pip install aiosmtplib"
            )

        result: Dict[str, Any] = {
            "to": to,
            "subject": subject,
            "success": False,
        }

        try:
            # Create message
            if html:
                message = MIMEMultipart("alternative")
                message.attach(MIMEText(body, "html"))
            else:
                message = MIMEText(body, "plain")

            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to

            # Send email
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=username,
                password=password,
                start_tls=True if smtp_port == 587 else False,
            )

            result.update({
                "success": True,
                "message": "Email sent successfully",
            })

        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Email send completed: success={result['success']}")
        return result
