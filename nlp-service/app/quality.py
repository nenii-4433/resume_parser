"""quality.py - scores how well a resume is written (0-100) and gives tips.

Runs AFTER validation. A weak resume is NOT rejected: it is parsed, scored
and flagged, with feedback the candidate can use to improve it.
"""
import re
from dataclasses import dataclass, field

try:  # optional: pip install pyspellchecker
    from spellchecker import SpellChecker
except ImportError:  # spelling check is skipped if not installed
    SpellChecker = None

try:  # optional: pip install scikit-learn
    from sklearn.ensemble import RandomForestRegressor
except ImportError:  # the project still works without it, but model metadata is missing
    RandomForestRegressor = None

# ---- weights (sum = 100) ----
W_CONTACT, W_SKILLS, W_EDU, W_EXP, W_STYLE, W_SPELL, W_LENGTH = 15, 15, 15, 20, 15, 10, 10

STRONG_MIN, AVERAGE_MIN = 80, 50

SECTION_NAMES = {
    "summary": r"summary|profile|objective|about me|career objective",
    "skills": r"skills|technical skills|key skills|core skills|technologies",
    "education": r"education|academic background|qualifications?|academics",
    "experience": r"experience|work experience|work history|employment|internships?",
    "projects": r"projects?|personal projects|academic projects",
}

ACTION_VERBS = {
    "built", "developed", "designed", "created", "implemented", "managed", "led",
    "improved", "reduced", "increased", "launched", "deployed", "integrated",
    "automated", "optimized", "maintained", "delivered", "analyzed", "tested",
    "collaborated", "organized", "trained", "wrote", "configured", "migrated",
}

VAGUE_PHRASES = [
    "hard working", "hardworking", "team player", "responsible for",
    "good communication skills", "quick learner", "detail oriented",
]

UNPROFESSIONAL_EMAIL = re.compile(
    r"(cool|boy|girl|sexy|king|queen|baby|hot|lover|dude|killer|gamer)|\d{4,}", re.I
)

TECH_WORDS = {  # lowercase tech terms the spell checker would wrongly flag
    "javascript", "mongodb", "nodejs", "reactjs", "expressjs", "api", "apis", "json",
    "html", "css", "git", "github", "sql", "mysql", "nosql", "python", "docker",
    "frontend", "backend", "fullstack", "webapp", "cms", "ui", "ux", "devops",
    "aws", "firebase", "postman", "redux", "typescript", "nextjs", "vercel",
    "linux", "bootstrap", "tailwind", "pytest", "spacy", "nltk", "ai", "ml", "nlp",
}


@dataclass
class QualityResult:
    score: int = 0
    label: str = "Weak"
    breakdown: dict = field(default_factory=dict)
    tips: list = field(default_factory=list)
    feature_vector: dict = field(default_factory=dict)
    model_used: str = "heuristic"


def find_sections(text: str) -> dict:
    """Return {section: text_under_it} using short header-like lines."""
    lines = text.splitlines()
    headers = []  # (line_index, canonical name)
    for i, line in enumerate(lines):
        cleaned = re.sub(r"[^A-Za-z ]", "", line).strip().lower()
        if not cleaned or len(line.strip()) > 40:
            continue
        for name, pat in SECTION_NAMES.items():
            if re.fullmatch(pat, cleaned):
                headers.append((i, name))
                break
    sections = {}
    for n, (i, name) in enumerate(headers):
        end = headers[n + 1][0] if n + 1 < len(headers) else len(lines)
        sections[name] = "\n".join(lines[i + 1:end])
    return sections


def count_skill_items(skills_text: str) -> int:
    parts = re.split(r"[,\n|•;]|\s-\s|^-|\s*:\s*", skills_text)
    return len([p for p in (x.strip(" -*•\t") for x in parts) if 1 < len(p) < 40])


def count_bullets(text: str) -> int:
    return len(re.findall(r"^\s*[•\-\*–▪●]\s+\S", text, re.M))


def count_action_verbs(text: str) -> int:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return len(words & ACTION_VERBS)


def misspelled_words(text: str, skip_text: str = "") -> list[str]:
    if SpellChecker is None:
        return []
    spell = SpellChecker()
    skip = set(re.findall(r"[a-z]+", skip_text.lower()))
    # only plain lowercase words: names and tech terms are usually capitalized
    candidates = [
        w for w in re.findall(r"\b[a-z]{4,}\b", text)
        if w not in TECH_WORDS and w not in skip
    ]
    return sorted(spell.unknown(candidates))


QUALITY_FEATURE_NAMES = [
    "contact_score", "skills_score", "education_score", "experience_score",
    "style_score", "spelling_score", "length_score", "words_count",
    "bullet_count", "action_verbs_count", "vague_phrase_count",
    "email_present", "phone_present", "skills_section_present",
    "education_section_present", "project_section_present",
]

QUALITY_FEATURE_TIPS = {
    "contact_score": "Add a professional email and phone number in the header.",
    "skills_score": "Add a clearer skills section with relevant tools and technologies.",
    "education_score": "Add dates and education details to strengthen credibility.",
    "experience_score": "Include a stronger experience or project section with real impact.",
    "style_score": "Use more bullet points and action verbs to improve readability.",
    "spelling_score": "Review grammar and spelling to make the resume look polished.",
    "length_score": "Keep the resume to a concise 1-2 page length with focused content.",
    "bullet_count": "Add more concise bullets to describe work clearly.",
    "action_verbs_count": "Start bullets with stronger action verbs like built, designed, and improved.",
    "vague_phrase_count": "Replace vague phrases with measurable achievements and examples.",
    "email_present": "Add a professional email address on the top line.",
    "phone_present": "Include a working contact number near the header.",
    "skills_section_present": "Create a dedicated skills section with technical tools and domains.",
    "education_section_present": "Add education details and dates for completeness.",
    "project_section_present": "Include a projects section to show practical work and outcomes.",
}


def _quality_model():
    if RandomForestRegressor is None:
        return None

    samples = [
        [15, 15, 15, 20, 15, 10, 10, 200, 6, 8, 0, 1, 1, 1, 1, 1, 88],
        [14, 12, 14, 18, 12, 8, 8, 170, 5, 6, 1, 1, 1, 1, 1, 0, 76],
        [10, 8, 10, 12, 8, 7, 5, 120, 3, 4, 2, 1, 1, 1, 1, 0, 58],
        [5, 4, 6, 6, 4, 3, 2, 90, 1, 2, 3, 0, 0, 0, 0, 0, 30],
        [2, 2, 3, 2, 2, 1, 2, 60, 0, 1, 4, 0, 0, 0, 0, 0, 15],
    ]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    X = [[row[i] for i in range(len(QUALITY_FEATURE_NAMES))] for row in [sample[:-1] for sample in samples]]
    y = [sample[-1] for sample in samples]
    model.fit(X, y)
    return model


def _feature_vector_from_breakdown(breakdown: dict, *, words: int, bullets: int, verbs: int, vague_count: int, email: bool, phone: bool, has_skills: bool, has_edu: bool, has_proj: bool) -> dict:
    return {
        "contact_score": float(breakdown.get("contact", 0)),
        "skills_score": float(breakdown.get("skills", 0)),
        "education_score": float(breakdown.get("education", 0)),
        "experience_score": float(breakdown.get("experience", 0)),
        "style_score": float(breakdown.get("style", 0)),
        "spelling_score": float(breakdown.get("spelling", 0)),
        "length_score": float(breakdown.get("length", 0)),
        "words_count": float(words),
        "bullet_count": float(bullets),
        "action_verbs_count": float(verbs),
        "vague_phrase_count": float(vague_count),
        "email_present": float(int(email)),
        "phone_present": float(int(phone)),
        "skills_section_present": float(int(has_skills)),
        "education_section_present": float(int(has_edu)),
        "project_section_present": float(int(has_proj)),
    }


def score_quality(text: str) -> QualityResult:
    res = QualityResult()
    tips = res.tips
    sections = find_sections(text)
    words = len(text.split())

    # 1. contact (15)
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(\+?\d[\d\s().-]{8,}\d)", text)
    contact = 0
    if email:
        contact += 8
        local = email.group(0).split("@")[0]
        if UNPROFESSIONAL_EMAIL.search(local):
            contact -= 3
            tips.append("Use a professional email address, ideally based on your name.")
    else:
        tips.append("No email address found. Add one in the header.")
    if phone:
        contact += 7
    else:
        tips.append("No phone number found. Add one in the header.")
    res.breakdown["contact"] = max(contact, 0)

    # 2. skills (15)
    skills = 0
    if "skills" in sections:
        skills += 7
        items = count_skill_items(sections["skills"])
        if items >= 5:
            skills += 8
        elif items >= 3:
            skills += 4
            tips.append("List more skills (at least 5 relevant ones).")
        else:
            tips.append("Your skills section is nearly empty. List your tools and technologies.")
    else:
        tips.append("No skills section found. Add a Skills section with your tools and technologies.")
    res.breakdown["skills"] = skills

    # 3. education (15)
    edu = 0
    if "education" in sections:
        edu += 8
        if re.search(r"\b(19|20)\d{2}\b", sections["education"]):
            edu += 7
        else:
            tips.append("Add dates (years) to your education.")
    else:
        tips.append("No education section found.")
    res.breakdown["education"] = edu

    # 4. experience / projects (20)
    has_exp, has_proj = "experience" in sections, "projects" in sections
    exp = 20 if (has_exp and has_proj) else 14 if (has_exp or has_proj) else 0
    if not has_exp and not has_proj:
        tips.append("No experience or projects found. Add 2 to 3 projects with what you built and the tools used.")
    elif not has_proj:
        tips.append("Consider adding a Projects section to show practical work.")
    res.breakdown["experience"] = exp

    # 5. style: bullets + action verbs (15)
    style = 0
    bullets = count_bullets(text)
    verbs = count_action_verbs(text)
    if bullets >= 4:
        style += 7
    else:
        tips.append("Use bullet points to describe your work instead of long paragraphs.")
    if verbs >= 4:
        style += 8
    elif verbs >= 2:
        style += 4
        tips.append("Start more bullet points with action verbs (built, developed, improved).")
    else:
        tips.append("Use action verbs such as built, developed, designed and improved.")
    res.breakdown["style"] = style

    vague = [p for p in VAGUE_PHRASES if p in text.lower()]
    if vague:
        tips.append("Replace vague phrases (" + ", ".join(vague[:3]) + ") with specific examples.")
    if not re.search(r"\d+\s*%|\b\d{2,}\+?\s*(users|clients|projects|customers|requests)", text, re.I):
        tips.append("Add measurable results where possible (for example: reduced load time by 30%).")

    # 6. spelling (10)
    wrong = misspelled_words(text, sections.get("skills", ""))
    if len(wrong) == 0:
        spell = 10
    elif len(wrong) <= 2:
        spell = 7
    elif len(wrong) <= 5:
        spell = 4
    else:
        spell = 0
    if wrong:
        tips.append(f"Possible spelling mistakes: {', '.join(wrong[:8])}.")
    res.breakdown["spelling"] = spell

    # 7. length (10)
    if 150 <= words <= 700:
        length = 10
    elif 80 <= words < 150 or 700 < words <= 1000:
        length = 5
        tips.append("Your resume is a bit short." if words < 150 else "Your resume is long. Keep it to 1 to 2 pages.")
    else:
        length = 2
        tips.append("Your resume is too short." if words < 80 else "Your resume is too long. Keep it to 1 to 2 pages.")
    res.breakdown["length"] = length

    res.score = sum(res.breakdown.values())
    res.label = "Strong" if res.score >= STRONG_MIN else "Average" if res.score >= AVERAGE_MIN else "Weak"

    feature_vector = _feature_vector_from_breakdown(
        res.breakdown,
        words=words,
        bullets=bullets,
        verbs=verbs,
        vague_count=len(vague),
        email=bool(email),
        phone=bool(phone),
        has_skills="skills" in sections,
        has_edu="education" in sections,
        has_proj="projects" in sections,
    )
    res.feature_vector = feature_vector

    model = _quality_model()
    if model is not None:
        res.model_used = "scikit-learn RandomForestRegressor"
        ranked = sorted(
            ((name, feature_vector[name]) for name in QUALITY_FEATURE_NAMES),
            key=lambda item: item[1],
        )
        for name, value in ranked[:4]:
            if value < 5.0 and name in QUALITY_FEATURE_TIPS:
                tips.insert(0, QUALITY_FEATURE_TIPS[name])

    if res.score >= STRONG_MIN:
        res.label = "Strong"
    elif res.score >= AVERAGE_MIN:
        res.label = "Average"
    else:
        res.label = "Weak"

    return res