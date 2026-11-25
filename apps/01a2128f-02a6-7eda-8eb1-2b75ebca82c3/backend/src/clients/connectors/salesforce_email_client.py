"""
Salesforce CRM-tracked email client.
For CRM-tracked emails to Contacts/Leads with activity history.
For general email sending without CRM tracking, use email_client.py instead.
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Optional

import requests

# Package-relative so the module works wherever the connectors package lives:
# app scaffolds import it as src.clients.connectors, agent-runtime skills as
# the salesforce skill package.
from .salesforce_client import get_salesforce_client

# In the workspace, unsent email lands here for inspection.
_WORKSPACE_EMAIL_CAPTURES = "/tmp/atlas-email-captures"


def _escape_apex_string(value: str) -> str:
    """
    Escape a string for safe inclusion in Apex code.

    Args:
        value: String to escape

    Returns:
        Escaped string safe for Apex
    """
    return (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r", "")
        .replace("\n", "\\n")
    )


class SalesforceEmailClient:
    """
    Client for sending CRM-tracked emails via Salesforce API.
    Emails are sent to Contacts/Leads and tracked in Salesforce activity history.
    Uses Client Credentials OAuth flow for authentication.
    """

    def __init__(self):
        """Initialize the CRM-tracked email client."""
        self.sf = get_salesforce_client()

    def _send_email(
        self,
        subject: str,
        body: str = "",
        html_body: Optional[str] = None,
        target_object_id: Optional[str] = None,
        to_addresses: Optional[List[str]] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        what_id: Optional[str] = None,
    ) -> dict:
        """
        Private helper method to send email via Salesforce Messaging API.

        Args:
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body
            target_object_id: Optional Contact/Lead ID (uses setTargetObjectId)
            to_addresses: Optional list of email addresses (uses setToAddresses)
            cc_addresses: Optional CC addresses (only with to_addresses)
            bcc_addresses: Optional BCC addresses (only with to_addresses)
            what_id: Optional record ID to link to

        Returns:
            dict: Response from Salesforce API

        Raises:
            RuntimeError: If the email sending fails
        """
        email_content = html_body if html_body else body

        email_content_escaped = _escape_apex_string(email_content)
        subject_escaped = _escape_apex_string(subject)

        apex_code_lines = [
            "Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();",
        ]

        if target_object_id:
            target_object_id_escaped = _escape_apex_string(target_object_id)
            apex_code_lines.append(
                f"mail.setTargetObjectId('{target_object_id_escaped}');"
            )
        elif to_addresses:
            email_addresses_apex = ", ".join(
                [f"'{_escape_apex_string(addr)}'" for addr in to_addresses]
            )
            apex_code_lines.append(
                f"mail.setToAddresses(new String[] {{{email_addresses_apex}}});"
            )

            # CC/BCC only supported with to_addresses, not with target_object_id
            if cc_addresses:
                cc_addresses_apex = ", ".join(
                    [f"'{_escape_apex_string(addr)}'" for addr in cc_addresses]
                )
                apex_code_lines.append(
                    f"mail.setCcAddresses(new String[] {{{cc_addresses_apex}}});"
                )

            if bcc_addresses:
                bcc_addresses_apex = ", ".join(
                    [f"'{_escape_apex_string(addr)}'" for addr in bcc_addresses]
                )
                apex_code_lines.append(
                    f"mail.setBccAddresses(new String[] {{{bcc_addresses_apex}}});"
                )
        else:
            raise ValueError("Either target_object_id or to_addresses must be provided")

        apex_code_lines.append(f"mail.setSubject('{subject_escaped}');")

        if html_body:
            apex_code_lines.append(f"mail.setHtmlBody('{email_content_escaped}');")
        else:
            apex_code_lines.append(f"mail.setPlainTextBody('{email_content_escaped}');")

        if what_id:
            what_id_escaped = _escape_apex_string(what_id)
            apex_code_lines.append(f"mail.setWhatId('{what_id_escaped}');")

        apex_code_lines.append(
            "Messaging.sendEmail(new Messaging.SingleEmailMessage[] { mail });"
        )

        apex_code = "\n".join(apex_code_lines)

        if os.environ.get("IS_WORKSPACE") == "true":
            email_data = {
                "timestamp": datetime.now().isoformat(),
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "target_object_id": target_object_id,
                "to_addresses": to_addresses,
                "cc_addresses": cc_addresses,
                "bcc_addresses": bcc_addresses,
                "what_id": what_id,
                "apex_code": apex_code,
            }

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = (
                f"{_WORKSPACE_EMAIL_CAPTURES}/salesforce_email_{timestamp_str}.json"
            )

            with open(filename, "w") as f:
                json.dump(email_data, f, indent=2)

            print(f"Email not sent. Data dumped to {filename}", file=sys.stderr)

            return {
                "line": -1,
                "column": -1,
                "compiled": True,
                "success": True,
                "compileProblem": None,
                "exceptionStackTrace": None,
                "exceptionMessage": None,
            }

        url = f"{self.sf.base_url}tooling/executeAnonymous/?anonymousBody={requests.utils.quote(apex_code)}"

        headers = {
            "Authorization": f"Bearer {self.sf.session_id}",
        }

        response = requests.get(url, headers=headers, timeout=30)

        if not response.ok:
            raise RuntimeError(
                f"Failed to send email: {response.status_code} - {response.text}"
            )

        result = response.json()

        if not result.get("compiled") or not result.get("success"):
            error_msg = result.get("compileProblem") or result.get("exceptionMessage")
            raise RuntimeError(f"Email sending failed: {error_msg}")

        return result


def send_email_to_contact(
    contact_id: str,
    subject: str,
    body: str = "",
    html_body: Optional[str] = None,
    what_id: Optional[str] = None,
) -> dict:
    """
    Convenience function to send CRM-tracked email to a Contact without creating a client instance.

    Args:
        contact_id: Contact or Lead ID
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        what_id: Optional record ID to link to (Account, Opportunity, Case, etc.)

    Returns:
        dict: Response from Salesforce API

    Example:
        >>> from src.clients.connectors.salesforce_email_client import send_email_to_contact
        >>> send_email_to_contact(
        ...     contact_id="003gL00000AbCDEAA3",
        ...     subject="Hello",
        ...     html_body="<p>Test email</p>",
        ...     what_id="001gL00000XyZPQAA3"
        ... )
    """
    client = SalesforceEmailClient()
    return client._send_email(
        subject=subject,
        body=body,
        html_body=html_body,
        target_object_id=contact_id,
        what_id=what_id,
    )
