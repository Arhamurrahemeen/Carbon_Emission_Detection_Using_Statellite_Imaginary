"""Extract page text from a company report PDF and list candidate claims for a person to confirm.

Run:    python scripts/extract_report_text.py data/raw/reports/<report>.pdf
Writes: data/raw/reports/<report>.pages.json   ([{"page": n, "text": "..."}])
Prints: candidate claims (type, value, page, sentence). Copy the confirmed ones into data/manual/claims.csv."""
import json
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify.claims import extract_claims  # noqa: E402


def main(pdf: str) -> None:
    path = Path(pdf)
    pages = [{"page": i + 1, "text": p.extract_text() or ""} for i, p in enumerate(PdfReader(path).pages)]
    out = path.with_suffix(".pages.json")
    out.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    empty = sum(not p["text"].strip() for p in pages)
    print(f"{len(pages)} pages ({empty} with no text, probably scanned) -> {out}")
    for c in extract_claims(pages, path.stem):
        print(f"p{c['source_page']:>4} {c['claim_type']:<14} {c['value']:>14,.1f}  {c['source_quote'][:110]}")


if __name__ == "__main__":
    main(sys.argv[1])
