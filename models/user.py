from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    full_name: str
    email: str
    role: str
    is_active: int
    created_at: str
    open_loans: int = 0

    @classmethod
    def from_row(cls, row):
        data = dict(row)
        data.pop("password_hash", None)
        return cls(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            email=row["email"] or "",
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            open_loans=data.get("open_loans", 0),
        )

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def role_label(self):
        return "Thủ thư" if self.is_admin else "Độc giả"

    @property
    def initials(self):
        parts = [part for part in self.full_name.split() if part]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][0].upper()
        return (parts[0][0] + parts[-1][0]).upper()
