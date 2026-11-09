from interfaces.repository_interface import INotificationRepository
from models.notification import Notification
from utils import now_str


class NotificationRepository(INotificationRepository):
    def __init__(self, db_manager):
        self._db = db_manager

    def create(self, user_id, title, message, kind="system"):
        with self._db.get_connection() as connection:
            connection.execute(
                """INSERT INTO notifications (user_id, title, message, kind, is_read, created_at)
                   VALUES (?, ?, ?, ?, 0, ?)""",
                (user_id, title, message, kind, now_str()),
            )

    def list_by_user(self, user_id):
        with self._db.get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM notifications WHERE user_id = ?
                   ORDER BY is_read ASC, created_at DESC, id DESC""",
                (user_id,),
            ).fetchall()
        return [Notification.from_row(row) for row in rows]

    def count_unread(self, user_id):
        with self._db.get_connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,)
            ).fetchone()[0]

    def mark_read(self, notification_id, user_id):
        with self._db.get_connection() as connection:
            connection.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, user_id),
            )

    def mark_all_read(self, user_id):
        with self._db.get_connection() as connection:
            connection.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,)
            )
