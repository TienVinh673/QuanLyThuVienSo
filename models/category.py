from dataclasses import dataclass


@dataclass
class Category:
    id: int
    name: str
    description: str = ""
    book_count: int = 0

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            book_count=data.get("book_count", 0),
        )
