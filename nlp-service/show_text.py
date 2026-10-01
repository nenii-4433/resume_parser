import sys

from app.quality import find_sections
from app.validation import validate_resume

path = sys.argv[1]
with open(path, "rb") as f:
    v = validate_resume(path.replace("\\", "/").split("/")[-1], f.read())
print("status:", v.status, v.reasons)
print("sections found:", list(find_sections(v.text)))
print("words:", len(v.text.split()))
print("-----")
print(v.text[:1500])