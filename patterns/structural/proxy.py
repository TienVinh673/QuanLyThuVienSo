"""Proxy Pattern — kiểm soát quyền truy cập tài liệu điện tử.

DocumentProxy đứng trước tài liệu thật: xác thực người dùng, kiểm tra phiếu mượn,
kiểm tra đường dẫn tệp rồi mới khởi tạo đối tượng tài liệu thật (lazy).
"""

from pathlib import Path

from errors import NotFoundError, PermissionDenied
from interfaces.document_interface import IDocument
from patterns.creational.factory_method import DocumentFactory


class DocumentProxy(IDocument):
    def __init__(self, path, assets_root, user, book, borrow_repository):
        self._path = Path(path)
        self._assets_root = Path(assets_root).resolve()
        self._user = user
        self._book = book
        self._borrow_repository = borrow_repository
        self._real_document = None

    @property
    def title(self):
        return self._book.title

    def _check_access(self):
        if self._user is None:
            raise PermissionDenied("Vui lòng đăng nhập để mở tài liệu.")
        if self._user.is_admin:
            return
        loan = self._borrow_repository.find_active_loan(self._user.id, self._book.id)
        if loan is None:
            raise PermissionDenied(
                f"Bạn chưa mượn “{self._book.title}”. Hãy gửi yêu cầu mượn và chờ thủ thư duyệt."
            )

    def _verified_path(self):
        path = self._path.resolve()
        if self._assets_root not in path.parents:
            raise PermissionDenied("Đường dẫn tài liệu không hợp lệ.")
        if not path.is_file():
            raise NotFoundError("Tệp tài liệu không tồn tại trên máy chủ.")
        return path

    def _real(self):
        if self._real_document is None:
            self._real_document = DocumentFactory.create_document(
                self._verified_path(), display_name=self._book.title
            )
        return self._real_document

    def info(self):
        self._check_access()
        info = self._real().info()
        info["protected"] = True
        return info

    def read_text(self):
        self._check_access()
        return self._real().read_text()

    def open_file(self):
        self._check_access()
        return self._verified_path()
