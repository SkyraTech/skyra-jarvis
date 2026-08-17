"""
Jarvis Google Workspace Tools — Phase 5
=========================================
Exposes Google Workspace integration capabilities to Gemini.
Calls the skyra-google-service (port 8002).

Available tools:
  - list_unread_emails    → Read unread messages from Gmail inbox
  - send_gmail_email      → Send an email using your Gmail account
  - list_calendar_events  → Retrieve upcoming events from primary calendar
  - create_calendar_event → Insert a new meeting/reminder to calendar
  - read_google_sheet     → Extract row values from a spreadsheet
  - update_google_sheet   → Write cell values in a spreadsheet
  - append_google_sheet   → Append rows of data to a spreadsheet
  - search_google_drive   → Search files inside Google Drive
"""

from loguru import logger
from utils.network import call_local_api
from config import config

GOOGLE_SERVICE_URL = config.GOOGLE_SERVICE_URL


async def list_unread_emails() -> str:
    """
    Check your Gmail inbox and return summaries of the top unread emails.
    Use this to see what emails require attention.
    """
    logger.info("📧 Tool Call: Checking unread emails...")
    success, data, err = await call_local_api("GET", f"{GOOGLE_SERVICE_URL}/gmail/unread", {})

    if success:
        emails = data.get("emails", [])
        if not emails:
            return "You have no unread emails."
        
        lines = [f"Unread emails ({len(emails)}):"]
        for msg in emails:
            lines.append(f"  • From: {msg.get('from')}")
            lines.append(f"    Subject: {msg.get('subject')}")
            lines.append(f"    Date: {msg.get('date')}")
            lines.append("")
        return "\n".join(lines)
    return f"Failed to check emails: {err}"


async def send_gmail_email(to: str, subject: str, body: str) -> str:
    """
    Send an email message using your Google/Gmail account.
    Use this to notify stakeholders, send reports, or email clients.

    Args:
        to: The recipient's email address (e.g. 'client@example.com')
        subject: The email subject line
        body: The plain text or HTML body content of the email
    """
    logger.info(f"📧 Tool Call: Sending email to {to}...")
    payload = {"to": to, "subject": subject, "body": body}
    success, data, err = await call_local_api("POST", f"{GOOGLE_SERVICE_URL}/gmail/send", payload)

    if success:
        if data.get("mock"):
            return f"Dry-run: Email to {to} drafted successfully (mock mode)."
        return f"Success! Email sent to {to}. Message ID: {data.get('messageId')}"
    return f"Failed to send email: {err}"


async def list_calendar_events(limit: int = 10) -> str:
    """
    Retrieve upcoming events from your Google Calendar.
    Use this to review your schedule or check meeting times.

    Args:
        limit: Maximum number of events to return (default: 10)
    """
    logger.info("📅 Tool Call: Fetching calendar events...")
    success, data, err = await call_local_api("GET", f"{GOOGLE_SERVICE_URL}/calendar/events?limit={limit}", {})

    if success:
        events = data.get("events", [])
        if not events:
            return "No upcoming events scheduled on your calendar."
        
        lines = ["Upcoming calendar events:"]
        for ev in events:
            start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", ""))
            lines.append(f"  • Event: {ev.get('summary')}")
            lines.append(f"    Time: {start}")
            if ev.get("description"):
                lines.append(f"    Details: {ev.get('description')}")
            lines.append("")
        return "\n".join(lines)
    return f"Failed to retrieve calendar: {err}"


async def create_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> str:
    """
    Add a new event or meeting to your Google Calendar.

    Args:
        summary: Title of the event (e.g. 'Project Review w/ Umesh')
        start_time: ISO-8601 start datetime string (e.g. '2026-08-16T15:00:00+05:30')
        end_time: ISO-8601 end datetime string (e.g. '2026-08-16T16:00:00+05:30')
        description: Agenda or description text (optional)
    """
    logger.info(f"📅 Tool Call: Scheduling event '{summary}'...")
    payload = {
        "summary": summary,
        "startTime": start_time,
        "endTime": end_time,
        "description": description
    }
    success, data, err = await call_local_api("POST", f"{GOOGLE_SERVICE_URL}/calendar/events/create", payload)

    if success:
        if data.get("mock"):
            return f"Dry-run: Calendar event '{summary}' scheduled successfully (mock mode)."
        return f"Success! Event '{summary}' scheduled. Calendar link: {data.get('link')}"
    return f"Failed to create event: {err}"


async def read_google_sheet(spreadsheet_id: str, range_name: str) -> str:
    """
    Extract row and cell values from a Google Sheet.
    Use this to read expenses, content calendars, or billing sheets.

    Args:
        spreadsheet_id: The ID of the spreadsheet (found in Google Sheets URL)
        range_name: The sheet tab and cell range (e.g. 'Sheet1!A1:C10')
    """
    logger.info(f"📊 Tool Call: Reading sheet '{spreadsheet_id}' range '{range_name}'...")
    payload = {"spreadsheetId": spreadsheet_id, "range": range_name}
    success, data, err = await call_local_api("POST", f"{GOOGLE_SERVICE_URL}/sheets/read", payload)

    if success:
        values = data.get("values", [])
        if not values:
            return f"No values found in sheet range '{range_name}'."
        
        lines = [f"Values read from range '{range_name}':"]
        for row in values:
            lines.append("  |  ".join([str(val) for val in row]))
        return "\n".join(lines)
    return f"Failed to read sheet: {err}"


async def update_google_sheet(spreadsheet_id: str, range_name: str, values: list[list[str]]) -> str:
    """
    Update cell values in a Google Sheet range.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        range_name: Sheet tab and cell range to update (e.g. 'Sheet1!A1:B2')
        values: 2D array of strings representing rows and columns of data
    """
    logger.info(f"📊 Tool Call: Updating sheet '{spreadsheet_id}' range '{range_name}'...")
    payload = {"spreadsheetId": spreadsheet_id, "range": range_name, "values": values}
    success, data, err = await call_local_api("POST", f"{GOOGLE_SERVICE_URL}/sheets/update", payload)

    if success:
        return f"Success! Updated sheet cells: {data.get('updatedCells')}"
    return f"Failed to update sheet: {err}"


async def append_google_sheet(spreadsheet_id: str, range_name: str, values: list[list[str]]) -> str:
    """
    Append rows of data to the bottom of a Google Sheet.
    Use this to add a new transaction, subscriber row, or expense log.

    Args:
        spreadsheet_id: The ID of the spreadsheet
        range_name: Sheet tab name and starting column range (e.g. 'Sheet1!A:C')
        values: 2D array of strings representing rows of data to append
    """
    logger.info(f"📊 Tool Call: Appending row to sheet '{spreadsheet_id}'...")
    payload = {"spreadsheetId": spreadsheet_id, "range": range_name, "values": values}
    success, data, err = await call_local_api("POST", f"{GOOGLE_SERVICE_URL}/sheets/append", payload)

    if success:
        return f"Success! Row appended to spreadsheet range: {data.get('updatedRange')}"
    return f"Failed to append to sheet: {err}"


async def search_google_drive(query: str) -> str:
    """
    Search for files inside your Google Drive by name.
    Use this to find product requirements documents, PDF templates, or project files.

    Args:
        query: Part of the filename to search for (e.g. 'PRD')
    """
    logger.info(f"🗂️ Tool Call: Searching Drive for '{query}'...")
    success, data, err = await call_local_api("GET", f"{GOOGLE_SERVICE_URL}/drive/search?q={query}", {})

    if success:
        files = data.get("files", [])
        if not files:
            return f"No files found matching '{query}' in Google Drive."
        
        lines = [f"Search results for files matching '{query}':"]
        for f in files:
            lines.append(f"  • {f.get('name')}")
            lines.append(f"    Type: {f.get('mimeType')}")
            lines.append(f"    Link: {f.get('webViewLink')}")
            lines.append("")
        return "\n".join(lines)
    return f"Drive search failed: {err}"
