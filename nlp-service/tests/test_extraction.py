from app.extraction import (
    extract_education,
    extract_email,
    extract_info,
    extract_name,
    extract_phone,
    extract_skills,
)

RESUME = """ALI KHAN
ali.khan@Example.com | +92 300 1234567
github.com/alikhan | linkedin.com/in/ali-khan

Summary
Full stack web developer who excels at building client websites.

Skills
JavaScript, React.js, Node.js, Express, MongoDB, Git, REST APIs, HTML, CSS

Experience
Web Developer, Ivy Solutions, 2025 - Present
- Built client websites and a custom CMS

Education
Bachelor of Science in Information Technology, 2020 - 2024
Intermediate in Computer Science, 2018
"""


def test_email_is_lowercased():
    assert extract_email(RESUME) == "ali.khan@example.com"


def test_phone_found():
    assert extract_phone(RESUME) == "+92 300 1234567"


def test_phone_ignores_years():
    assert extract_phone("Education 2020 - 2024") is None


def test_name_from_top_line():
    assert extract_name(RESUME) == "Ali Khan"


def test_name_skips_section_headers():
    assert extract_name("Summary\nSkills\nSara Ahmed\nsara@x.com") == "Sara Ahmed"


def test_skills_found_with_aliases():
    skills = extract_skills(RESUME)
    for expected in ["JavaScript", "React", "Node.js", "Express", "MongoDB", "Git", "REST API", "HTML", "CSS"]:
        assert expected in skills, skills


def test_ambiguous_words_not_counted_as_skills():
    assert "Excel" not in extract_skills("I excel at teamwork and can express ideas clearly.")


def test_education_entries_with_years():
    edu = extract_education(RESUME)
    assert len(edu) == 2
    assert edu[0]["years"] == ["2020", "2024"]


def test_extract_info_combines_everything():
    info = extract_info(RESUME)
    assert info.name == "Ali Khan"
    assert info.email == "ali.khan@example.com"
    assert info.github == "github.com/alikhan"
    assert info.linkedin == "linkedin.com/in/ali-khan"
    assert "React" in info.skills