# Resume Parser

A Python-based resume parsing and screening project that validates uploaded resumes, extracts structured candidate details, and scores the quality of the resume.

## What this project does

- Validates PDF and DOCX resume files
- Rejects malformed, malicious, gibberish, or non-resume content
- Extracts candidate information such as:
  - name
  - email
  - phone
  - LinkedIn
  - GitHub
  - skills
  - education
- Scores resume quality using a heuristic model
- Shows improvement tips for weak resumes
- Offers a small Flask web interface for uploading files

## Project structure

```text
resume_parser/
├── .gitignore
├── README.md
├── requirements.txt
├── conftest.py
├── nlp-service/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── extraction.py
│   │   ├── quality.py
│   │   ├── validation.py
│   │   ├── web.py
│   │   └── templates/
│   │       └── index.html
│   ├── tests/
│   │   ├── test_extraction.py
│   │   ├── test_quality.py
│   │   ├── test_validation.py
│   │   └── test_web_app.py
│   ├── show_text.py
│   └── results_*.csv
├── samples/
│   ├── good/
│   ├── mine/
│   └── rejected/
└── .venv/
```

## Setup

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

3. Run tests

```powershell
python -m pytest nlp-service/tests -q
```

## Run the web app

From the project root:

```powershell
cd nlp-service
python app/web.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Notes

- The project is designed as an MVP for resume parsing and screening.
- Validation is intentionally strict to avoid accepting junk, spam, or malicious documents.
- The quality score is based on heuristic checks rather than a production ML model.

## Current verified status

The project test suite is passing in the current environment with:

```powershell
python -m pytest nlp-service/tests -q
```

which currently reports:

```text
32 passed
```
