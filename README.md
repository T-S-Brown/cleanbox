<div align="center">
  <img src="email_cleaner_logo.png" alt="Cleanbox logo" width="180" />

  # Cleanbox

  **Safely reclaim space from your inbox.**

  [![Tests](https://github.com/T-S-Brown/cleanbox/actions/workflows/test.yml/badge.svg)](https://github.com/T-S-Brown/cleanbox/actions/workflows/test.yml)
  [![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![IMAP](https://img.shields.io/badge/Mail-IMAP%20over%20SSL-4B5563)](https://www.rfc-editor.org/rfc/rfc3501)
  [![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)
</div>

Cleanbox is a local, privacy-first web application for finding and removing bulk marketing emails while protecting receipts, bookings, financial records, account alerts, and other important messages. It also surfaces the largest messages so you can reclaim the most storage with the least effort.

> Cleanbox is designed to run locally. It does not upload your mailbox to a third-party service. Use provider app passwords where available, and review the dry-run results before deleting anything.

## What it does

- Connects to Gmail, Hotmail/Outlook/Live, Office 365, or any custom IMAP server.
- Provides a sandbox demo with realistic sample messages and no credentials.
- Detects newsletters and promotional mail using unsubscribe headers, bulk headers, marketing platforms, sender patterns, and promotional language.
- Protects purchases, receipts, invoices, travel, deliveries, financial records, healthcare, legal documents, and security codes with higher-priority rules.
- Flags emails larger than 1 MB, 5 MB, and 10 MB, with largest-first sorting.
- Scans the entire inbox from the oldest message or limits scans to a selected batch.
- Offers a non-destructive dry run, move-to-trash deletion, batch undo, and an explicit permanent-delete option.
- Groups marketing email by sender for quick cleanup.

## Quick start

Requirements: Python 3.9 or newer.

```bash
git clone https://github.com/T-S-Brown/cleanbox.git
cd cleanbox
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python start.py
```

Open [http://localhost:8000](http://localhost:8000). To explore the app without connecting an account, choose the sandbox demo.

## Account access

Cleanbox connects directly to your mailbox over IMAP with SSL. For Gmail and Microsoft accounts, create an app password rather than using your primary account password:

- [Google app passwords](https://myaccount.google.com/apppasswords)
- [Microsoft account security](https://account.live.com/proofs/manage/additional)

Credentials are used only to establish the local IMAP session. Do not commit credentials, `.env` files, or app passwords to a repository.

## Safety model

Cleanbox applies protection rules before marketing rules. If a message looks like both a promotion and a purchase confirmation, booking, receipt, financial record, or security notification, it is treated as protected. Always use the dry run and review selected messages before confirming deletion.

Moving messages to Trash is reversible through Cleanbox's undo history when supported by the provider. Permanent deletion/EXPUNGE is irreversible.

## Tests

Run the test suite locally with:

```bash
python -m pytest -q
```

GitHub Actions runs the suite on Python 3.9 and 3.13 for pushes and pull requests.

## Project structure

```text
cleanbox/
├── app.py              # FastAPI server and REST endpoints
├── classifier.py       # Protection, marketing, and size classification rules
├── imap_client.py      # IMAP-over-SSL mailbox client
├── mock_data.py        # Sandbox mailbox data
├── start.py            # Local launcher with browser startup
├── requirements.txt    # Python dependencies
├── test_classifier.py  # Classification tests
├── test_app.py         # API integration tests
└── static/             # Frontend HTML, JavaScript, and CSS
```

## License

Cleanbox is licensed under the [GNU Affero General Public License v3.0](LICENSE). See the license file for the complete terms.

<div align="center">
  <sub>Built for a cleaner, calmer inbox.</sub>
</div>
