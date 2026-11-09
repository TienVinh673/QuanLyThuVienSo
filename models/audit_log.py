from dataclasses import dataclass


@dataclass
class AuditLog:
    id: int
    user_id: int | None
    action: str
    detail: str
    created_at: str
    actor_name: str = ""

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            action=row["action"],
            detail=row["detail"] or "",
            created_at=row["created_at"],
            actor_name=data.get("actor_name") or "Hệ thống",
        )
