import re
from pathlib import Path
from typing import List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents"]


def get_credentials_paths():
    """Get the paths for credentials and token files."""
    from pathlib import Path
    
    # Try ~/.config/md2gdoc/ first (recommended)
    config_dir = Path.home() / ".config" / "md2gdoc"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_creds = config_dir / "credentials.json"
    config_token = config_dir / "token.json"
    
    # Fallback to current directory
    current_creds = Path("credentials.json")
    current_token = Path("token.json")
    
    # Determine which credentials file to use
    if config_creds.exists():
        creds_path = config_creds
        token_path = config_token
    elif current_creds.exists():
        creds_path = current_creds
        token_path = current_token
    else:
        # Default to config directory for new files
        creds_path = config_creds
        token_path = config_token
    
    return creds_path, token_path


def authenticate_docs_service():
    """Authenticate and build the Google Docs service."""
    creds_path, token_path = get_credentials_paths()
    
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Google API credentials not found. Please save credentials.json to:\n"
                    f"  {creds_path}\n"
                    f"Or current directory: credentials.json\n\n"
                    f"Get credentials from: https://console.cloud.google.com/"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        
        logger.info(f"Authentication token saved to: {token_path}")

    return build("docs", "v1", credentials=creds)


def build_requests_and_text(md_content: str) -> Tuple[str, List[dict]]:
    """
    Parse markdown content and build a combined text string plus formatting requests.
    Returns the full text to insert and a list of formatting requests.
    """
    full_text = ""
    requests = []
    current_index = 1  # The doc always starts at index 1

    # Split content into lines.
    lines = md_content.splitlines()

    # Process each line.
    # We'll record checklist ranges in a list so we can later apply checklist formatting.
    checklist_ranges = []  # list of (start_idx, end_idx) for checklist items

    for line in lines:
        is_checkbox = False  # Initialize for each line
        original_line = line  # Keep for footer detection.
        line = line.rstrip("\n")
        style = None
        indent_level = 0

        # Determine what the line represents.
        if not line.strip():
            new_line = "\n"
        elif line.startswith("# "):
            new_line = line[2:].strip() + "\n"
            style = "HEADING_1"
        elif line.startswith("## "):
            new_line = line[3:].strip() + "\n"
            style = "HEADING_2"
        elif line.startswith("### "):
            new_line = line[4:].strip() + "\n"
            style = "HEADING_3"
        elif line.startswith("#### "):
            new_line = line[5:].strip() + "\n"
            style = "HEADING_4"
        elif line.startswith("##### "):
            new_line = line[6:].strip() + "\n"
            style = "HEADING_5"
        elif line.startswith("###### "):
            new_line = line[7:].strip() + "\n"
            style = "HEADING_6"
        elif re.match(r"^- \[ \]", line):
            # Markdown checkbox: Remove the '- [ ]' marker and flag as checklist item.
            new_line = line[6:].strip() + "\n"
            is_checkbox = True
        elif re.match(r"^- \[x\]", line):
            # Checked markdown checkbox: Remove the '- [x]' marker and flag as checklist item.
            new_line = line[6:].strip() + "\n"
            is_checkbox = True
        elif re.match(r"^\s*-", line):
            # Bullet point. Count leading spaces to determine indent (assume 2 spaces per level).
            match = re.match(r"^(\s*)-\s*(.*)", line)
            if match:
                spaces = match.group(1)
                indent_level = len(spaces) // 2  # Each 2 spaces equals one indent level.
                new_line = "• " + match.group(2).strip() + "\n"
            else:
                new_line = line + "\n"
        elif re.match(r"^\s*\d+\.", line):
            # Numbered list
            match = re.match(r"^(\s*)\d+\.\s*(.*)", line)
            if match:
                spaces = match.group(1)
                indent_level = len(spaces) // 2
                new_line = match.group(2).strip() + "\n"
            else:
                new_line = line + "\n"
        else:
            new_line = line + "\n"

        # Record where this line starts.
        start_idx = current_index
        full_text += new_line
        current_index += len(new_line)
        end_idx = current_index

        # If this line was a checkbox, record its range for later checklist formatting.
        if is_checkbox:
            checklist_ranges.append((start_idx, end_idx))

        # If we have a heading style, add a paragraph style update.
        if style:
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start_idx, "endIndex": end_idx},
                    "paragraphStyle": {"namedStyleType": style},
                    "fields": "namedStyleType"
                }
            })

        # If this is a bullet point with indent, update indentation.
        if indent_level > 0:
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start_idx, "endIndex": end_idx},
                    "paragraphStyle": {"indentStart": {"magnitude": 36 * indent_level, "unit": "PT"}},
                    "fields": "indentStart"
                }
            })

        # Bold any assignee mentions (e.g., @sarah) within the line.
        for m in re.finditer(r"@\w+", new_line):
            m_start = start_idx + m.start()
            m_end = start_idx + m.end()
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": m_start, "endIndex": m_end},
                    "textStyle": {"bold": True},
                    "fields": "bold"
                }
            })

        # Style footer information (e.g., "Meeting recorded by:" or "Duration:")
        if re.search(r"^(Meeting recorded by:|Duration:)", original_line.strip()):
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start_idx, "endIndex": end_idx},
                    "textStyle": {
                        "italic": True,
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.5, "green": 0.5, "blue": 0.5}}}
                    },
                    "fields": "italic,foregroundColor"
                }
            })

    # For each recorded checklist range, add a request to convert that paragraph into a checklist.
    for start_idx, end_idx in checklist_ranges:
        requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start_idx, "endIndex": end_idx},
                "bulletPreset": "BULLET_CHECKBOX"
            }
        })

    return full_text, requests


def create_google_doc(service, title: str, md_content: str) -> str | None:
    """Create a Google Doc from markdown content."""
    try:
        # Create a new Google Doc.
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        logger.info(f"Created Google Doc with ID: {doc_id}")

        # Build full text and formatting requests from markdown.
        full_text, requests = build_requests_and_text(md_content)

        # First, insert the complete text.
        insert_request = {
            "requests": [
                {"insertText": {"location": {"index": 1}, "text": full_text}}
            ]
        }
        service.documents().batchUpdate(documentId=doc_id, body=insert_request).execute()
        logger.info("Inserted text into document")

        # Then, apply formatting requests.
        if requests:
            service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
            logger.info(f"Applied {len(requests)} formatting requests")

        return f"https://docs.google.com/document/d/{doc_id}"
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        return None


def convert_markdown_to_gdoc(markdown_file: str, title: str | None = None) -> str | None:
    """Convert a markdown file to a Google Doc."""
    # Check if file exists
    md_file = Path(markdown_file)
    if not md_file.exists():
        logger.error(f"File '{markdown_file}' not found.")
        return None
    
    # Determine title
    doc_title = title if title else md_file.stem
    
    # Read markdown content
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return None
    
    # Authenticate and create document
    try:
        service = authenticate_docs_service()
        doc_link = create_google_doc(service, doc_title, md_content)
        
        if doc_link:
            logger.success(f"Google Doc created successfully: {doc_link}")
            return doc_link
        else:
            logger.error("Failed to create document.")
            return None
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
