from interfaces.repository_interface import IUserRepository
from models.user import User
from utils import now_str


class UserRepository(IUserRepository):
    def __init__(self, db_manager):
        self._db = db_manager

    def _row_to_user(self, row):
        return User.from_row(row) if row else None

    def get_by_username(self, username):
        with self._db.get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE lower(username) = lower(?)", (username,)
            ).fetchone()
        return self._row_to_user(row)

    def get_by_id(self, user_id):
        with self._db.get_connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row_to_user(row)

    def create(self, username, password_hash, full_name, email, role):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO users (username, password_hash, full_name, email, role, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (username, password_hash, full_name, email, role, now_str()),
            )
            user_id = cursor.lastrowid
        return self.get_by_id(user_id)

    def list_readers(self, keyword=""):
        like = f"%{keyword.strip()}%"
        with self._db.get_connection() as connection:
            rows = connection.execute(
                """SELECT u.*,
                          (SELECT COUNT(*) FROM borrow_records b
                           WHERE b.user_id = u.id AND b.status IN ('pending', 'borrowed')) AS open_loans
                   FROM users u
                   WHERE u.role = 'reader'
                     AND (? = '%%' OR u.username LIKE ? OR u.full_name LIKE ? OR u.email LIKE ?)
                   ORDER BY u.full_name COLLATE NOCASE""",
                (like, like, like, like),
            ).fetchall()
        return [User.from_row(row) for row in rows]

    def list_admins(self):
        with self._db.get_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM users WHERE role = 'admin' AND is_active = 1"
            ).fetchall()
        return [User.from_row(row) for row in rows]

    def count_readers(self):
        with self._db.get_connection() as connection:
            return connection.execute("SELECT COUNT(*) FROM users WHERE role = 'reader'").fetchone()[0]

    def set_active(self, user_id, is_active):
        with self._db.get_connection() as connection:
            connection.execute(
                "UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id)
            )
