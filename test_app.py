"""
test_app.py - End-to-end integration tests for Cleanbox API.
"""

from fastapi.testclient import TestClient
from app import app, SESSIONS
import time

client = TestClient(app)

def test_get_presets():
    res = client.get("/api/presets")
    assert res.status_code == 200
    data = res.json()
    assert "gmail" in data["presets"]
    assert "hotmail" in data["presets"]
    assert data["presets"]["gmail"]["host"] == "imap.gmail.com"
    assert data["presets"]["hotmail"]["host"] == "outlook.office365.com"
    print("✓ /api/presets returns correct Gmail and Hotmail configurations")

def test_sandbox_connect_and_scan():
    # 1. Connect to demo mode
    res = client.post("/api/connect", json={
        "provider": "gmail",
        "email": "demo.user@sandbox.com",
        "is_demo": True
    })
    assert res.status_code == 200
    conn_data = res.json()
    assert conn_data["success"] is True
    session_id = conn_data["session_id"]
    assert "INBOX" in conn_data["folders"]
    print("✓ /api/connect successfully opened Sandbox session")

    # 2. Trigger scan
    res = client.post("/api/scan", json={
        "session_id": session_id,
        "folder": "INBOX",
        "max_emails": 500
    })
    assert res.status_code == 200

    # Wait for scan background task
    time.sleep(0.5)

    # 3. Check status
    res = client.get(f"/api/scan/status?session_id={session_id}")
    assert res.status_code == 200
    st_data = res.json()
    assert st_data["status"]["state"] == "complete"
    stats = st_data["stats"]
    assert stats["total_count"] == 20
    assert stats["marketing_count"] > 0
    assert stats["protected_count"] > 0
    assert stats["large_count"] > 0
    print(f"✓ Scan completed: {stats['total_count']} emails analyzed ({stats['total_size_formatted']}), "
          f"{stats['marketing_count']} marketing ({stats['marketing_size_formatted']}), "
          f"{stats['protected_count']} protected, {stats['large_count']} large (>1MB)")

    # 4. Check protected emails integrity
    res = client.get(f"/api/emails?session_id={session_id}&category=protected")
    assert res.status_code == 200
    prot_data = res.json()
    for mail in prot_data["emails"]:
        assert mail["is_protected"] is True
        assert mail["is_marketing"] is False
        assert len(mail["protection_reasons"]) > 0
    print(f"✓ Verified {len(prot_data['emails'])} protected emails (receipts/bookings) are safeguarded")

    # 5. Check large emails flagging
    res = client.get(f"/api/emails?session_id={session_id}&category=large&sort_by=size_desc")
    assert res.status_code == 200
    large_data = res.json()
    assert len(large_data["emails"]) > 0
    # First email should be the largest
    assert large_data["emails"][0]["size_bytes"] >= large_data["emails"][-1]["size_bytes"]
    print(f"✓ Verified large emails sorting: Top largest email is {large_data['emails'][0]['size_formatted']}")

    # 6. Test Dry-Run deletion preview
    # Pick marketing emails to delete
    res_mkt = client.get(f"/api/emails?session_id={session_id}&category=marketing")
    mkt_ids = [m["id"] for m in res_mkt.json()["emails"]]
    
    # Intentionally slip in a protected email ID to test safety guard!
    protected_id = prot_data["emails"][0]["id"]
    test_ids = mkt_ids[:3] + [protected_id]

    res_del_preview = client.post("/api/delete", json={
        "session_id": session_id,
        "email_ids": test_ids,
        "dry_run": True
    })
    assert res_del_preview.status_code == 200
    dry_data = res_del_preview.json()
    assert dry_data["dry_run"] is True
    assert dry_data["blocked_protected_count"] == 1, "Protected email MUST be blocked from deletion!"
    assert dry_data["target_count"] == 3
    print("✓ Dry-run deletion correctly blocked protected email and previewed space to free")

    # 7. Test actual deletion
    res_delete = client.post("/api/delete", json={
        "session_id": session_id,
        "email_ids": test_ids,
        "permanent": False,
        "dry_run": False
    })
    assert res_delete.status_code == 200
    del_data = res_delete.json()
    assert del_data["success"] is True
    assert del_data["deleted_count"] == 3
    assert del_data["blocked_protected_count"] == 1
    assert del_data["freed_bytes"] > 0
    print(f"✓ Deletion succeeded: Freed {del_data['freed_formatted']} and safely preserved protected emails")

    # 8. Check sender aggregation
    res_senders = client.get(f"/api/senders?session_id={session_id}")
    assert res_senders.status_code == 200
    senders = res_senders.json()["senders"]
    assert len(senders) > 0
    print(f"✓ Senders endpoint returned {len(senders)} aggregated sender profiles")

    # 9. Test Undo Move to Bin
    undo_res = client.post("/api/undo", json={
        "session_id": session_id,
        "batch_id": del_data.get("batch_id")
    })
    assert undo_res.status_code == 200
    undo_data = undo_res.json()
    assert undo_data["success"] is True
    assert undo_data["restored_count"] == 3
    # Check that total emails returned to 20
    st_res = client.get(f"/api/scan/status?session_id={session_id}")
    assert st_res.json()["stats"]["total_count"] == 20
    print(f"✓ Successfully tested Undo: Restored {undo_data['restored_count']} emails back from Bin to INBOX")

    # 10. Check Undo History
    hist_res = client.get(f"/api/undo/history?session_id={session_id}")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["history"]) >= 1
    assert hist_data["history"][0]["status"] == "restored"
    print("✓ Verified /api/undo/history tracks batch status transitions")


def test_scan_entire_inbox_from_start():
    # Connect
    res = client.post("/api/connect", json={
        "provider": "gmail",
        "email": "demo.fullscan@sandbox.com",
        "is_demo": True
    })
    session_id = res.json()["session_id"]

    # Trigger scan for ENTIRE inbox from the start (oldest first)
    res_scan = client.post("/api/scan", json={
        "session_id": session_id,
        "folder": "INBOX",
        "max_emails": 0,
        "order": "oldest",
        "scan_entire": True
    })
    assert res_scan.status_code == 200
    time.sleep(0.5)

    # Check status
    res_st = client.get(f"/api/scan/status?session_id={session_id}")
    assert res_st.status_code == 200
    st = res_st.json()
    assert st["status"]["state"] == "complete"
    assert st["stats"]["total_count"] == 20

    # Verify oldest email comes first when scanning from the start
    res_emails = client.get(f"/api/emails?session_id={session_id}&category=all&sort_by=date_desc")
    assert res_emails.status_code == 200
    # Also verify raw scanned order
    raw_emails = SESSIONS[session_id]["emails"]
    assert len(raw_emails) == 20
    assert raw_emails[0]["id"] == "mock_20", "First email should be the oldest email (mock_20 from 20 days ago)"
    print("✓ Verified scanning entire inbox from the start: scanned all 20 emails with oldest first")


def test_dry_run_simulation_guarantee():
    res = client.post("/api/connect", json={
        "provider": "gmail",
        "email": "demo.dryrun@sandbox.com",
        "is_demo": True
    })
    session_id = res.json()["session_id"]
    client.post("/api/scan", json={"session_id": session_id, "folder": "INBOX", "max_emails": 0})
    time.sleep(0.5)

    res_emails = client.get(f"/api/emails?session_id={session_id}&category=marketing")
    mkt_ids = [m["id"] for m in res_emails.json()["emails"]]
    initial_count = len(SESSIONS[session_id]["emails"])

    # Perform Dry Run
    res_dry = client.post("/api/delete", json={
        "session_id": session_id,
        "email_ids": mkt_ids,
        "dry_run": True,
        "permanent": False
    })
    assert res_dry.status_code == 200
    dry_data = res_dry.json()
    assert dry_data["dry_run"] is True
    assert dry_data["is_undoable"] is True
    assert "Move to Trash / Bin (Undoable)" in dry_data["mode"]
    assert len(dry_data["targets_sample"]) == len(mkt_ids)
    assert len(dry_data["senders_summary"]) > 0

    # Ensure ABSOLUTELY ZERO emails were deleted during dry run
    after_dry_count = len(SESSIONS[session_id]["emails"])
    assert initial_count == after_dry_count, "Dry run must NOT remove any emails from mailbox!"
    print("✓ Dry run simulation guarantee verified: detailed preview returned and mailbox untouched")


def test_imap_restore_unit():
    from unittest.mock import MagicMock
    from imap_client import MailboxSession

    mailbox = MailboxSession("gmail", "imap.gmail.com", 993, "test@gmail.com", "pw")
    mailbox.client = MagicMock()
    mailbox.trash_folder = "[Gmail]/Trash"
    mailbox.client.select.return_value = ("OK", [b"123"])

    # Simulate search in trash by Message-ID, then copy, store \Deleted, and expunge
    mailbox.client.uid.side_effect = [
        ("OK", [b"101"]),   # search
        ("OK", [b"Copied"]), # copy to source
        ("OK", [b"Stored"]), # store \Deleted in trash
    ]
    mailbox.client.expunge.return_value = ("OK", [b"Expunged"])

    count, errs = mailbox.restore_emails(
        source_folder="INBOX",
        trash_folder="[Gmail]/Trash",
        emails=[{"id": "50", "message_id": "<test@example.com>", "subject": "Test restore"}]
    )
    assert count == 1
    assert len(errs) == 0
    print("✓ IMAP MailboxSession.restore_emails successfully restored email from Trash back to INBOX")


if __name__ == "__main__":
    test_get_presets()
    test_sandbox_connect_and_scan()
    test_scan_entire_inbox_from_start()
    test_dry_run_simulation_guarantee()
    test_imap_restore_unit()
    print("\nALL END-TO-END INTEGRATION TESTS PASSED! 🎉")
