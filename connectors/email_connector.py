"""
EmailConnector
==============
Implements BaseConnector for an IMAP mailbox — pulls message metadata
and attachment filenames (e.g. invoices/contracts arriving as email
attachments, a very common real enterprise source).

IMPORTANT — HONESTY NOTE: imaplib/email are Python standard library
(no extra dependency), so this WILL run wherever Python runs. However,
there was no live mailbox available to test an actual IMAP connection
against in this build environment. The MESSAGE-PARSING logic (subject,
sender, body, attachment detection) was tested against a real
constructed MIME message; the live imaplib fetch itself was not.

`mock_messages` (a list of raw RFC822 message bytes) lets you test the
full flow offline, without any real mailbox.

Connect  -> log into the IMAP server and select a folder
Extract  -> search + fetch messages, parse subject/sender/date/body/attachments
Validate -> reuse the shared required-field checks
Transform-> normalize into the common AI-ready schema

NEXT STEP NOT BUILT YET: piping PDF/DOCX attachment BYTES back through
PDFConnector/DocxConnector so an emailed invoice gets full Document
Intelligence treatment, not just its filename recorded. Straightforward
to add — out of scope for this pass.
"""

import email
from typing import Any, Dict, List, Optional

from connectors.base_connector import BaseConnector
from pipeline.validators import split_valid_invalid


class EmailConnector(BaseConnector):
    def __init__(
        self,
        host: str = None,
        username: str = None,
        password: str = None,
        folder: str = "INBOX",
        search_criteria: str = "ALL",
        limit: int = 20,
        required_fields: List[str] = None,
        mock_messages: Optional[List[bytes]] = None,
    ):
        super().__init__(source_name="email")
        self.host = host
        self.username = username
        self.password = password
        self.folder = folder
        self.search_criteria = search_criteria
        self.limit = limit
        self.required_fields = required_fields or []
        self.mock_messages = mock_messages  # offline/demo mode

    def connect(self) -> None:
        if self.mock_messages is not None:
            return
        # UNTESTED PATH — no live mailbox in the build environment.
        import imaplib
        self._connection = imaplib.IMAP4_SSL(self.host)
        self._connection.login(self.username, self.password)
        self._connection.select(self.folder)

    def extract(self) -> List[Dict[str, Any]]:
        if self.mock_messages is not None:
            raw_messages = self.mock_messages
        else:
            # UNTESTED PATH
            typ, data = self._connection.search(None, self.search_criteria)
            ids = data[0].split()[: self.limit]
            raw_messages = []
            for msg_id in ids:
                typ, msg_data = self._connection.fetch(msg_id, "(RFC822)")
                raw_messages.append(msg_data[0][1])
            self._connection.logout()

        records = []
        for raw in raw_messages:
            msg = email.message_from_bytes(raw)
            attachments = []
            body_text = ""
            for part in msg.walk():
                disposition = str(part.get("Content-Disposition", ""))
                filename = part.get_filename()
                if "attachment" in disposition and filename:
                    attachments.append(filename)
                elif part.get_content_type() == "text/plain" and not filename:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text += payload.decode(errors="replace")

            records.append({
                "subject": msg.get("Subject", ""),
                "sender": msg.get("From", ""),
                "date": msg.get("Date", ""),
                "attachments": attachments,
                "body_text": body_text[:2000],
            })
        return records

    def validate(self, raw_records: List[Dict[str, Any]]):
        return split_valid_invalid(raw_records, ["subject"] + self.required_fields)

    def transform(self, valid_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        for i, record in enumerate(valid_records):
            transformed.append({
                "record_id": f"email-{i}",
                "source_type": "email",
                "content": record,
                "metadata": {"folder": self.folder},
            })
        return transformed
