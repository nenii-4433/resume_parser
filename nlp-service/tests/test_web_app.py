import io

from app.web import create_app


def test_homepage_renders_upload_form():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Upload resume" in response.data
    assert b"input type=\"file\"" in response.data


def test_oversized_upload_shows_a_user_facing_error():
    app = create_app()
    app.config["MAX_CONTENT_LENGTH"] = 32

    response = app.test_client().post(
        "/",
        data={"resume": (io.BytesIO(b"x" * 64), "resume.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert b"maximum file size is 4 MB" in response.data
