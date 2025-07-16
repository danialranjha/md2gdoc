import argparse
import sys

from loguru import logger

from .converter import convert_markdown_to_gdoc


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Convert markdown file to Google Doc")
    parser.add_argument("markdown_file", help="Path to the markdown file")
    parser.add_argument("-t", "--title", help="Title for the Google Doc (defaults to filename)")

    args = parser.parse_args()

    # Convert markdown to Google Doc
    doc_link = convert_markdown_to_gdoc(args.markdown_file, args.title)

    if doc_link:
        print(f"Google Doc created successfully: {doc_link}")
    else:
        logger.error("Failed to create document.")
        sys.exit(1)


if __name__ == "__main__":
    main()
