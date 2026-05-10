from __future__ import annotations

import argparse
import sys

from clipocr_core import ClipOCRError, load_config, recognize_clipboard_image


def run(print_result: bool) -> int:
    markdown = recognize_clipboard_image(load_config())

    if print_result:
        print(markdown)
    else:
        print(f"OK: Markdown copied to clipboard ({len(markdown)} characters)")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OCR the clipboard image and copy clean Markdown back to clipboard.")
    parser.add_argument("--print", action="store_true", help="Also print the Markdown result to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return run(print_result=args.print)
    except ClipOCRError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
