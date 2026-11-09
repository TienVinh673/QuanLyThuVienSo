from pathlib import Path

from errors import NotFoundError
from interfaces.repository_interface import IBorrowRepository
from patterns.structural.proxy import DocumentProxy


class DocumentService:
    def __init__(self, assets_root, borrow_repository: IBorrowRepository):
        self._assets_root = Path(assets_root)
        self._borrows = borrow_repository

    @property
    def assets_root(self):
        return self._assets_root

    def proxy_for(self, user, book):
        if not book.file_path:
            raise NotFoundError("Sách này chưa được đính kèm tệp tài liệu.")
        path = self._assets_root / book.file_path
        return DocumentProxy(path, self._assets_root, user, book, self._borrows)
