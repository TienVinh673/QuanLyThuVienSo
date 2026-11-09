import pytest

from main import create_app


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "library-test.db"),
            "SEED_DEMO": True,
        }
    )
    yield application


@pytest.fixture()
def facade(app):
    return app.extensions["facade"]


@pytest.fixture()
def client(app):
    return app.test_client()


def login_client(app, username, password):
    client = app.test_client()
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 302
    return client


@pytest.fixture()
def admin_client(app):
    return login_client(app, "admin", "admin123")


@pytest.fixture()
def reader_client(app):
    return login_client(app, "reader", "reader123")


def find_book(facade, title):
    return next(book for book in facade.filter_books() if book.title == title)
