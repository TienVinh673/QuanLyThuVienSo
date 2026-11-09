from pathlib import Path
from types import SimpleNamespace

import pytest

from database.db_manager import DatabaseManager
from errors import PermissionDenied, UnsupportedDocumentError
from patterns.behavioral.observer import Observer
from patterns.behavioral.strategy import SearchByAuthor, SearchByTitle, SearchContext
from patterns.creational.factory_method import DocumentFactory, PDFDocument, TextDocument
from patterns.creational.singleton import SingletonMeta
from patterns.structural.proxy import DocumentProxy
from tests.conftest import find_book


def test_singleton_returns_same_database_manager():
    assert DatabaseManager() is DatabaseManager()
    assert type(DatabaseManager()) is DatabaseManager
    assert isinstance(DatabaseManager, SingletonMeta)


def test_singleton_keeps_configuration_between_instances(app):
    first = DatabaseManager()
    second = DatabaseManager()
    assert Path(first.db_path) == Path(second.db_path) == Path(app.config["DATABASE"])


def test_factory_creates_document_by_extension(app):
    assets = Path(app.config["ASSETS_DIR"])

    pdf = DocumentFactory.create_document(assets / "books" / "nha-gia-kim.pdf", "Nhà Giả Kim")
    txt = DocumentFactory.create_document(assets / "books" / "clean-code.txt", "Clean Code")

    assert isinstance(pdf, PDFDocument)
    assert isinstance(txt, TextDocument)
    assert pdf.info()["kind"] == "PDF"
    assert txt.info()["kind"] == "Văn bản"
    assert "Clean Code" in txt.read_text()
    assert DocumentFactory.supported_extensions() == ["PDF", "TXT"]


def test_factory_rejects_unsupported_extension():
    with pytest.raises(UnsupportedDocumentError):
        DocumentFactory.create_document(Path("tai-lieu.docx"))


def test_proxy_allows_admin_even_without_loan(facade):
    admin = facade.get_user(1)
    book = find_book(facade, "Clean Code")
    document = facade.book_detail(admin, book.id)

    assert document["can_open"] is True
    assert document["document"]["protected"] is True


def test_proxy_allows_reader_with_active_loan(facade, app):
    reader = facade.get_user(2)
    book = find_book(facade, "Nhà Giả Kim")
    proxy = DocumentProxy(
        Path(app.config["ASSETS_DIR"]) / book.file_path,
        app.config["ASSETS_DIR"],
        reader,
        book,
        facade._borrows._borrows,
    )

    info = proxy.info()
    assert info["protected"] is True
    assert info["title"] == "Nhà Giả Kim"


def test_proxy_denies_reader_without_loan(facade):
    reader = facade.get_user(2)
    book = find_book(facade, "Clean Code")

    with pytest.raises(PermissionDenied):
        facade.document_view(reader, book.id)

    with pytest.raises(PermissionDenied):
        facade.document_file(reader, book.id)


def test_proxy_denies_path_outside_assets(app, facade):
    admin = facade.get_user(1)
    book = find_book(facade, "Clean Code")
    outside = Path(app.config["ASSETS_DIR"]).parent / "database" / "library.db"

    proxy = DocumentProxy(outside, app.config["ASSETS_DIR"], admin, book, facade._borrows._borrows)
    with pytest.raises(PermissionDenied):
        proxy.open_file()


def test_observer_receives_events_in_order(facade):
    events = []

    class Recorder(Observer):
        def update(self, event):
            events.append(event.name)

    recorder = Recorder()
    facade._borrows.attach(recorder)
    try:
        reader = facade.get_user(2)
        admin = facade.get_user(1)
        book = find_book(facade, "Dế Mèn Phiêu Lưu Ký")
        record = facade.request_borrow(reader, book.id)
        facade.approve_request(admin, record.id)
        facade.return_book(reader, record.id)
    finally:
        facade._borrows.detach(recorder)

    assert events == ["borrow_requested", "borrow_approved", "book_returned"]


def test_strategy_context_switches_algorithm(facade):
    books = facade.filter_books()
    title_hits = SearchByTitle().search(books, "python")
    author_hits = SearchByAuthor().search(books, "python")

    assert len(title_hits) == 2
    assert author_hits == []
    assert SearchContext.strategy_for("author") is not SearchContext.strategy_for("title")


def test_facade_orchestrates_borrow_with_one_call(facade):
    reader = facade.get_user(2)
    admin = facade.get_user(1)
    book = find_book(facade, "Clean Code")

    record = facade.request_borrow(reader, book.id)
    assert next(r for r in facade.list_requests("pending") if r.id == record.id).status == "pending"

    facade.approve_request(admin, record.id)
    loans = facade.list_user_loans(reader.id)
    assert any(loan.id == record.id and loan.status == "borrowed" for loan in loans)

    facade.return_book(reader, record.id)
    loans = facade.list_user_loans(reader.id)
    assert any(loan.id == record.id and loan.status == "returned" for loan in loans)
