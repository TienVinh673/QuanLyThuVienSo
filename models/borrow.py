from dataclasses import dataclass
from datetime import date

STATUS_LABELS = {
    "pending": "Chờ duyệt",
    "borrowed": "Đang mượn",
    "returned": "Đã trả",
    "rejected": "Từ chối",
    "cancelled": "Đã hủy",
}

STATUS_TONES = {
    "pending": "warn",
    "borrowed": "info",
    "returned": "success",
    "rejected": "danger",
    "cancelled": "muted",
}


@dataclass
class BorrowRecord:
    id: int
    user_id: int
    book_id: int
    request_date: str
    borrow_date: str | None
    due_date: str | None
    return_date: str | None
    status: str
    note: str
    processed_by: int | None
    processed_at: str | None
    book_title: str = ""
    book_author: str = ""
    book_cover_color: str = "#145c4c"
    reader_name: str = ""
    reader_username: str = ""

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            book_id=row["book_id"],
            request_date=row["request_date"],
            borrow_date=row["borrow_date"],
            due_date=row["due_date"],
            return_date=row["return_date"],
            status=row["status"],
            note=row["note"] or "",
            processed_by=row["processed_by"],
            processed_at=row["processed_at"],
            book_title=data.get("book_title") or "",
            book_author=data.get("book_author") or "",
            book_cover_color=data.get("book_cover_color") or "#145c4c",
            reader_name=data.get("reader_name") or "",
            reader_username=data.get("reader_username") or "",
        )

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def status_tone(self):
        return STATUS_TONES.get(self.status, "muted")

    @property
    def is_open(self):
        return self.status in ("pending", "borrowed")

    @property
    def is_overdue(self):
        if self.status != "borrowed" or not self.due_date:
            return False
        return date.fromisoformat(self.due_date) < date.today()

    @property
    def days_left(self):
        if self.status != "borrowed" or not self.due_date:
            return None
        return (date.fromisoformat(self.due_date) - date.today()).days

    @property
    def due_progress(self):
        """Phần trăm thời gian đã trôi qua của kỳ hạn 14 ngày (dùng cho thanh tiến độ)."""
        if self.status != "borrowed" or not self.due_date or not self.borrow_date:
            return 0
        total = (date.fromisoformat(self.due_date) - date.fromisoformat(self.borrow_date)).days or 1
        elapsed = (date.today() - date.fromisoformat(self.borrow_date)).days
        return max(0, min(100, round(elapsed / total * 100)))
