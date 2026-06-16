# services/sheets_service.py
# Google Sheets integration for logging editorial comments and edit proposals.
# Uses the same Firebase service account credentials to authenticate with
# the Google Sheets API. Creates the spreadsheet on first use and shares
# it with the configured owner email.

import logging
import os

import gspread
from google.oauth2.service_account import Credentials


logger = logging.getLogger(__name__)


# ========================================================================
#   Configuration
# ========================================================================

# Email to share the spreadsheet with (gets edit access)
SHEET_OWNER_EMAIL = "annie@annielytics.com"

# Spreadsheet name
SPREADSHEET_NAME = "Auditmaton: Ads - Editorial Feedback"

# Column headers for each tab
COMMENTS_HEADERS = [
    "Timestamp",
    "Author",
    "Check ID",
    "Content Path",
    "Selected Text",
    "Comment",
    "Status",
]

PROPOSALS_HEADERS = [
    "Timestamp",
    "Proposed By",
    "Check ID",
    "Field Path",
    "Original Text",
    "Proposed Text",
    "Status",
    "Reviewed By",
    "Review Note",
]

# Google API scopes needed for Sheets + Drive (to create/share files)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ========================================================================
#   Client Initialization
# ========================================================================

# Module-level cache so we only authenticate once per process
_client = None
_spreadsheet = None


def _get_client():
    """
    Returns an authenticated gspread client using the Firebase service account.

    Uses the GOOGLE_APPLICATION_CREDENTIALS environment variable to locate
    the service account JSON key file. Returns None if credentials are
    not configured.

    Returns:
        gspread.Client or None: Authenticated client, or None if unavailable.
    """
    global _client

    if _client is not None:
        return _client

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set — Sheets logging disabled")
        return None

    try:
        credentials = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        _client = gspread.authorize(credentials)
        logger.info("Google Sheets client initialized")
        return _client

    except Exception as e:
        logger.error("Failed to initialize Google Sheets client: %s", e)
        return None


def _get_spreadsheet():
    """
    Returns the editorial feedback spreadsheet, creating it if it doesn't exist.

    On first call, looks for an existing spreadsheet by name. If not found,
    creates a new one with 'Comments' and 'Edit Proposals' tabs, adds column
    headers, and shares it with the owner email.

    Returns:
        gspread.Spreadsheet or None: The spreadsheet, or None if unavailable.
    """
    global _spreadsheet

    if _spreadsheet is not None:
        return _spreadsheet

    client = _get_client()
    if not client:
        return None

    try:

        # Try to open existing spreadsheet
        try:
            _spreadsheet = client.open(SPREADSHEET_NAME)
            logger.info("Opened existing spreadsheet: %s", SPREADSHEET_NAME)
            return _spreadsheet
        except gspread.SpreadsheetNotFound:
            pass

        # Create new spreadsheet
        _spreadsheet = client.create(SPREADSHEET_NAME)
        logger.info("Created new spreadsheet: %s", SPREADSHEET_NAME)

        # Rename default sheet to 'Comments' and add headers
        comments_ws = _spreadsheet.sheet1
        comments_ws.update_title("Comments")
        comments_ws.append_row(COMMENTS_HEADERS)

        # Bold the header row
        comments_ws.format("A1:G1", {"textFormat": {"bold": True}})

        # Freeze the header row
        comments_ws.freeze(rows=1)

        # Create 'Edit Proposals' tab with headers
        proposals_ws = _spreadsheet.add_worksheet(title="Edit Proposals", rows=1000, cols=len(PROPOSALS_HEADERS))
        proposals_ws.append_row(PROPOSALS_HEADERS)

        # Bold the header row
        proposals_ws.format("A1:I1", {"textFormat": {"bold": True}})

        # Freeze the header row
        proposals_ws.freeze(rows=1)

        # Share with the owner
        _spreadsheet.share(SHEET_OWNER_EMAIL, perm_type="user", role="writer")
        logger.info("Shared spreadsheet with %s", SHEET_OWNER_EMAIL)

        return _spreadsheet

    except Exception as e:
        logger.error("Failed to get/create spreadsheet: %s", e)
        return None


# ========================================================================
#   Public API
# ========================================================================

def log_comment(timestamp, author_email, check_id, content_path, selected_text, comment_text):
    """
    Appends a row to the 'Comments' tab of the editorial feedback spreadsheet.

    Args:
        timestamp (str): ISO-format timestamp.
        author_email (str): Email of the comment author.
        check_id (str): The check identifier.
        content_path (str): The data-content-path value.
        selected_text (str): The exact text that was selected.
        comment_text (str): The comment body.
    """

    spreadsheet = _get_spreadsheet()
    if not spreadsheet:
        return

    try:
        ws = spreadsheet.worksheet("Comments")
        ws.append_row([
            timestamp,
            author_email,
            check_id,
            content_path,
            selected_text,
            comment_text,
            "Open",
        ])
        logger.info("Logged comment to Google Sheet: %s by %s", check_id, author_email)

    except Exception as e:
        logger.error("Failed to log comment to Google Sheet: %s", e)


def log_edit_proposal(timestamp, author_email, check_id, field_path, original_text, proposed_text):
    """
    Appends a row to the 'Edit Proposals' tab of the editorial feedback spreadsheet.

    Args:
        timestamp (str): ISO-format timestamp.
        author_email (str): Email of the proposing user.
        check_id (str): The check identifier.
        field_path (str): Dot-notation path to the JSON field.
        original_text (str): The original text being replaced.
        proposed_text (str): The proposed replacement text.
    """

    spreadsheet = _get_spreadsheet()
    if not spreadsheet:
        return

    try:
        ws = spreadsheet.worksheet("Edit Proposals")
        ws.append_row([
            timestamp,
            author_email,
            check_id,
            field_path,
            original_text,
            proposed_text,
            "Pending",
            "",
            "",
        ])
        logger.info("Logged edit proposal to Google Sheet: %s::%s by %s", check_id, field_path, author_email)

    except Exception as e:
        logger.error("Failed to log edit proposal to Google Sheet: %s", e)
