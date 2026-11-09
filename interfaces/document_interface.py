from abc import ABC, abstractmethod


class IDocument(ABC):
    """Abstraction chung cho tài liệu điện tử (PDF, TXT...)."""

    @property
    @abstractmethod
    def title(self): ...

    @abstractmethod
    def info(self):
        """Trả về thông tin mô tả tài liệu (loại, dung lượng, tên tệp...)."""

    @abstractmethod
    def read_text(self):
        """Trả về nội dung văn bản nếu định dạng hỗ trợ, ngược lại None."""

    @abstractmethod
    def open_file(self):
        """Trả về đường dẫn tệp thật sau khi đã kiểm tra quyền."""
