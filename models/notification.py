from dataclasses import dataclass

KIND_TONES = {
    "request": "warn",
    "approved": "success",
    "rejected": "danger",
    "returned": "info",
    "system": "muted",
}


@dataclass
class Notification:
    id: int
    user_id: int
    title: str
    message: str
    kind: str
    is_read: int
    created_at: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            message=row["message"],
            kind=row["kind"],
            is_read=row["is_read"],
            created_at=row["created_at"],
        )

    @property
    def tone(self):
        return KIND_TONES.get(self.kind, "muted")
