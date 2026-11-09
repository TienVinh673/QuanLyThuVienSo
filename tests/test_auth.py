from werkzeug.security import check_password_hash


def test_login_admin_redirects_to_dashboard(client):
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")


def test_login_reader_redirects_to_home(reader_client):
    response = reader_client.get("/")
    assert response.status_code == 200
    assert "Không gian đọc" in response.get_data(as_text=True)


def test_wrong_password_shows_error(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "sai-mat-khau"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "không đúng" in response.get_data(as_text=True)


def test_anonymous_user_is_redirected_to_login(client):
    response = client.get("/admin/books")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_reader_cannot_reach_admin_area(reader_client):
    response = reader_client.get("/admin")
    assert response.status_code == 403
    assert "Chỉ thủ thư" in response.get_data(as_text=True)


def test_admin_required_blocks_reader_on_post(reader_client, facade):
    response = reader_client.post(
        "/admin/books/new",
        data={"title": "Sách lạ", "author": "Ai đó", "isbn": "999-999", "total_copies": 1},
    )
    assert response.status_code == 302
    assert not any(book.title == "Sách lạ" for book in facade.filter_books())


def test_register_creates_hashed_reader_and_logs_in(client, facade):
    response = client.post(
        "/register",
        data={
            "full_name": "Nguyễn Văn Mới",
            "username": "bandocmoi",
            "email": "moi@example.com",
            "password": "matkhau123",
            "confirm_password": "matkhau123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    user = next((u for u in facade.list_readers() if u.username == "bandocmoi"), None)
    assert user is not None
    assert user.role == "reader"
    assert user.password_hash != "matkhau123"
    assert check_password_hash(user.password_hash, "matkhau123")

    home = client.get("/")
    assert home.status_code == 200
    assert "Nguyễn Văn Mới" in home.get_data(as_text=True)


def test_register_rejects_duplicate_username(client):
    response = client.post(
        "/register",
        data={
            "full_name": "Trùng Tên",
            "username": "reader",
            "password": "matkhau123",
            "confirm_password": "matkhau123",
        },
        follow_redirects=True,
    )
    assert "đã tồn tại" in response.get_data(as_text=True)


def test_locked_reader_cannot_login(app, facade):
    facade.set_reader_active(2, False)
    client = app.test_client()
    response = client.post(
        "/login",
        data={"username": "reader", "password": "reader123"},
        follow_redirects=True,
    )
    assert "đã bị khóa" in response.get_data(as_text=True)
