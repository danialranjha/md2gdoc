#!/usr/bin/env python3
"""
Markdown to Google Docs Converter

This script converts a markdown file to a Google Doc with proper formatting.
"""

import re
import sys
import argparse
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents"]

def authenticate_docs_service():
    """Authenticate and build the Google Docs service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if Path("token.json").exists():
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("docs", "v1", credentials=creds)

def build_requests_and_text(md_content):
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
        elif re.match(r"^-", line):
            # Bullet point. Count leading spaces to determine indent (assume 2 spaces per level).
            match = re.match(r"^(\s*)-\s*(.*)", line)
            if match:
                spaces = match.group(1)
                indent_level = len(spaces) // 2  # Each 2 spaces equals one indent level.
                new_line = "• " + match.group(2).strip() + "\n"
            else:
                new_line = line + "\n"
        elif re.match(r"^\d+\.", line):
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

def create_google_doc(service, title, md_content):
    """Create a Google Doc from markdown content."""
    try:
        # Create a new Google Doc.
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]

        # Build full text and formatting requests from markdown.
        full_text, requests = build_requests_and_text(md_content)

        # First, insert the complete text.
        insert_request = {
            "requests": [
                {"insertText": {"location": {"index": 1}, "text": full_text}}
            ]
        }
        service.documents().batchUpdate(documentId=doc_id, body=insert_request).execute()

        # Then, apply formatting requests.
        if requests:
            service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

        return f"https://docs.google.com/document/d/{doc_id}"
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Convert markdown file to Google Doc")
    parser.add_argument("markdown_file", help="Path to the markdown file")
    parser.add_argument("-t", "--title", help="Title for the Google Doc (defaults to filename)")
    
    args = parser.parse_args()
    
    # Check if file exists
    md_file = Path(args.markdown_file)
    if not md_file.exists():
        print(f"Error: File '{args.markdown_file}' not found.")
        sys.exit(1)
    
    # Determine title
    title = args.title if args.title else md_file.stem
    
    # Read markdown content
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Authenticate and create document
    try:
        service = authenticate_docs_service()
        doc_link = create_google_doc(service, title, md_content)
        
        if doc_link:
            print(f"Google Doc created successfully: {doc_link}")
        else:
            print("Failed to create document.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()