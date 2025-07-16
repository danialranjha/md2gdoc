# Markdown to Google Docs Converter

Convert markdown files to Google Docs with proper formatting including headings, lists, checkboxes, and more.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google API credentials:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Docs API
   - Create credentials (OAuth 2.0 Client ID) for a desktop application
   - Download the credentials file and save it as `credentials.json` in this directory

## Usage

```bash
python md2gdoc.py <markdown_file> [-t TITLE]
```

### Examples

```bash
# Convert with default title (filename)
python md2gdoc.py example.md

# Convert with custom title
python md2gdoc.py example.md -t "My Custom Document Title"
```

## Supported Markdown Features

- **Headings** (H1-H6): `# ## ### #### ##### ######`
- **Bullet lists**: `- item`
- **Numbered lists**: `1. item`
- **Checkboxes**: `- [ ]` and `- [x]`
- **Nested lists** (indented with spaces)
- **@mentions** (automatically bolded)
- **Footer styling** for lines starting with "Meeting recorded by:" or "Duration:"

## First Run

On first run, the script will:
1. Open your browser for Google authentication
2. Create a `token.json` file to store your credentials for future use

## Files

- `md2gdoc.py` - Main script
- `requirements.txt` - Python dependencies
- `credentials.json` - Google API credentials (you need to create this)
- `token.json` - Generated after first authentication