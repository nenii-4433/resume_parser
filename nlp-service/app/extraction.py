"""extraction.py - pulls structured data out of resume text.

Runs AFTER validation. Uses regex for emails/phones/links, a spaCy
PhraseMatcher for skills, and simple rules (plus spaCy NER as a fallback)
for the name.
"""
import re
from dataclasses import dataclass, field
from functools import lru_cache

import spacy
from spacy.matcher import PhraseMatcher

from app.quality import SECTION_NAMES, find_sections

# canonical skill name -> extra spellings people use
SKILLS = {
    "JavaScript": ["js"], "TypeScript": ["ts"], "Python": [], "Java": [], "C++": [],
    "C#": [], "PHP": [], "Golang": [], "Ruby": [], "Kotlin": [], "Swift": [],
    "React": ["react.js", "reactjs"], "Next.js": ["nextjs"], "Redux": [],
    "Angular": [], "Vue": ["vue.js", "vuejs"], "HTML": ["html5"], "CSS": ["css3"],
    "Tailwind CSS": ["tailwind"], "Bootstrap": [], "Sass": [],
    "Node.js": ["nodejs", "node"], "Express": ["express.js", "expressjs"],
    "Django": [], "Flask": [], "FastAPI": [], "Spring Boot": [], "Laravel": [],
    "MongoDB": ["mongo"], "MySQL": [], "PostgreSQL": ["postgres"], "SQL": [],
    "SQLite": [], "Redis": [], "Firebase": [], "Mongoose": [],
    "REST API": ["rest apis", "restful api", "restful apis"],
    "GraphQL": [], "JWT": [], "WebSocket": ["websockets", "socket.io"],
    "Git": [], "GitHub": [], "Docker": [], "Kubernetes": [], "AWS": [],
    "Linux": [], "CI/CD": [], "Vercel": [], "Render": [], "Postman": [],
    "Figma": [], "Three.js": ["threejs"], "WordPress": [], "Shopify": [],
    "Machine Learning": ["ml"], "Deep Learning": [], "NLP": [], "spaCy": [],
    "NLTK": [], "TensorFlow": [], "PyTorch": [], "scikit-learn": ["sklearn"],
    "Pandas": [], "NumPy": [], "Hugging Face": ["huggingface"],
    "Generative AI": ["gen ai", "genai"], "Prompt Engineering": [],
    "Power BI": [], "Tableau": [], "Excel": [], "Jest": [], "Pytest": [],
    "Agile": [], "Scrum": [], "Jira": [],
}

# words that are also normal English: only count them when capitalized
AMBIGUOUS_SKILLS = {"Express", "Swift", "Ruby", "Excel", "Render"}

DEGREE_PATTERN = re.compile(
    r"\b(bachelor|bachelors|master|masters|b\.?sc|m\.?sc|bs|ms|bba|mba|bca|mca|"
    r"phd|ph\.d|b\.?tech|m\.?tech|diploma|associate degree|intermediate|fsc|f\.sc|"
    r"matric|a-levels?|o-levels?)\b",
    re.I,
)
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")


@dataclass
class ExtractedInfo:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    skills: list = field(default_factory=list)
    education: list = field(default_factory=list)


@lru_cache(maxsize=1)
def _matcher():
    nlp = spacy.blank("en")  # tokenizer only, no model needed for matching
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    for canonical, aliases in SKILLS.items():
        terms = [canonical.lower(), *aliases]
        matcher.add(canonical, [nlp.make_doc(t) for t in terms])
    return nlp, matcher


@lru_cache(maxsize=1)
def _ner():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return None


# ---------------- individual extractors ----------------
def extract_email(text: str) -> str | None:
    m = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    return m.group(0).lower() if m else None


def extract_phone(text: str) -> str | None:
    for m in re.finditer(r"\+?\d[\d\s().-]{8,}\d", text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13:
            return re.sub(r"\s+", " ", m.group(0)).strip()
    return None


def extract_links(text: str) -> tuple[str | None, str | None]:
    li = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?", text, re.I)
    gh = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", text, re.I)
    return (li.group(0) if li else None, gh.group(0) if gh else None)


def _looks_like_name(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 40 or re.search(r"[\d@:/|]", line):
        return False
    if re.fullmatch("|".join(SECTION_NAMES.values()), re.sub(r"[^A-Za-z ]", "", line).strip().lower()):
        return False
    words = line.split()
    return 2 <= len(words) <= 4 and all(re.fullmatch(r"[A-Za-z.'-]+", w) for w in words)


def extract_name(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()][:6]
    for line in lines:
        if _looks_like_name(line):
            return line.title() if line.isupper() else line
    nlp = _ner()  # fallback: spaCy NER on the top of the document
    if nlp is not None:
        doc = nlp(" ".join(lines)[:400])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()
    return None


def extract_skills(text: str) -> list[str]:
    nlp, matcher = _matcher()
    doc = nlp.make_doc(text)
    found = set()
    for mid, start, end in matcher(doc):
        name = nlp.vocab.strings[mid]
        if name in AMBIGUOUS_SKILLS and not doc[start:end].text[0].isupper():
            continue
        found.add(name)
    return sorted(found, key=str.lower)


def extract_education(text: str) -> list[dict]:
    section = find_sections(text).get("education", "")
    entries = []
    for line in section.splitlines():
        if DEGREE_PATTERN.search(line):
            entries.append({"text": line.strip(" -•*\t"), "years": YEAR_PATTERN.findall(line)})
    return entries


# ---------------- main entry ----------------
def extract_info(text: str) -> ExtractedInfo:
    linkedin, github = extract_links(text)
    return ExtractedInfo(
        name=extract_name(text),
        email=extract_email(text),
        phone=extract_phone(text),
        linkedin=linkedin,
        github=github,
        skills=extract_skills(text),
        education=extract_education(text),
    )