from app.web import create_app


def test_homepage_renders_upload_form():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Upload resume" in response.data
    assert b"input type=\"file\"" in response.data
