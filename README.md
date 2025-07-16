# Markdown to Google Docs Converter

Convert markdown files to Google Docs with proper formatting including headings, lists, checkboxes, and more.

## Installation

### Option 1: Install with pipx (Recommended)
```bash
# Install pipx if you don't have it
brew install pipx  # macOS
# or: pip install pipx

# Install md2gdoc globally
pipx install md2gdoc

# Now you can use it anywhere
md2gdoc example.md
```

### Option 2: Install from source
```bash
git clone <repository-url>
cd md2gdoc
pipx install .
```

## Google API Setup

Before using md2gdoc, you need to set up Google API credentials:

1. **Go to the [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project or select an existing one**
3. **Enable the Google Docs API**
4. **Create credentials (OAuth 2.0 Client ID) for a desktop application**
5. **Download the credentials file**

### Credentials Location

The `credentials.json` file needs to be in a location where md2gdoc can find it:

**Option A: Home directory (Recommended)**
```bash
# Save credentials in your home directory
mkdir -p ~/.config/md2gdoc
# Move your downloaded credentials.json file to:
mv ~/Downloads/credentials.json ~/.config/md2gdoc/credentials.json
```

**Option B: Current working directory**
```bash
# md2gdoc will also look for credentials.json in the current directory
# This is less convenient but works for testing
```

## Usage

```bash
md2gdoc <markdown_file> [-t TITLE]
```

### Examples

```bash
# Convert with default title (filename)
md2gdoc example.md

# Convert with custom title
md2gdoc example.md -t "My Custom Document Title"

# Works from any directory
cd ~/Documents
md2gdoc meeting-notes.md
```

## First Run Authentication

On first run, md2gdoc will:
1. Look for `credentials.json` in `~/.config/md2gdoc/` or current directory
2. Open your browser for Google authentication
3. Create a `token.json` file to store your credentials for future use
4. Token will be saved in `~/.config/md2gdoc/token.json`

## Supported Markdown Features

- **Headings** (H1-H6): `# ## ### #### ##### ######`
- **Bullet lists**: `- item`
- **Numbered lists**: `1. item`
- **Checkboxes**: `- [ ]` and `- [x]`
- **Nested lists** (indented with spaces)
- **@mentions** (automatically bolded)
- **Footer styling** for lines starting with "Meeting recorded by:" or "Duration:"

## Development

If you want to contribute or modify the code:

```bash
# Clone the repository
git clone <repository-url>
cd md2gdoc

# Set up development environment
python3 -m venv .venv
source .venv/bin/activate
pip install uv
uv sync

# Run tests
make test

# Format code
make format

# Install in development mode
pipx install -e .
```

## Troubleshooting

### Credentials Not Found
If you get a credentials error:
1. Ensure `credentials.json` is in `~/.config/md2gdoc/` or current directory
2. Check that the file has the correct OAuth 2.0 client ID format
3. Verify you created a "Desktop Application" credential type

### Permission Denied
If you get permission errors:
1. Make sure the credentials file is readable
2. Check that `~/.config/md2gdoc/` directory exists and is writable

### Authentication Issues
If authentication fails:
1. Delete the `token.json` file to force re-authentication
2. Make sure you're using the correct Google account
3. Check that the Google Docs API is enabled in your project

## Files and Directories

- `~/.config/md2gdoc/credentials.json` - Google API credentials (you create this)
- `~/.config/md2gdoc/token.json` - Generated after first authentication
- Current directory fallback for both files also supported