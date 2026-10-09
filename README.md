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
│   ├── build.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── vercel.json
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

## Deploy on Vercel

1. Push this repository to GitHub and import it in Vercel.
2. Set **Root Directory** to `nlp-service` and leave the framework preset on
   **Other** (Vercel detects Flask from the Python project files).
3. Deploy. Vercel uses `pyproject.toml` to load the Flask app and runs
   `build.py` to install the NLTK WordNet data needed by resume validation.
4. Open the deployment URL and try a PDF and a DOCX resume.

No environment variables or external database are required. Vercel limits
function request bodies to 4.5 MB, so uploads are capped at 4 MB to leave room
for multipart form data. Larger uploads require storing the file externally
before processing it.

## Notes

- The project is designed as an MVP for resume parsing and screening.
- Validation is intentionally strict to avoid accepting junk, spam, or malicious documents.
- The quality score is based on heuristic checks rather than a production ML model.
- `requirements.txt` at the repository root installs the Vercel runtime dependencies and pytest for local development.

## Current verified status

The project test suite is passing in the current environment with:

```powershell
python -m pytest nlp-service/tests -q
```

which currently reports:

```text
36 passed
```
