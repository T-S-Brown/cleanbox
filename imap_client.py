"""
imap_client.py - Robust IMAP client supporting Gmail, Hotmail/Outlook, and custom providers.
Optimized for high-speed scanning of message sizes and headers using BODY.PEEK.
"""

import imaplib
import email
from email.header import decode_header
import re
from typing import List, Dict, Any, Optional, Tuple, Callable
import socket

# Timeout in seconds for IMAP operations
IMAP_TIMEOUT = 30

PRESETS = {
    "gmail": {
        "name": "Gmail",
        "host": "imap.gmail.com",
        "port": 993,
        "ssl": True,
        "trash_candidates": ["[Gmail]/Trash", "[Gmail]/Bin", "Trash"],
    },
    "hotmail": {
        "name": "Hotmail / Outlook",
        "host": "outlook.office365.com",
        "port": 993,
        "ssl": True,
        "trash_candidates": ["Deleted Items", "Deleted", "Trash", "Bin"],
    },
    "custom": {
        "name": "Custom IMAP",
        "host": "",
        "port": 993,
        "ssl": True,
        "trash_candidates": ["Trash", "Deleted Items", "Deleted", "Bin"],
    }
}


def decode_mime_words(s: Optional[str]) -> str:
    """Decode RFC 2047 MIME encoded words in email headers (e.g. =?UTF-8?B?...?=)."""
    if not s:
        return ""
    try:
        decoded_fragments = decode_header(s)
        parts = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                encoding = encoding or "utf-8"
                try:
                    parts.append(fragment.decode(encoding, errors="replace"))
                except (LookupError, UnicodeDecodeError):
                    parts.append(fragment.decode("utf-8", errors="replace"))
            else:
                parts.append(str(fragment))
        return " ".join(parts).strip()
    except Exception:
        return str(s)


class MailboxSession:
    def __init__(self, provider: str, host: str, port: int, email_addr: str, password: str, use_ssl: bool = True):
        self.provider = provider.lower()
        self.host = host
        self.port = port
        self.email_addr = email_addr
        self.password = password
        self.use_ssl = use_ssl
        self.client: Optional[imaplib.IMAP4] = None
        self.trash_folder: Optional[str] = None

    def connect(self) -> Tuple[bool, str]:
        """Establish connection and authenticate with IMAP server."""
        try:
            socket.setdefaulttimeout(IMAP_TIMEOUT)
            if self.use_ssl:
                self.client = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.client = imaplib.IMAP4(self.host, self.port)

            res, data = self.client.login(self.email_addr, self.password)
            if res != "OK":
                return False, f"Login failed: {data}"
            
            # Identify trash folder
            self.trash_folder = self._detect_trash_folder()
            return True, "Successfully connected"
        except imaplib.IMAP4.error as e:
            return False, f"IMAP authentication error: {str(e)}"
        except socket.timeout:
            return False, f"Connection timed out while connecting to {self.host}:{self.port}"
        except Exception as e:
            return False, f"Failed to connect: {str(e)}"

    def list_folders(self) -> List[str]:
        """Get list of available mailbox folders."""
        if not self.client:
            return []
        try:
            res, folders = self.client.list()
            if res != "OK" or not folders:
                return ["INBOX"]
            folder_names = []
            for item in folders:
                if not item:
                    continue
                # IMAP list returns e.g. '(\\HasNoChildren) "/" "INBOX"'
                match = re.search(r'"([^"]+)"$', item.decode("utf-8", errors="replace").strip())
                if match:
                    folder_names.append(match.group(1))
                else:
                    parts = item.decode("utf-8", errors="replace").strip().split()
                    if parts:
                        folder_names.append(parts[-1].strip('"'))
            return folder_names if folder_names else ["INBOX"]
        except Exception:
            return ["INBOX"]

    def _detect_trash_folder(self) -> str:
        """Find the provider's trash folder."""
        folders = self.list_folders()
        candidates = PRESETS.get(self.provider, PRESETS["custom"])["trash_candidates"]
        
        for cand in candidates:
            for f in folders:
                if f.lower() == cand.lower():
                    return f

        # Fallback regex search
        for f in folders:
            if re.search(r"trash|bin|deleted", f, re.IGNORECASE):
                return f
        
        return "Trash"

    def scan_emails(
        self,
        folder: str = "INBOX",
        max_emails: Optional[int] = 500,
        order: str = "newest",  # "newest" or "oldest" ("start")
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan email sizes and headers in specified folder.
        Uses BODY.PEEK to prevent marking emails as read.
        Supports scanning entire inbox from the start (oldest first) or newest first.
        """
        if not self.client:
            raise RuntimeError("IMAP client not connected")

        # Select folder (readonly=True to ensure no unread state changes)
        res, data = self.client.select(f'"{folder}"', readonly=True)
        if res != "OK":
            # Try without quotes if failed
            res, data = self.client.select(folder, readonly=True)
            if res != "OK":
                raise RuntimeError(f"Could not open folder {folder}: {data}")

        # Search for all UIDs
        res, search_data = self.client.uid("search", None, "ALL")
        if res != "OK" or not search_data or not search_data[0]:
            return []

        uids = search_data[0].split()
        total_found = len(uids)

        # Slice based on order and max_emails
        # "oldest" / "start": scans starting from the beginning of mailbox history (UID 1 ... N)
        # "newest": scans starting from the latest emails down
        if max_emails and max_emails > 0 and total_found > max_emails:
            if order in ("oldest", "start"):
                uids_to_fetch = uids[:max_emails]
            else:
                uids_to_fetch = list(reversed(uids[-max_emails:]))
        else:
            # Entire inbox!
            if order in ("oldest", "start"):
                uids_to_fetch = uids
            else:
                uids_to_fetch = list(reversed(uids))

        emails_list: List[Dict[str, Any]] = []

        batch_size = 100 if len(uids_to_fetch) > 500 else 50
        num_batches = (len(uids_to_fetch) + batch_size - 1) // batch_size

        for i in range(num_batches):
            chunk = uids_to_fetch[i * batch_size : (i + 1) * batch_size]
            uid_set = b",".join(chunk).decode("ascii")

            if progress_callback:
                progress_callback(len(emails_list), len(uids_to_fetch), f"Fetching headers {i+1}/{num_batches}")

            # Fetch RFC822.SIZE and specific headers with BODY.PEEK
            fetch_cmd = "(RFC822.SIZE BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO DATE MESSAGE-ID LIST-UNSUBSCRIBE LIST-UNSUBSCRIBE-POST PRECEDENCE X-CAMPAIGN X-MAILER)])"
            res, fetch_data = self.client.uid("fetch", uid_set, fetch_cmd)
            if res != "OK":
                continue

            for item in fetch_data:
                if isinstance(item, tuple):
                    header_bytes = item[1]
                    meta = item[0].decode("utf-8", errors="replace")

                    # Extract UID and size from meta string
                    uid_match = re.search(r"UID\s+(\d+)", meta)
                    size_match = re.search(r"RFC822\.SIZE\s+(\d+)", meta)

                    uid_str = uid_match.group(1) if uid_match else ""
                    size_bytes = int(size_match.group(1)) if size_match else 0

                    # Parse headers
                    msg = email.message_from_bytes(header_bytes)
                    subject = decode_mime_words(msg.get("Subject", ""))
                    sender = decode_mime_words(msg.get("From", ""))
                    recipient = decode_mime_words(msg.get("To", ""))
                    date_str = msg.get("Date", "")
                    message_id = msg.get("Message-ID", "").strip()
                    
                    headers_dict = {}
                    for h in ["list-unsubscribe", "list-unsubscribe-post", "precedence", "x-campaign", "x-mailer", "message-id"]:
                        v = msg.get(h)
                        if v:
                            headers_dict[h] = v
                    if message_id and "message-id" not in headers_dict:
                        headers_dict["message-id"] = message_id

                    emails_list.append({
                        "id": uid_str,
                        "uid": uid_str,
                        "message_id": message_id,
                        "subject": subject or "(No Subject)",
                        "sender": sender or "(Unknown Sender)",
                        "recipient": recipient,
                        "date": date_str,
                        "size_bytes": size_bytes,
                        "headers": headers_dict,
                        "folder": folder
                    })

        if progress_callback:
            progress_callback(len(emails_list), len(uids_to_fetch), "Completed scanning")

        return emails_list

    def delete_emails(self, folder: str, uids: List[str], permanent: bool = False) -> Tuple[int, List[str]]:
        r"""
        Delete emails by UID.
        If permanent=False: moves to Trash/Bin (recoverable).
        If permanent=True: flags \Deleted and expunges.
        Returns: (count_succeeded, errors)
        """
        if not self.client:
            raise RuntimeError("IMAP client not connected")

        if not uids:
            return 0, []

        res, _ = self.client.select(f'"{folder}"', readonly=False)
        if res != "OK":
            res, _ = self.client.select(folder, readonly=False)

        uid_set = ",".join(uids)
        errors = []
        deleted_count = 0

        try:
            if not permanent:
                trash_target = self.trash_folder or self._detect_trash_folder()
                # Try UID MOVE first (RFC 6855) if server supports it, else COPY then mark \Deleted
                res, data = self.client.uid("copy", uid_set, f'"{trash_target}"')
                if res != "OK":
                    # Try without quotes
                    res, data = self.client.uid("copy", uid_set, trash_target)

                if res == "OK":
                    # Mark original as deleted and expunge
                    self.client.uid("store", uid_set, "+FLAGS", "(\\Deleted)")
                    self.client.expunge()
                    deleted_count = len(uids)
                else:
                    errors.append(f"Could not move to trash ({trash_target}): {data}")
            else:
                # Permanent deletion: mark \Deleted and EXPUNGE
                res, data = self.client.uid("store", uid_set, "+FLAGS", "(\\Deleted)")
                if res == "OK":
                    self.client.expunge()
                    deleted_count = len(uids)
                else:
                    errors.append(f"Failed to flag emails for permanent deletion: {data}")
        except Exception as e:
            errors.append(str(e))

        return deleted_count, errors

    def restore_emails(self, source_folder: str, trash_folder: str, emails: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        """
        Restore emails from trash_folder back to source_folder (e.g. INBOX).
        Searches for each email in trash_folder by Message-ID (or Subject fallback) and copies it back.
        Returns: (count_succeeded, errors)
        """
        if not self.client:
            raise RuntimeError("IMAP client not connected")

        if not emails:
            return 0, []

        target_trash = trash_folder or self.trash_folder or self._detect_trash_folder()
        res, _ = self.client.select(f'"{target_trash}"', readonly=False)
        if res != "OK":
            res, _ = self.client.select(target_trash, readonly=False)
            if res != "OK":
                return 0, [f"Could not open trash folder {target_trash}"]

        restored_count = 0
        errors = []

        for mail in emails:
            msg_id = mail.get("message_id") or mail.get("headers", {}).get("message-id", "")
            subject = mail.get("subject", "")
            found_uids = []

            # 1. Search by Message-ID in trash
            if msg_id:
                clean_msg_id = msg_id.replace('"', '').replace('\\', '').strip()
                if clean_msg_id:
                    try:
                        res, search_data = self.client.uid("search", None, f'HEADER Message-ID "{clean_msg_id}"')
                        if res == "OK" and search_data and search_data[0]:
                            found_uids = search_data[0].split()
                    except Exception:
                        pass

            # 2. Fallback search by Subject in trash
            if not found_uids and subject and subject != "(No Subject)":
                try:
                    clean_subject = re.sub(r'["\\]', '', subject)[:50].strip()
                    if clean_subject:
                        res, search_data = self.client.uid("search", None, f'SUBJECT "{clean_subject}"')
                        if res == "OK" and search_data and search_data[0]:
                            found_uids = search_data[0].split()
                except Exception:
                    pass

            # 3. Move found UID from trash back to source_folder
            if found_uids:
                target_uid = found_uids[-1].decode("ascii") if isinstance(found_uids[-1], bytes) else str(found_uids[-1])
                try:
                    res, copy_data = self.client.uid("copy", target_uid, f'"{source_folder}"')
                    if res != "OK":
                        res, copy_data = self.client.uid("copy", target_uid, source_folder)

                    if res == "OK":
                        self.client.uid("store", target_uid, "+FLAGS", "(\\Deleted)")
                        self.client.expunge()
                        restored_count += 1
                    else:
                        errors.append(f"Failed to copy email back to {source_folder}: {copy_data}")
                except Exception as e:
                    errors.append(f"Error restoring email {mail.get('id')}: {str(e)}")
            else:
                errors.append(f"Could not locate email '{subject[:30]}' in {target_trash}")

        return restored_count, errors

    def disconnect(self):
        """Disconnect and close IMAP session."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            try:
                self.client.logout()
            except Exception:
                pass
            self.client = None
