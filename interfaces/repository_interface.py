"""Các interface nhỏ, tách riêng theo từng aggregate (minh họa ISP).

Service chỉ phụ thuộc vào abstraction (DIP), không phụ thuộc lớp SQLite cụ thể.
"""

from abc import ABC, abstractmethod


class IUserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username): ...

    @abstractmethod
    def get_by_id(self, user_id): ...

    @abstractmethod
    def create(self, username, password_hash, full_name, email, role): ...

    @abstractmethod
    def list_readers(self, keyword=""): ...

    @abstractmethod
    def list_admins(self): ...

    @abstractmethod
    def count_readers(self): ...

    @abstractmethod
    def set_active(self, user_id, is_active): ...


class IBookRepository(ABC):
    @abstractmethod
    def list_books(self, category_id=None, keyword=""): ...

    @abstractmethod
    def list_all(self): ...

    @abstractmethod
    def get_by_id(self, book_id): ...

    @abstractmethod
    def find_by_isbn(self, isbn): ...

    @abstractmethod
    def create(self, data): ...

    @abstractmethod
    def update(self, book_id, data): ...

    @abstractmethod
    def delete(self, book_id): ...

    @abstractmethod
    def count_books(self): ...

    @abstractmethod
    def count_copies(self): ...

    @abstractmethod
    def recent(self, limit=6): ...

    @abstractmethod
    def category_distribution(self): ...


class IBorrowRepository(ABC):
    @abstractmethod
    def create_request(self, user_id, book_id): ...

    @abstractmethod
    def get_by_id(self, record_id): ...

    @abstractmethod
    def find_open_record(self, user_id, book_id): ...

    @abstractmethod
    def find_active_loan(self, user_id, book_id): ...

    @abstractmethod
    def list_by_user(self, user_id): ...

    @abstractmethod
    def list_records(self, status=None): ...

    @abstractmethod
    def approve(self, record_id, admin_id, note=""): ...

    @abstractmethod
    def reject(self, record_id, admin_id, note=""): ...

    @abstractmethod
    def mark_returned(self, record_id): ...

    @abstractmethod
    def count_by_status(self, status): ...

    @abstractmethod
    def count_overdue(self): ...

    @abstractmethod
    def count_open_for_book(self, book_id): ...


class INotificationRepository(ABC):
    @abstractmethod
    def create(self, user_id, title, message, kind="system"): ...

    @abstractmethod
    def list_by_user(self, user_id): ...

    @abstractmethod
    def count_unread(self, user_id): ...

    @abstractmethod
    def mark_read(self, notification_id, user_id): ...

    @abstractmethod
    def mark_all_read(self, user_id): ...


class ICategoryRepository(ABC):
    @abstractmethod
    def list_all(self): ...

    @abstractmethod
    def get_by_id(self, category_id): ...

    @abstractmethod
    def find_by_name(self, name): ...

    @abstractmethod
    def create(self, name, description=""): ...

    @abstractmethod
    def update(self, category_id, name, description=""): ...

    @abstractmethod
    def delete(self, category_id): ...


class IAuditRepository(ABC):
    @abstractmethod
    def log(self, user_id, action, detail=""): ...

    @abstractmethod
    def recent(self, limit=8): ...
