from errors import BusinessRuleError, NotFoundError, PermissionDenied
from interfaces.repository_interface import (
    IAuditRepository,
    IBookRepository,
    IBorrowRepository,
)
from patterns.behavioral.observer import LibraryEvent, Subject
from utils import loan_due_date, today_str


class BorrowService(Subject):
    """Subject của Observer: phát sự kiện mỗi khi trạng thái mượn/trả thay đổi."""

    def __init__(
        self,
        borrow_repository: IBorrowRepository,
        book_repository: IBookRepository,
        audit_repository: IAuditRepository,
    ):
        super().__init__()
        self._borrows = borrow_repository
        self._books = book_repository
        self._audit = audit_repository

    def request_borrow(self, reader, book_id):
        if reader.is_admin:
            raise PermissionDenied("Tài khoản thủ thư không sử dụng chức năng mượn sách.")
        book = self._books.get_by_id(book_id)
        if book is None:
            raise NotFoundError("Không tìm thấy sách.")
        if book.available_copies < 1:
            raise BusinessRuleError("Sách hiện đã hết bản sao, vui lòng chọn sách khác.")
        if self._borrows.find_open_record(reader.id, book_id):
            raise BusinessRuleError("Bạn đã có yêu cầu hoặc phiếu mượn cho cuốn sách này.")

        record = self._borrows.create_request(reader.id, book_id)
        self._audit.log(reader.id, "Gửi yêu cầu mượn", f"“{book.title}”")
        self.notify(LibraryEvent("borrow_requested", record))
        return record

    def approve(self, admin, record_id, note=""):
        record = self._get_record(record_id)
        if record.status != "pending":
            raise BusinessRuleError("Chỉ có thể duyệt yêu cầu đang chờ.")
        book = self._books.get_by_id(record.book_id)
        if book is None:
            raise NotFoundError("Không tìm thấy sách.")
        if book.available_copies < 1:
            raise BusinessRuleError("Sách đã hết bản sao, hãy từ chối yêu cầu này.")

        self._borrows.approve(record_id, admin.id, today_str(), loan_due_date(), note.strip())
        updated = self._get_record(record_id)
        self._audit.log(admin.id, "Duyệt yêu cầu mượn", f"{updated.reader_name} — “{updated.book_title}”")
        self.notify(LibraryEvent("borrow_approved", updated))
        return updated

    def reject(self, admin, record_id, note=""):
        record = self._get_record(record_id)
        if record.status != "pending":
            raise BusinessRuleError("Chỉ có thể từ chối yêu cầu đang chờ.")
        self._borrows.reject(record_id, admin.id, note.strip())
        updated = self._get_record(record_id)
        self._audit.log(admin.id, "Từ chối yêu cầu mượn", f"{updated.reader_name} — “{updated.book_title}”")
        self.notify(LibraryEvent("borrow_rejected", updated))
        return updated

    def return_book(self, actor, record_id):
        record = self._get_record(record_id)
        if not actor.is_admin and record.user_id != actor.id:
            raise PermissionDenied("Bạn chỉ có thể trả sách trong phiếu mượn của mình.")
        if record.status != "borrowed":
            raise BusinessRuleError("Phiếu mượn này không ở trạng thái đang mượn.")

        self._borrows.mark_returned(record_id)
        updated = self._get_record(record_id)
        self._audit.log(actor.id, "Trả sách", f"{updated.reader_name} — “{updated.book_title}”")
        self.notify(LibraryEvent("book_returned", updated))
        return updated

    def list_for_user(self, user_id):
        return self._borrows.list_by_user(user_id)

    def list_records(self, status=None):
        return self._borrows.list_records(status)

    def open_record_for(self, user_id, book_id):
        return self._borrows.find_open_record(user_id, book_id)

    def active_loan_for(self, user_id, book_id):
        return self._borrows.find_active_loan(user_id, book_id)

    def pending_count(self):
        return self._borrows.count_by_status("pending")

    def statistics(self):
        return {
            "pending": self._borrows.count_by_status("pending"),
            "borrowed": self._borrows.count_by_status("borrowed"),
            "returned": self._borrows.count_by_status("returned"),
            "rejected": self._borrows.count_by_status("rejected"),
            "overdue": self._borrows.count_overdue(),
        }

    def recent_activity(self, limit=7):
        return self._audit.recent(limit)

    def _get_record(self, record_id):
        record = self._borrows.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Không tìm thấy phiếu mượn.")
        return record
