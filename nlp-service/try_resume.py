import sys

from app.extraction import extract_info
from app.quality import score_quality
from app.validation import validate_resume

path = sys.argv[1]
filename = path.replace("\\", "/").split("/")[-1]

with open(path, "rb") as f:
    data = f.read()

v = validate_resume(filename, data)
print("Validation:", v.status, v.reasons)

if v.status == "ok":
    print("\nExtracted:", extract_info(v.text))
    q = score_quality(v.text)
    print(f"\nQuality: {q.score}/100 ({q.label})")
    for tip in q.tips:
        print(" -", tip)