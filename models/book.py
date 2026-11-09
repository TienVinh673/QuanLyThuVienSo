from dataclasses import dataclass
from pathlib import Path


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str
    category_id: int | None
    publisher: str
    publish_year: int | None
    description: str
    file_path: str
    total_copies: int
    available_copies: int
    cover_color: str
    created_at: str
    category_name: str = "Chưa phân loại"

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"],
            category_id=row["category_id"],
            publisher=row["publisher"] or "",
            publish_year=row["publish_year"],
            description=row["description"] or "",
            file_path=row["file_path"] or "",
            total_copies=row["total_copies"],
            available_copies=row["available_copies"],
            cover_color=row["cover_color"] or "#145c4c",
            created_at=row["created_at"],
            category_name=data.get("category_name") or "Chưa phân loại",
        )

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def file_extension(self):
        suffix = Path(self.file_path).suffix.lstrip(".").upper() if self.file_path else ""
        return suffix or "—"

    @property
    def is_borrowed_out(self):
        return self.available_copies < self.total_copies
