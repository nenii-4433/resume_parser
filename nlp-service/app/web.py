from __future__ import annotations

from flask import Flask, render_template, request

from app.extraction import extract_info
from app.quality import score_quality
from app.validation import validate_resume


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")

    @app.route("/", methods=["GET", "POST"])
    def index():
        result = None
        error = None

        if request.method == "POST":
            file = request.files.get("resume")
            if not file or file.filename == "":
                error = "Please choose a resume file first."
            else:
                data = file.read()
                validation = validate_resume(file.filename, data)

                if validation.status != "ok":
                    error = "; ".join(validation.reasons) or "Resume could not be validated."
                else:
                    info = extract_info(validation.text)
                    quality = score_quality(validation.text)
                    result = {
                        "name": info.name or "Not found",
                        "email": info.email or "Not found",
                        "phone": info.phone or "Not found",
                        "linkedin": info.linkedin or "Not found",
                        "github": info.github or "Not found",
                        "skills": info.skills,
                        "education": info.education,
                        "quality_score": quality.score,
                        "quality_label": quality.label,
                        "quality_tips": quality.tips,
                        "status": validation.status,
                    }

        return render_template("index.html", result=result, error=error)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
