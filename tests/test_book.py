import pytest

from errors import BusinessRuleError, ValidationError
from tests.conftest import find_book

NEW_BOOK = {
    "title": "Thiết kế hướng đối tượng",
    "author": "Nguyễn Thị Bích",
    "isbn": "978-604-9-12345-6",
    "publisher": "NXB Giáo dục",
    "publish_year": "2024",
    "category_id": "3",
    "description": "Sách về phân tích và thiết kế phần mềm.",
    "file_path": "books/lap-trinh-python.txt",
    "total_copies": "2",
    "cover_color": "#2f5d62",
}


def test_admin_creates_book(admin_client, facade):
    response = admin_client.post("/admin/books/new", data=NEW_BOOK, follow_redirects=True)

    assert response.status_code == 200
    assert "Thiết kế hướng đối tượng" in response.get_data(as_text=True)

    book = next((b for b in facade.filter_books() if b.isbn == NEW_BOOK["isbn"]), None)
    assert book is not None
    assert book.total_copies == 2
    assert book.available_copies == 2
    assert book.category_name == "Công nghệ"


def test_duplicate_isbn_is_rejected(admin_client, facade):
    before = len(facade.filter_books())
    data = dict(NEW_BOOK, isbn="978-604-1-00001-1")
    response = admin_client.post("/admin/books/new", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert "đã được dùng" in response.get_data(as_text=True)
    assert len(facade.filter_books()) == before


def test_book_validation_rejects_path_traversal(admin_client, facade):
    before = len(facade.filter_books())
    data = dict(NEW_BOOK, isbn="978-604-9-99999-9", file_path="../../etc/passwd.txt")
    response = admin_client.post("/admin/books/new", data=data, follow_redirects=True)

    assert "đường dẫn tương đối" in response.get_data(as_text=True).lower()
    assert len(facade.filter_books()) == before


def test_service_rejects_unsupported_extension(facade):
    with pytest.raises(ValidationError):
        facade.create_book(dict(NEW_BOOK, isbn="978-604-9-88888-8", file_path="books/tai-lieu.docx"))


def test_seeded_book_cannot_be_deleted_while_borrowed(admin_client, facade):
    book = find_book(facade, "Nhà Giả Kim")
    with pytest.raises(BusinessRuleError):
        facade.delete_book(book.id)

    response = admin_client.post(f"/admin/books/{book.id}/delete", follow_redirects=True)
    assert "không thể xóa" in response.get_data(as_text=True)
    assert facade.get_book(book.id).title == "Nhà Giả Kim"


def test_admin_updates_book_availability(admin_client, facade):
    book = find_book(facade, "Lập trình Python căn bản")
    original_available = book.available_copies

    data = dict(
        NEW_BOOK,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        total_copies="6",
        category_id=str(book.category_id),
    )
    response = admin_client.post(f"/admin/books/{book.id}/edit", data=data, follow_redirects=True)
    assert response.status_code == 200

    updated = facade.get_book(book.id)
    assert updated.total_copies == 6
    assert updated.available_copies == original_available + 1


def test_search_strategies_return_expected_results(facade):
    by_title = facade.search_books("python", "title")
    assert by_title["count"] == 2
    assert {book.title for book in by_title["books"]} == {
        "Lập trình Python căn bản",
        "Python nâng cao và Design Patterns",
    }

    by_author = facade.search_books("coelho", "author")
    assert [book.title for book in by_author["books"]] == ["Nhà Giả Kim"]

    by_isbn = facade.search_books("00004", "isbn")
    assert [book.title for book in by_isbn["books"]] == ["Lập trình Python căn bản"]

    by_category = facade.search_books("cong nghe", "category")
    assert by_category["count"] == 3

    by_all = facade.search_books("nha gia kim", "all")
    assert [book.title for book in by_all["books"]] == ["Nhà Giả Kim"]


def test_search_is_accent_insensitive_and_falls_back_to_all(facade):
    result = facade.search_books("so do", "title")
    assert [book.title for book in result["books"]] == ["Số Đỏ"]

    fallback = facade.search_books("python", "khong-ton-tai")
    assert fallback["criteria_label"] == "Tất cả"


def test_admin_book_list_search_is_accent_insensitive(admin_client, facade):
    response = admin_client.get("/admin/books", query_string={"q": "so do"})
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Số Đỏ" in page
    assert "Nhà Giả Kim" not in page

    technology = next(c for c in facade.list_categories() if c.name == "Công nghệ")
    filtered = admin_client.get(
        "/admin/books", query_string={"q": "so do", "category": technology.id}
    )
    assert "Số Đỏ" not in filtered.get_data(as_text=True)


def test_category_with_books_cannot_be_deleted(admin_client, facade):
    category = next(c for c in facade.list_categories() if c.name == "Văn học")
    response = admin_client.post(f"/admin/categories/{category.id}/delete", follow_redirects=True)
    assert "không thể xóa" in response.get_data(as_text=True)
    assert any(c.id == category.id for c in facade.list_categories())
