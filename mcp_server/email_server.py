from __future__ import annotations

import os
import re
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from mcp.server import MCPServer

load_dotenv()

mcp = MCPServer(
    "Movie Assistant Email",
    instructions="Send grounded movie summaries or scene analyses by email when requested by the host application.",
)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@mcp.tool()
def send_email(recipient: str, subject: str, body: str) -> str:
    """Send a plain-text email through the configured SMTP account."""
    if not EMAIL_RE.fullmatch(recipient):
        raise ValueError("Invalid recipient email address.")

    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", username)

    if not all([host, username, password, sender]):
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM in .env.")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)

    return f"Email successfully sent to {recipient}."


if __name__ == "__main__":
    mcp.run()
