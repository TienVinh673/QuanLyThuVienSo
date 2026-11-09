"""Observer Pattern — thông báo khi trạng thái mượn/trả thay đổi."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from utils import format_date


@dataclass(frozen=True)
class LibraryEvent:
    name: str
    record: object


class Observer(ABC):
    @abstractmethod
    def update(self, event): ...


class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event):
        for observer in list(self._observers):
            observer.update(event)

    @property
    def observers(self):
        return list(self._observers)


class AdminNotification(Observer):
    def __init__(self, notification_service, user_repository):
        self._notifications = notification_service
        self._users = user_repository

    def update(self, event):
        record = event.record
        if event.name == "borrow_requested":
            title = "Yêu cầu mượn mới"
            message = f"{record.reader_name} vừa gửi yêu cầu mượn “{record.book_title}”."
            kind = "request"
        elif event.name == "book_returned":
            title = "Độc giả đã trả sách"
            message = f"{record.reader_name} đã trả “{record.book_title}”. Bản sao đã được cập nhật."
            kind = "returned"
        else:
            return
        for admin in self._users.list_admins():
            self._notifications.notify(admin.id, title, message, kind)


class ReaderNotification(Observer):
    def __init__(self, notification_service):
        self._notifications = notification_service

    def update(self, event):
        record = event.record
        if event.name == "borrow_approved":
            self._notifications.notify(
                record.user_id,
                "Yêu cầu mượn được duyệt",
                f"“{record.book_title}” đã sẵn sàng. Hạn trả: {format_date(record.due_date)}.",
                "approved",
            )
        elif event.name == "borrow_rejected":
            reason = f" Lý do: {record.note}" if record.note else ""
            self._notifications.notify(
                record.user_id,
                "Yêu cầu mượn bị từ chối",
                f"Yêu cầu mượn “{record.book_title}” không được duyệt.{reason}",
                "rejected",
            )
        elif event.name == "book_returned":
            self._notifications.notify(
                record.user_id,
                "Trả sách thành công",
                f"Bạn đã trả “{record.book_title}”. Cảm ơn bạn đã sử dụng thư viện.",
                "returned",
            )
