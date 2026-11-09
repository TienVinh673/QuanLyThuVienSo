"""Facade Pattern — một điểm vào duy nhất cho tầng giao diện.

View chỉ gọi các phương thức của LibraryFacade; Facade điều phối AuthService,
BookService, BorrowService, NotificationService, DocumentService.
"""

from errors import AppError


class LibraryFacade:
    def __init__(
        self,
        auth_service,
        book_service,
        category_service,
        borrow_service,
        notification_service,
        document_service,
    ):
        self._auth = auth_service
        self._books = book_service
        self._categories = category_service
        self._borrows = borrow_service
        self._notifications = notification_service
        self._documents = document_service

    # ---------- Xác thực ----------
    def login(self, username, password):
        return self._auth.login(username, password)

    def register(self, full_name, username, password, confirm_password, email=""):
        return self._auth.register(full_name, username, password, confirm_password, email)

    def get_user(self, user_id):
        return self._auth.get_user(user_id)

    # ---------- Sách & tìm kiếm ----------
    def search_books(self, keyword, criteria="all"):
        return self._books.search(keyword, criteria)

    def search_options(self):
        return self._books.strategy_options()

    def get_book(self, book_id):
        return self._books.get_book(book_id)

    def filter_books(self, category_id=None, keyword=""):
        return self._books.list_books(category_id, keyword)

    def recent_books(self, limit=6):
        return self._books.recent_books(limit)

    def book_detail(self, user, book_id):
        book = self._books.get_book(book_id)
        detail = {
            "book": book,
            "open_record": None,
            "active_loan": None,
            "can_open": False,
            "document": None,
            "access_message": "",
        }
        if user is None:
            detail["access_message"] = "Đăng nhập để mượn hoặc mở tài liệu."
            return detail

        if not user.is_admin:
            detail["open_record"] = self._borrows.open_record_for(user.id, book.id)
            detail["active_loan"] = self._borrows.active_loan_for(user.id, book.id)

        if not book.file_path:
            detail["access_message"] = "Sách này chưa được đính kèm tệp tài liệu."
            return detail

        try:
            detail["document"] = self._documents.proxy_for(user, book).info()
            detail["can_open"] = True
            detail["access_message"] = "Bạn có quyền mở tài liệu này."
        except AppError as error:
            detail["access_message"] = error.message
        return detail

    def create_book(self, raw):
        return self._books.create_book(raw)

    def update_book(self, book_id, raw):
        return self._books.update_book(book_id, raw)

    def delete_book(self, book_id):
        self._books.delete_book(book_id)

    def asset_files(self):
        root = self._documents.assets_root
        if not root.exists():
            return []
        files = []
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".pdf", ".txt"}:
                files.append(path.relative_to(root).as_posix())
        return files

    # ---------- Danh mục ----------
    def list_categories(self):
        return self._categories.list_categories()

    def create_category(self, name, description=""):
        return self._categories.create_category(name, description)

    def update_category(self, category_id, name, description=""):
        self._categories.update_category(category_id, name, description)

    def delete_category(self, category_id):
        self._categories.delete_category(category_id)

    # ---------- Độc giả ----------
    def list_readers(self, keyword=""):
        return self._auth.list_readers(keyword)

    def set_reader_active(self, user_id, is_active):
        return self._auth.set_reader_active(user_id, is_active)

    # ---------- Mượn / trả ----------
    def request_borrow(self, reader, book_id):
        return self._borrows.request_borrow(reader, book_id)

    def approve_request(self, admin, record_id, note=""):
        return self._borrows.approve(admin, record_id, note)

    def reject_request(self, admin, record_id, note=""):
        return self._borrows.reject(admin, record_id, note)

    def return_book(self, actor, record_id):
        return self._borrows.return_book(actor, record_id)

    def list_requests(self, status=None):
        return self._borrows.list_records(status)

    def list_user_loans(self, user_id):
        return self._borrows.list_for_user(user_id)

    def pending_request_count(self):
        return self._borrows.pending_count()

    def borrow_statistics(self):
        return self._borrows.statistics()

    # ---------- Thông báo ----------
    def list_notifications(self, user_id):
        return self._notifications.list_for_user(user_id)

    def unread_count(self, user_id):
        return self._notifications.unread_count(user_id)

    def mark_notification_read(self, notification_id, user_id):
        self._notifications.mark_read(notification_id, user_id)

    def mark_all_notifications_read(self, user_id):
        self._notifications.mark_all_read(user_id)

    # ---------- Tài liệu (qua Proxy) ----------
    def document_view(self, user, book_id):
        book = self._books.get_book(book_id)
        proxy = self._documents.proxy_for(user, book)
        info = proxy.info()
        text = proxy.read_text() if info["supports_text"] else None
        return {"book": book, "info": info, "text": text}

    def document_file(self, user, book_id):
        book = self._books.get_book(book_id)
        return self._documents.proxy_for(user, book).open_file()

    # ---------- Dashboard ----------
    def admin_dashboard(self):
        book_stats = self._books.statistics()
        borrow_stats = self._borrows.statistics()
        return {
            "book_stats": book_stats,
            "borrow_stats": borrow_stats,
            "readers": self._auth.count_readers(),
            "pending_requests": self._borrows.list_records("pending")[:4],
            "recent_records": self._borrows.list_records()[:6],
            "recent_activity": self._borrows.recent_activity(7),
            "category_distribution": book_stats["category_distribution"],
        }

    def reader_dashboard(self, user):
        records = self._borrows.list_for_user(user.id)
        return {
            "current_loans": [record for record in records if record.status == "borrowed"],
            "pending_requests": [record for record in records if record.status == "pending"],
            "history": records[:5],
            "notifications": self._notifications.list_for_user(user.id)[:4],
            "unread_notifications": self._notifications.unread_count(user.id),
            "recent_books": self._books.recent_books(6),
        }
