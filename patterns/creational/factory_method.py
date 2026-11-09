"""Factory Method Pattern — khởi tạo đối tượng tài liệu theo định dạng tệp.

Bổ sung định dạng mới = thêm một BaseDocumentFactory mới vào _FACTORIES,
không sửa nơi gọi DocumentFactory.create_document.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from errors import UnsupportedDocumentError
from interfaces.document_interface import IDocument
from utils import human_size


class StoredDocument(IDocument):
    kind = "Tài liệu"
    supports_text = False

    def __init__(self, path, display_name=""):
        self._path = Path(path)
        self._display_name = display_name.strip() or self._path.stem

    @property
    def title(self):
        return self._display_name

    def info(self):
        size = self._path.stat().st_size if self._path.exists() else None
        return {
            "title": self.title,
            "kind": self.kind,
            "extension": self._path.suffix.lstrip(".").upper(),
            "filename": self._path.name,
            "size": human_size(size),
            "supports_text": self.supports_text,
        }

    def read_text(self):
        return None

    def open_file(self):
        return self._path


class TextDocument(StoredDocument):
    kind = "Văn bản"
    supports_text = True

    def read_text(self):
        try:
            return self._path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return self._path.read_text(encoding="utf-8", errors="replace")


class PDFDocument(StoredDocument):
    kind = "PDF"


class BaseDocumentFactory(ABC):
    extension = ""

    def supports(self, path):
        return Path(path).suffix.lower() == f".{self.extension}"

    @abstractmethod
    def create_document(self, path, display_name=""):
        ...


class TextDocumentFactory(BaseDocumentFactory):
    extension = "txt"

    def create_document(self, path, display_name=""):
        return TextDocument(path, display_name)


class PDFDocumentFactory(BaseDocumentFactory):
    extension = "pdf"

    def create_document(self, path, display_name=""):
        return PDFDocument(path, display_name)


class DocumentFactory:
    """Điểm vào duy nhất; tự chọn factory con phù hợp với phần mở rộng tệp."""

    _factories = (PDFDocumentFactory(), TextDocumentFactory())

    @classmethod
    def create_document(cls, path, display_name=""):
        for factory in cls._factories:
            if factory.supports(path):
                return factory.create_document(path, display_name)
        extension = Path(path).suffix.lstrip(".").upper() or "không xác định"
        raise UnsupportedDocumentError(
            f"Định dạng {extension} chưa được hỗ trợ. Hệ thống hiện đọc được PDF và TXT."
        )

    @classmethod
    def supported_extensions(cls):
        return [factory.extension.upper() for factory in cls._factories]
