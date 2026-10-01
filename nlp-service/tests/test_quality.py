from app.quality import score_quality

STRONG = """Ali Khan
ali.khan@example.com | +92 300 1234567

Summary
Full stack web developer with one year of experience building client websites and custom content management systems for small businesses.

Skills
JavaScript, React, Node.js, Express, MongoDB, Git, REST APIs, HTML, CSS

Experience
Web Developer, Ivy Solutions, 2025 - Present
- Built and deployed 5 client websites using React and Node.js
- Developed a custom CMS that reduced content update time by 40%
- Integrated payment gateways and automated order emails
- Collaborated with designers to deliver projects on schedule
- Maintained databases and optimized slow queries for 2000+ users

Projects
Resume Parser
- Designed an NLP pipeline that extracts skills and contact details
- Implemented ranking using sentence embeddings
- Tested the system with 50 sample resumes
- Created a dashboard to review results for hiring teams

Education
Bachelor of Science in Information Technology, 2024
Completed coursework in databases, web development and software engineering. Final year project focused on building a content management platform for a local business.
"""

WEAK = """my name is ahmed
i am hard working and responsible for many things
i have developement experiance and good communication skills
email cool_boy12345@gmail.com
"""


def test_strong_resume_scores_high():
    r = score_quality(STRONG)
    assert r.label == "Strong", (r.score, r.breakdown, r.tips)


def test_weak_resume_scores_low_with_tips():
    r = score_quality(WEAK)
    assert r.label == "Weak"
    assert r.score < 50
    assert len(r.tips) >= 5


def test_missing_sections_are_reported():
    r = score_quality(WEAK)
    joined = " ".join(r.tips).lower()
    assert "skills section" in joined
    assert "education" in joined


def test_unprofessional_email_flagged():
    r = score_quality(WEAK)
    assert any("professional email" in t for t in r.tips)


def test_breakdown_adds_up_to_score():
    r = score_quality(STRONG)
    assert r.score == sum(r.breakdown.values())
    assert 0 <= r.score <= 100


def test_quality_result_uses_library_backed_model_metadata():
    r = score_quality(STRONG)
    assert r.model_used.startswith("scikit-learn")
    assert isinstance(r.feature_vector, dict)
    assert "contact_score" in r.feature_vector