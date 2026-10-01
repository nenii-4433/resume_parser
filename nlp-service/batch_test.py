"""batch_test.py - run validation, extraction and quality on every resume in a folder.

Usage (from nlp-service, venv active):
    python batch_test.py ..\\samples\\good results_good.csv
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from app.extraction import extract_info
from app.quality import score_quality
from app.validation import validate_resume

LEVELS = ("Fresher", "Intermediate", "Professional")


def level_from_name(name: str) -> str:
    for level in LEVELS:
        if level.lower() in name.lower():
            return level
    return ""


def run_one(path: Path, folder: Path) -> dict:
    row = {
        "file": str(path.relative_to(folder)),
        "level": level_from_name(path.name),
        "status": "", "reasons": "", "name": "", "email": "", "phone": "",
        "skills_found": 0, "education_found": 0, "quality": "", "label": "",
    }
    try:
        v = validate_resume(path.name, path.read_bytes())
    except Exception as e:  # never let one bad file stop the batch
        row["status"], row["reasons"] = "error", str(e)
        return row
    row["status"], row["reasons"] = v.status, "; ".join(v.reasons)
    if v.status == "ok":
        info = extract_info(v.text)
        q = score_quality(v.text)
        row.update(
            name=info.name or "", email=info.email or "", phone=info.phone or "",
            skills_found=len(info.skills), education_found=len(info.education),
            quality=q.score, label=q.label,
        )
    return row


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python batch_test.py <folder> [output.csv]")
    folder = Path(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "results.csv"
    files = sorted(p for p in folder.rglob("*") if p.suffix.lower() in (".pdf", ".docx"))
    if not files:
        sys.exit(f"No PDF or DOCX files found in {folder}")

    rows = []
    for i, p in enumerate(files, 1):
        rows.append(run_one(p, folder))
        if i % 25 == 0:
            print(f"  processed {i}/{len(files)}")

    with open(out, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig opens cleanly in Excel
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # ---- summary ----
    print(f"\nFiles: {len(rows)}   CSV: {out}")
    print("Status:", dict(Counter(r["status"] for r in rows)))
    reasons = Counter()
    for r in rows:
        if r["status"] in ("rejected", "needs_review") and r["reasons"]:
            reasons[r["reasons"].split(":")[0].split("(")[0].strip()] += 1
    if reasons:
        print("Top rejection reasons:", dict(reasons.most_common(6)))

    ok = [r for r in rows if r["status"] == "ok"]
    if ok:
        print(f"\nParsed OK: {len(ok)}")
        print("  name found :", sum(1 for r in ok if r["name"]), f"/ {len(ok)}")
        print("  email found:", sum(1 for r in ok if r["email"]), f"/ {len(ok)}")
        print("  phone found:", sum(1 for r in ok if r["phone"]), f"/ {len(ok)}")
        print("  3+ skills  :", sum(1 for r in ok if r["skills_found"] >= 3), f"/ {len(ok)}")
        print("  education  :", sum(1 for r in ok if r["education_found"] >= 1), f"/ {len(ok)}")
        by_level = defaultdict(list)
        for r in ok:
            by_level[r["level"] or "unlabeled"].append(r["quality"])
        print("  average quality score by level:")
        for level, scores in sorted(by_level.items()):
            print(f"    {level:<13} {sum(scores) / len(scores):5.1f}  ({len(scores)} files)")


if __name__ == "__main__":
    main()