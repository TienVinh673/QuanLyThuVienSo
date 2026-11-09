from interfaces.repository_interface import IAuditRepository
from models.audit_log import AuditLog
from utils import now_str


class AuditRepository(IAuditRepository):
    def __init__(self, db_manager):
        self._db = db_manager

    def log(self, user_id, action, detail=""):
        with self._db.get_connection() as connection:
            connection.execute(
                "INSERT INTO audit_logs (user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
                (user_id, action, detail, now_str()),
            )

    def recent(self, limit=8):
        with self._db.get_connection() as connection:
            rows = connection.execute(
                """SELECT a.*, u.full_name AS actor_name
                   FROM audit_logs a
                   LEFT JOIN users u ON u.id = a.user_id
                   ORDER BY a.created_at DESC, a.id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [AuditLog.from_row(row) for row in rows]
