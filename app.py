"""
app.py - FastAPI application for Cleanbox.
Provides REST endpoints and serves the modern Web UI for scanning, classifying,
flagging large emails, and safely deleting marketing emails from Gmail and Hotmail.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from classifier import classify_email, format_bytes, LARGE_SIZE_BYTES_1MB, LARGE_SIZE_BYTES_5MB, LARGE_SIZE_BYTES_10MB
from imap_client import MailboxSession, PRESETS
from mock_data import get_mock_emails

app = FastAPI(
    title="Cleanbox",
    description="Connect to Gmail & Hotmail, detect marketing emails, flag largest emails, protect receipts & bookings, and free up storage.",
    version="1.0.0"
)

# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# In-memory storage for active sessions
# Key: session_id -> { "session": MailboxSession or None, "is_demo": bool, "emails": [...], "status": {...}, "undo_history": [...] }
SESSIONS: Dict[str, Dict[str, Any]] = {}


# --- Pydantic Request Models ---
class ConnectRequest(BaseModel):
    provider: str = Field(..., description="gmail, hotmail, or custom")
    email: str = Field(..., description="Email address")
    password: Optional[str] = Field("", description="App password")
    host: Optional[str] = None
    port: Optional[int] = 993
    ssl: Optional[bool] = True
    is_demo: Optional[bool] = False


class ScanRequest(BaseModel):
    session_id: str
    folder: Optional[str] = "INBOX"
    max_emails: Optional[int] = 500  # 0 or None means entire inbox
    order: Optional[str] = "newest"  # "newest" or "oldest" ("start")
    scan_entire: Optional[bool] = False


class DeleteRequest(BaseModel):
    session_id: str
    email_ids: List[str]
    permanent: Optional[bool] = False
    dry_run: Optional[bool] = False
    override_protection: Optional[bool] = False


class UndoRequest(BaseModel):
    session_id: str
    batch_id: Optional[str] = None


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Cleanbox is running. Place index.html in static/</h1>")


@app.get("/api/presets")
async def get_presets():
    """Return provider configurations and setup guides."""
    return {
        "presets": {
            "gmail": {
                "name": "Gmail",
                "host": "imap.gmail.com",
                "port": 993,
                "ssl": True,
                "guide": {
                    "title": "How to connect Gmail",
                    "steps": [
                        "1. Go to your Google Account (myaccount.google.com)",
                        "2. Select Security -> 2-Step Verification (ensure it is ON)",
                        "3. Scroll to the bottom and click 'App passwords'",
                        "4. Create a new password named 'Cleanbox'",
                        "5. Copy and paste the 16-character code here."
                    ],
                    "help_url": "https://myaccount.google.com/apppasswords"
                }
            },
            "hotmail": {
                "name": "Hotmail / Outlook / Live",
                "host": "outlook.office365.com",
                "port": 993,
                "ssl": True,
                "guide": {
                    "title": "How to connect Hotmail / Outlook",
                    "steps": [
                        "1. Go to account.microsoft.com/security",
                        "2. Select 'Advanced security options'",
                        "3. Under 'App passwords', click 'Create a new app password'",
                        "4. Copy and paste the generated password here."
                    ],
                    "help_url": "https://account.live.com/proofs/manage/additional"
                }
            },
            "custom": {
                "name": "Custom IMAP",
                "host": "",
                "port": 993,
                "ssl": True,
                "guide": {
                    "title": "Custom IMAP connection",
                    "steps": [
                        "Enter your provider's IMAP server address, port (usually 993), and credentials."
                    ]
                }
            }
        }
    }


@app.post("/api/connect")
async def connect_email(req: ConnectRequest):
    """Authenticate with email server or launch sandbox demo mode."""
    session_id = str(uuid.uuid4())

    if req.is_demo:
        # Create Sandbox session with mock mailbox
        SESSIONS[session_id] = {
            "session": None,
            "is_demo": True,
            "email": req.email or "demo@example.com",
            "provider": req.provider or "gmail",
            "folders": ["INBOX", "Archive", "Promotions", "Spam"],
            "trash_folder": "Trash",
            "emails": [],
            "status": {"state": "ready", "message": "Demo mailbox ready for scanning", "progress": 0}
        }
        return {
            "success": True,
            "session_id": session_id,
            "message": "Connected to Sandbox Demo Mailbox",
            "folders": ["INBOX", "Archive", "Promotions", "Spam"],
            "is_demo": True
        }

    provider_info = PRESETS.get(req.provider.lower(), PRESETS["custom"])
    host = req.host or provider_info["host"]
    port = req.port or provider_info["port"]
    use_ssl = req.ssl if req.ssl is not None else provider_info["ssl"]

    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Email and App Password are required.")

    mailbox = MailboxSession(
        provider=req.provider,
        host=host,
        port=port,
        email_addr=req.email.strip(),
        password=req.password.strip(),
        use_ssl=use_ssl
    )

    success, msg = mailbox.connect()
    if not success:
        raise HTTPException(status_code=401, detail=msg)

    folders = mailbox.list_folders()

    SESSIONS[session_id] = {
        "session": mailbox,
        "is_demo": False,
        "email": req.email.strip(),
        "provider": req.provider,
        "folders": folders,
        "trash_folder": mailbox.trash_folder,
        "emails": [],
        "status": {"state": "ready", "message": "Connected", "progress": 0}
    }

    return {
        "success": True,
        "session_id": session_id,
        "message": f"Successfully connected to {req.email}",
        "folders": folders,
        "trash_folder": mailbox.trash_folder,
        "is_demo": False
    }


def _run_scan_task(session_id: str, folder: str, max_emails: Optional[int], order: str = "newest", scan_entire: bool = False):
    """Background scanner and classifier."""
    sess_data = SESSIONS.get(session_id)
    if not sess_data:
        return

    effective_max = 0 if (scan_entire or max_emails == 0) else (max_emails or 500)
    if effective_max == 0:
        scope_msg = "entire inbox from the start (oldest first)" if order in ("oldest", "start") else "entire inbox (newest first)"
    else:
        scope_msg = f"{effective_max} emails from the start" if order in ("oldest", "start") else f"latest {effective_max} emails"

    sess_data["status"] = {"state": "scanning", "message": f"Scanning {scope_msg}...", "progress": 5}

    try:
        raw_emails = []
        if sess_data["is_demo"]:
            raw_emails = get_mock_emails(max_emails=effective_max, order=order)
            sess_data["status"] = {"state": "scanning", "message": f"Processing mock mailbox ({scope_msg})...", "progress": 60}
        else:
            mailbox: MailboxSession = sess_data["session"]
            def on_progress(done, total, msg):
                pct = int((done / max(total, 1)) * 90) + 5
                sess_data["status"] = {
                    "state": "scanning",
                    "message": f"{msg} ({done}/{total})",
                    "progress": pct
                }

            raw_emails = mailbox.scan_emails(folder=folder, max_emails=effective_max, order=order, progress_callback=on_progress)

        sess_data["status"] = {"state": "classifying", "message": "Classifying emails...", "progress": 92}

        # Run classifier on every email
        classified_emails = []
        total_size = 0
        marketing_size = 0
        marketing_count = 0
        protected_count = 0
        large_count = 0
        large_size = 0

        for mail in raw_emails:
            classification = classify_email(
                subject=mail.get("subject", ""),
                sender=mail.get("sender", ""),
                headers=mail.get("headers", {}),
                size_bytes=mail.get("size_bytes", 0),
                body_snippet=mail.get("body_snippet", "")
            )

            full_record = {
                **mail,
                **classification
            }
            classified_emails.append(full_record)

            size = full_record["size_bytes"]
            total_size += size

            if full_record["is_protected"]:
                protected_count += 1
            elif full_record["is_marketing"]:
                marketing_count += 1
                marketing_size += size

            if full_record["is_large"]:
                large_count += 1
                large_size += size

        sess_data["emails"] = classified_emails
        sess_data["stats"] = {
            "total_count": len(classified_emails),
            "total_size_bytes": total_size,
            "total_size_formatted": format_bytes(total_size),
            "marketing_count": marketing_count,
            "marketing_size_bytes": marketing_size,
            "marketing_size_formatted": format_bytes(marketing_size),
            "protected_count": protected_count,
            "large_count": large_count,
            "large_size_bytes": large_size,
            "large_size_formatted": format_bytes(large_size)
        }
        sess_data["status"] = {"state": "complete", "message": "Scan finished!", "progress": 100}

    except Exception as e:
        sess_data["status"] = {"state": "error", "message": f"Scan error: {str(e)}", "progress": 0}


@app.post("/api/scan")
async def start_scan(req: ScanRequest, bg_tasks: BackgroundTasks):
    """Trigger email scanning in the background."""
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found. Please connect first.")

    bg_tasks.add_task(
        _run_scan_task,
        req.session_id,
        req.folder or "INBOX",
        req.max_emails,
        req.order or "newest",
        req.scan_entire or False
    )
    return {"status": "started", "message": "Scanning started"}


@app.get("/api/scan/status")
async def scan_status(session_id: str):
    """Poll scanning progress."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sess_data = SESSIONS[session_id]
    return {
        "status": sess_data.get("status", {}),
        "stats": sess_data.get("stats", {})
    }


@app.get("/api/emails")
async def list_emails(
    session_id: str,
    category: Optional[str] = "all",     # all, marketing, protected, large
    min_size_mb: Optional[float] = 0.0,
    search: Optional[str] = None,
    sender: Optional[str] = None,
    sort_by: Optional[str] = "size_desc", # size_desc, size_asc, date_desc, date_asc, score_desc
    limit: Optional[int] = 200,
    offset: Optional[int] = 0
):
    """Retrieve and filter scanned emails."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    emails = SESSIONS[session_id].get("emails", [])
    filtered = []

    search_query = (search or "").lower().strip()
    sender_filter = (sender or "").lower().strip()
    min_bytes = int((min_size_mb or 0) * 1024 * 1024)

    for mail in emails:
        # Category filter
        if category == "marketing" and not mail["is_marketing"]:
            continue
        if category == "protected" and not mail["is_protected"]:
            continue
        if category == "large" and not mail["is_large"]:
            continue

        # Min size filter
        if min_bytes > 0 and mail["size_bytes"] < min_bytes:
            continue

        # Sender filter
        if sender_filter and sender_filter not in mail["sender"].lower():
            continue

        # Search query
        if search_query:
            subj = mail["subject"].lower()
            sndr = mail["sender"].lower()
            snip = (mail.get("body_snippet") or "").lower()
            if search_query not in subj and search_query not in sndr and search_query not in snip:
                continue

        filtered.append(mail)

    # Sorting
    if sort_by == "size_desc":
        filtered.sort(key=lambda x: x["size_bytes"], reverse=True)
    elif sort_by == "size_asc":
        filtered.sort(key=lambda x: x["size_bytes"], reverse=False)
    elif sort_by == "score_desc":
        filtered.sort(key=lambda x: x.get("marketing_score", 0), reverse=True)
    # Default: already in date order from scan, but if requested:
    elif sort_by == "date_desc":
        pass

    total_filtered = len(filtered)
    total_filtered_size = sum(x["size_bytes"] for x in filtered)
    paged = filtered[offset : offset + limit]

    return {
        "total": total_filtered,
        "total_size_bytes": total_filtered_size,
        "total_size_formatted": format_bytes(total_filtered_size),
        "limit": limit,
        "offset": offset,
        "emails": paged
    }


@app.get("/api/senders")
async def list_top_senders(session_id: str):
    """Group scanned emails by sender to allow bulk cleanup by sender."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    emails = SESSIONS[session_id].get("emails", [])
    sender_map: Dict[str, Dict[str, Any]] = {}

    for mail in emails:
        sndr = mail["sender"]
        if sndr not in sender_map:
            sender_map[sndr] = {
                "sender": sndr,
                "count": 0,
                "total_size_bytes": 0,
                "marketing_count": 0,
                "protected_count": 0,
                "email_ids": []
            }

        sender_map[sndr]["count"] += 1
        sender_map[sndr]["total_size_bytes"] += mail["size_bytes"]
        sender_map[sndr]["email_ids"].append(mail["id"])
        if mail["is_marketing"]:
            sender_map[sndr]["marketing_count"] += 1
        if mail["is_protected"]:
            sender_map[sndr]["protected_count"] += 1

    senders_list = list(sender_map.values())
    for s in senders_list:
        s["total_size_formatted"] = format_bytes(s["total_size_bytes"])
        s["is_primarily_marketing"] = s["marketing_count"] > 0 and s["protected_count"] == 0

    # Sort senders taking up the most space first
    senders_list.sort(key=lambda x: x["total_size_bytes"], reverse=True)
    return {"senders": senders_list[:50]}


@app.post("/api/delete")
async def delete_emails(req: DeleteRequest):
    """
    Safely delete or move emails to trash.
    PROTECTED EMAILS CANNOT BE DELETED unless override_protection=True.
    """
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess_data = SESSIONS[req.session_id]
    emails = sess_data.get("emails", [])
    
    # Map by id
    email_dict = {m["id"]: m for m in emails}
    
    targets_to_delete = []
    blocked_protected = []
    bytes_to_free = 0

    for eid in req.email_ids:
        mail = email_dict.get(eid)
        if not mail:
            continue

        if mail["is_protected"] and not req.override_protection:
            blocked_protected.append({
                "id": eid,
                "subject": mail["subject"],
                "reason": mail["protection_reasons"]
            })
            continue

        targets_to_delete.append(mail)
        bytes_to_free += mail["size_bytes"]

    # If Dry Run, return preview without executing
    if req.dry_run:
        senders_summary = {}
        for m in targets_to_delete:
            s = m["sender"]
            if s not in senders_summary:
                senders_summary[s] = {"sender": s, "count": 0, "size_bytes": 0}
            senders_summary[s]["count"] += 1
            senders_summary[s]["size_bytes"] += m["size_bytes"]

        senders_list = sorted(senders_summary.values(), key=lambda x: x["size_bytes"], reverse=True)
        for s in senders_list:
            s["size_formatted"] = format_bytes(s["size_bytes"])

        return {
            "dry_run": True,
            "target_count": len(targets_to_delete),
            "space_to_free_bytes": bytes_to_free,
            "space_to_free_formatted": format_bytes(bytes_to_free),
            "blocked_protected_count": len(blocked_protected),
            "blocked_protected_examples": blocked_protected[:5],
            "mode": "Permanent Deletion (EXPUNGE)" if req.permanent else "Move to Trash / Bin (Undoable)",
            "is_undoable": not (req.permanent or False),
            "targets_sample": [
                {
                    "id": m["id"],
                    "subject": m["subject"],
                    "sender": m["sender"],
                    "size_formatted": m.get("size_formatted") or format_bytes(m["size_bytes"]),
                    "date": m.get("date", "")
                }
                for m in targets_to_delete[:50]
            ],
            "senders_summary": senders_list[:10]
        }

    # Execute deletion
    deleted_uids = [m["id"] for m in targets_to_delete]
    errors = []
    freed_bytes = 0
    actual_deleted_count = 0
    batch_id = str(uuid.uuid4())
    folder = targets_to_delete[0].get("folder", "INBOX") if targets_to_delete else "INBOX"

    if sess_data["is_demo"]:
        # Mock deletion in demo session
        uids_set = set(deleted_uids)
        sess_data["emails"] = [m for m in emails if m["id"] not in uids_set]
        actual_deleted_count = len(deleted_uids)
        freed_bytes = bytes_to_free
        if not req.permanent:
            sess_data.setdefault("bin", []).extend(targets_to_delete)
    else:
        mailbox: MailboxSession = sess_data["session"]
        if not mailbox:
            raise HTTPException(status_code=400, detail="Mailbox session disconnected")

        # Call IMAP delete
        actual_deleted_count, errors = mailbox.delete_emails(folder, deleted_uids, permanent=req.permanent or False)
        
        if actual_deleted_count > 0:
            freed_bytes = bytes_to_free
            deleted_set = set(deleted_uids[:actual_deleted_count])
            sess_data["emails"] = [m for m in emails if m["id"] not in deleted_set]

    # Record in undo history
    if actual_deleted_count > 0:
        undo_batch = {
            "batch_id": batch_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_folder": folder,
            "trash_folder": sess_data.get("trash_folder") or "Trash",
            "count": actual_deleted_count,
            "freed_bytes": freed_bytes,
            "freed_formatted": format_bytes(freed_bytes),
            "emails": [dict(m) for m in targets_to_delete[:actual_deleted_count]],
            "permanent": req.permanent or False,
            "status": "permanent_expunged" if req.permanent else "in_bin"
        }
        if "undo_history" not in sess_data:
            sess_data["undo_history"] = []
        sess_data["undo_history"].insert(0, undo_batch)

    # Recalculate stats
    remaining = sess_data["emails"]
    tot_size = sum(m["size_bytes"] for m in remaining)
    mkt_size = sum(m["size_bytes"] for m in remaining if m["is_marketing"])
    lrg_size = sum(m["size_bytes"] for m in remaining if m["is_large"])

    sess_data["stats"] = {
        "total_count": len(remaining),
        "total_size_bytes": tot_size,
        "total_size_formatted": format_bytes(tot_size),
        "marketing_count": sum(1 for m in remaining if m["is_marketing"]),
        "marketing_size_bytes": mkt_size,
        "marketing_size_formatted": format_bytes(mkt_size),
        "protected_count": sum(1 for m in remaining if m["is_protected"]),
        "large_count": sum(1 for m in remaining if m["is_large"]),
        "large_size_bytes": lrg_size,
        "large_size_formatted": format_bytes(lrg_size)
    }

    return {
        "success": True,
        "deleted_count": actual_deleted_count,
        "freed_bytes": freed_bytes,
        "freed_formatted": format_bytes(freed_bytes),
        "blocked_protected_count": len(blocked_protected),
        "blocked_protected": blocked_protected,
        "remaining_count": len(remaining),
        "errors": errors,
        "batch_id": batch_id if not req.permanent else None,
        "can_undo": not (req.permanent or False),
        "mode": "Permanent Deletion (EXPUNGE)" if req.permanent else "Moved to Trash / Bin (Undoable)"
    }


@app.post("/api/undo")
async def undo_delete(req: UndoRequest):
    """
    Restore emails moved to the Trash/Bin back to their original folder (e.g. INBOX).
    """
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess_data = SESSIONS[req.session_id]
    undo_history = sess_data.get("undo_history", [])
    if not undo_history:
        raise HTTPException(status_code=400, detail="No deletion history to undo.")

    target_batch = None
    if req.batch_id:
        for b in undo_history:
            if b["batch_id"] == req.batch_id:
                target_batch = b
                break
        if not target_batch:
            raise HTTPException(status_code=404, detail="Undo batch not found")
    else:
        for b in undo_history:
            if b.get("status") == "in_bin":
                target_batch = b
                break
        if not target_batch:
            raise HTTPException(status_code=400, detail="No undoable batches in Bin. All batches have been restored or permanently deleted.")

    if target_batch.get("status") == "restored":
        raise HTTPException(status_code=400, detail="This batch has already been restored.")
    if target_batch.get("permanent"):
        raise HTTPException(status_code=400, detail="Cannot undo permanently expunged emails.")

    emails_to_restore = target_batch["emails"]
    restored_count = 0
    errors = []

    if sess_data["is_demo"]:
        current_ids = {m["id"] for m in sess_data["emails"]}
        restored_list = []
        for m in emails_to_restore:
            if m["id"] not in current_ids:
                restored_list.append(m)
        sess_data["emails"].extend(restored_list)
        restored_count = len(restored_list)
        restored_ids = {m["id"] for m in restored_list}
        sess_data["bin"] = [m for m in sess_data.get("bin", []) if m["id"] not in restored_ids]
    else:
        mailbox: MailboxSession = sess_data.get("session")
        if not mailbox:
            raise HTTPException(status_code=400, detail="Mailbox session disconnected")

        source_folder = target_batch.get("source_folder", "INBOX")
        trash_folder = target_batch.get("trash_folder") or sess_data.get("trash_folder", "Trash")
        restored_count, errors = mailbox.restore_emails(
            source_folder=source_folder,
            trash_folder=trash_folder,
            emails=emails_to_restore
        )

        current_ids = {m["id"] for m in sess_data["emails"]}
        for m in emails_to_restore[:restored_count]:
            if m["id"] not in current_ids:
                sess_data["emails"].append(m)

    target_batch["status"] = "restored"

    # Recalculate stats
    remaining = sess_data["emails"]
    tot_size = sum(m["size_bytes"] for m in remaining)
    mkt_size = sum(m["size_bytes"] for m in remaining if m["is_marketing"])
    lrg_size = sum(m["size_bytes"] for m in remaining if m["is_large"])

    sess_data["stats"] = {
        "total_count": len(remaining),
        "total_size_bytes": tot_size,
        "total_size_formatted": format_bytes(tot_size),
        "marketing_count": sum(1 for m in remaining if m["is_marketing"]),
        "marketing_size_bytes": mkt_size,
        "marketing_size_formatted": format_bytes(mkt_size),
        "protected_count": sum(1 for m in remaining if m["is_protected"]),
        "large_count": sum(1 for m in remaining if m["is_large"]),
        "large_size_bytes": lrg_size,
        "large_size_formatted": format_bytes(lrg_size)
    }

    return {
        "success": True,
        "restored_count": restored_count,
        "batch_id": target_batch["batch_id"],
        "folder": target_batch.get("source_folder", "INBOX"),
        "errors": errors,
        "message": f"Successfully restored {restored_count} email(s) from Bin back to {target_batch.get('source_folder', 'INBOX')}."
    }


@app.get("/api/undo/history")
async def get_undo_history(session_id: str):
    """Retrieve history of batches moved to Bin or deleted."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    sess_data = SESSIONS[session_id]
    batches = sess_data.get("undo_history", [])

    summary = []
    for b in batches:
        summary.append({
            "batch_id": b["batch_id"],
            "timestamp": b["timestamp"],
            "count": b["count"],
            "freed_formatted": b["freed_formatted"],
            "source_folder": b["source_folder"],
            "trash_folder": b.get("trash_folder", "Trash"),
            "status": b["status"],
            "permanent": b.get("permanent", False),
            "sample_subjects": [m["subject"] for m in b.get("emails", [])[:4]]
        })
    return {
        "history": summary,
        "active_bin_count": sum(1 for b in batches if b["status"] == "in_bin")
    }


@app.post("/api/disconnect")
async def disconnect_session(session_id: str):
    """Disconnect and clean up session."""
    if session_id in SESSIONS:
        sess = SESSIONS.pop(session_id)
        if sess.get("session"):
            sess["session"].disconnect()
    return {"success": True, "message": "Disconnected"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Cleanbox server on http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
