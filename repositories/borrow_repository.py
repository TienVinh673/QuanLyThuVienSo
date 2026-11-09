from errors import BusinessRuleError
from interfaces.repository_interface import IBorrowRepository
from models.borrow import BorrowRecord
from utils import now_str, today_str

RECORD_SELECT = """
    SELECT br.*, b.title AS book_title, b.author AS book_author,
           b.cover_color AS book_cover_color,
           u.full_name AS reader_name, u.username AS reader_username
    FROM borrow_records br
    JOIN books b ON b.id = br.book_id
    JOIN users u ON u.id = br.user_id
"""


class BorrowRepository(IBorrowRepository):
    def __init__(self, db_manager):
        self._db = db_manager

    def _fetch(self, connection, sql, params=()):
        rows = connection.execute(sql, params).fetchall()
        return [BorrowRecord.from_row(row) for row in rows]

    def create_request(self, user_id, book_id):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO borrow_records (user_id, book_id, request_date, status)
                   VALUES (?, ?, ?, 'pending')""",
                (user_id, book_id, now_str()),
            )
            record_id = cursor.lastrowid
        return self.get_by_id(record_id)

    def get_by_id(self, record_id):
        with self._db.get_connection() as connection:
            row = connection.execute(f"{RECORD_SELECT} WHERE br.id = ?", (record_id,)).fetchone()
        return BorrowRecord.from_row(row) if row else None

    def find_open_record(self, user_id, book_id):
        with self._db.get_connection() as connection:
            row = connection.execute(
                f"""{RECORD_SELECT}
                    WHERE br.user_id = ? AND br.book_id = ? AND br.status IN ('pending', 'borrowed')
                    ORDER BY br.id DESC LIMIT 1""",
                (user_id, book_id),
            ).fetchone()
        return BorrowRecord.from_row(row) if row else None

    def find_active_loan(self, user_id, book_id):
        with self._db.get_connection() as connection:
            row = connection.execute(
                f"""{RECORD_SELECT}
                    WHERE br.user_id = ? AND br.book_id = ? AND br.status = 'borrowed'
                    ORDER BY br.id DESC LIMIT 1""",
                (user_id, book_id),
            ).fetchone()
        return BorrowRecord.from_row(row) if row else None

    def list_by_user(self, user_id):
        with self._db.get_connection() as connection:
            return self._fetch(
                connection,
                f"{RECORD_SELECT} WHERE br.user_id = ? ORDER BY br.request_date DESC, br.id DESC",
                (user_id,),
            )

    def list_records(self, status=None):
        sql = RECORD_SELECT
        params = ()
        if status:
            sql += " WHERE br.status = ?"
            params = (status,)
        sql += " ORDER BY br.request_date DESC, br.id DESC"
        with self._db.get_connection() as connection:
            return self._fetch(connection, sql, params)

    def approve(self, record_id, admin_id, borrow_date, due_date, note=""):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                """UPDATE borrow_records
                   SET status = 'borrowed', borrow_date = ?, due_date = ?, note = ?,
                       processed_by = ?, processed_at = ?
                   WHERE id = ? AND status = 'pending'""",
                (borrow_date, due_date, note, admin_id, now_str(), record_id),
            )
            if cursor.rowcount == 0:
                raise BusinessRuleError("Yêu cầu này không còn ở trạng thái chờ duyệt.")
            updated = connection.execute(
                """UPDATE books SET available_copies = available_copies - 1
                   WHERE id = (SELECT book_id FROM borrow_records WHERE id = ?)
                     AND available_copies > 0""",
                (record_id,),
            )
            if updated.rowcount == 0:
                raise BusinessRuleError("Sách đã hết bản sao, không thể duyệt yêu cầu này.")

    def reject(self, record_id, admin_id, note=""):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                """UPDATE borrow_records
                   SET status = 'rejected', note = ?, processed_by = ?, processed_at = ?
                   WHERE id = ? AND status = 'pending'""",
                (note, admin_id, now_str(), record_id),
            )
            if cursor.rowcount == 0:
                raise BusinessRuleError("Yêu cầu này không còn ở trạng thái chờ duyệt.")

    def mark_returned(self, record_id):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                """UPDATE borrow_records
                   SET status = 'returned', return_date = ?, processed_at = ?
                   WHERE id = ? AND status = 'borrowed'""",
                (now_str(), now_str(), record_id),
            )
            if cursor.rowcount == 0:
                raise BusinessRuleError("Phiếu mượn này không ở trạng thái đang mượn.")
            connection.execute(
                """UPDATE books SET available_copies = available_copies + 1
                   WHERE id = (SELECT book_id FROM borrow_records WHERE id = ?)""",
                (record_id,),
            )

    def count_by_status(self, status):
        with self._db.get_connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM borrow_records WHERE status = ?", (status,)
            ).fetchone()[0]

    def count_overdue(self):
        with self._db.get_connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM borrow_records WHERE status = 'borrowed' AND due_date < ?",
                (today_str(),),
            ).fetchone()[0]

    def count_open_for_book(self, book_id):
        with self._db.get_connection() as connection:
            return connection.execute(
                """SELECT COUNT(*) FROM borrow_records
                   WHERE book_id = ? AND status IN ('pending', 'borrowed')""",
                (book_id,),
            ).fetchone()[0]
