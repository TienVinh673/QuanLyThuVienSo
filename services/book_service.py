import re
from pathlib import Path

from errors import BusinessRuleError, NotFoundError, ValidationError
from interfaces.repository_interface import (
    IBookRepository,
    IBorrowRepository,
    ICategoryRepository,
)
from patterns.behavioral.strategy import SearchContext
from utils import parse_year

COVER_PALETTE = [
    "#145c4c", "#7a3b2e", "#3f5d7d", "#6b5b3e",
    "#8a4b5c", "#2f5d62", "#8c6b2f", "#414a6b",
]
SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


class BookService:
    def __init__(
        self,
        book_repository: IBookRepository,
        category_repository: ICategoryRepository,
        borrow_repository: IBorrowRepository,
    ):
        self._books = book_repository
        self._categories = category_repository
        self._borrows = borrow_repository
        self._search = SearchContext(book_repository)

    def list_books(self, category_id=None, keyword=""):
        keyword = (keyword or "").strip()
        if not keyword:
            return self._books.list_books(category_id)
        books = self._search.search(keyword)
        if category_id:
            books = [book for book in books if book.category_id == category_id]
        return books

    def search(self, keyword, criteria="all"):
        keyword = (keyword or "").strip()
        books = self._search.search(keyword, criteria) if keyword else self._books.list_all()
        strategy = self._search.strategy_for(criteria)
        return {
            "books": books,
            "keyword": keyword,
            "criteria": criteria,
            "criteria_label": strategy.label,
            "count": len(books),
        }

    def get_book(self, book_id):
        book = self._books.get_by_id(book_id)
        if book is None:
            raise NotFoundError("Không tìm thấy sách.")
        return book

    def create_book(self, raw):
        data = self._build_payload(raw)
        self._books.create(data)
        return self._books.find_by_isbn(data["isbn"])

    def update_book(self, book_id, raw):
        current = self.get_book(book_id)
        data = self._build_payload(raw, current)

        borrowed_out = current.total_copies - current.available_copies
        if data["total_copies"] < borrowed_out:
            raise BusinessRuleError(
                f"Đang có {borrowed_out} bản sao được mượn, không thể giảm tổng số xuống dưới mức này."
            )
        data["available_copies"] = data["total_copies"] - borrowed_out
        self._books.update(book_id, data)
        return self.get_book(book_id)

    def delete_book(self, book_id):
        book = self.get_book(book_id)
        open_records = self._borrows.count_open_for_book(book_id)
        if open_records:
            raise BusinessRuleError(
                f"“{book.title}” còn {open_records} phiếu mượn chưa kết thúc, không thể xóa."
            )
        self._books.delete(book_id)

    def recent_books(self, limit=6):
        return self._books.recent(limit)

    def statistics(self):
        return {
            "book_titles": self._books.count_books(),
            "copies": self._books.count_copies(),
            "category_distribution": self._books.category_distribution(),
        }

    def strategy_options(self):
        return SearchContext.options()

    def _build_payload(self, raw, current=None):
        title = (raw.get("title") or "").strip()
        author = (raw.get("author") or "").strip()
        isbn = (raw.get("isbn") or "").strip()
        publisher = (raw.get("publisher") or "").strip()
        description = (raw.get("description") or "").strip()
        file_path = (raw.get("file_path") or "").strip().replace("\\", "/")
        cover_color = (raw.get("cover_color") or "").strip() or COVER_PALETTE[0]

        if len(title) < 2:
            raise ValidationError("Tên sách cần ít nhất 2 ký tự.")
        if len(author) < 2:
            raise ValidationError("Tên tác giả cần ít nhất 2 ký tự.")
        if not isbn:
            raise ValidationError("Vui lòng nhập mã ISBN.")

        existing = self._books.find_by_isbn(isbn)
        if existing and (current is None or existing.id != current.id):
            raise ValidationError(f"Mã ISBN “{isbn}” đã được dùng cho sách khác.")

        try:
            total_copies = int(raw.get("total_copies") or 1)
        except (TypeError, ValueError):
            raise ValidationError("Số bản sao phải là số nguyên.")
        if total_copies < 1:
            raise ValidationError("Số bản sao phải ít nhất là 1.")

        publish_year = None
        if (raw.get("publish_year") or "").strip():
            publish_year = parse_year(raw.get("publish_year"))
            if publish_year is None:
                raise ValidationError("Năm xuất bản không hợp lệ.")

        category_id = None
        if (raw.get("category_id") or "").strip():
            try:
                category_id = int(raw.get("category_id"))
            except (TypeError, ValueError):
                raise ValidationError("Danh mục không hợp lệ.")
            if self._categories.get_by_id(category_id) is None:
                raise ValidationError("Danh mục đã chọn không tồn tại.")

        if file_path:
            path = Path(file_path)
            if ".." in path.parts or path.is_absolute():
                raise ValidationError("Đường dẫn tệp phải là đường dẫn tương đối trong thư mục assets.")
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValidationError("Chỉ hỗ trợ tệp tài liệu PDF hoặc TXT.")

        if not re.match(r"^#[0-9a-fA-F]{6}$", cover_color):
            cover_color = COVER_PALETTE[0]

        return {
            "title": title,
            "author": author,
            "isbn": isbn,
            "category_id": category_id,
            "publisher": publisher,
            "publish_year": publish_year,
            "description": description,
            "file_path": file_path,
            "total_copies": total_copies,
            "available_copies": total_copies,
            "cover_color": cover_color,
        }
