from interfaces.repository_interface import IBookRepository
from models.book import Book
from utils import now_str

BOOK_SELECT = """
    SELECT b.*, c.name AS category_name
    FROM books b
    LEFT JOIN categories c ON c.id = b.category_id
"""


class BookRepository(IBookRepository):
    def __init__(self, db_manager):
        self._db = db_manager

    def _fetch(self, connection, sql, params=()):
        rows = connection.execute(sql, params).fetchall()
        return [Book.from_row(row) for row in rows]

    def list_books(self, category_id=None, keyword=""):
        conditions = []
        params = []
        if category_id:
            conditions.append("b.category_id = ?")
            params.append(category_id)
        keyword = (keyword or "").strip()
        if keyword:
            conditions.append("(b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)")
            params.extend([f"%{keyword}%"] * 3)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self._db.get_connection() as connection:
            return self._fetch(connection, f"{BOOK_SELECT} {where} ORDER BY b.id DESC", params)

    def list_all(self):
        with self._db.get_connection() as connection:
            return self._fetch(connection, f"{BOOK_SELECT} ORDER BY b.id DESC")

    def get_by_id(self, book_id):
        with self._db.get_connection() as connection:
            row = connection.execute(f"{BOOK_SELECT} WHERE b.id = ?", (book_id,)).fetchone()
        return Book.from_row(row) if row else None

    def find_by_isbn(self, isbn):
        with self._db.get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM books WHERE replace(upper(isbn), '-', '') = replace(upper(?), '-', '')",
                (isbn,),
            ).fetchone()
        return Book.from_row(row) if row else None

    def create(self, data):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO books
                   (title, author, isbn, category_id, publisher, publish_year, description,
                    file_path, total_copies, available_copies, cover_color, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["title"], data["author"], data["isbn"], data["category_id"],
                    data["publisher"], data["publish_year"], data["description"],
                    data["file_path"], data["total_copies"], data["available_copies"],
                    data["cover_color"], now_str(),
                ),
            )
            return cursor.lastrowid

    def update(self, book_id, data):
        with self._db.get_connection() as connection:
            connection.execute(
                """UPDATE books
                   SET title = ?, author = ?, isbn = ?, category_id = ?, publisher = ?,
                       publish_year = ?, description = ?, file_path = ?,
                       total_copies = ?, available_copies = ?, cover_color = ?
                   WHERE id = ?""",
                (
                    data["title"], data["author"], data["isbn"], data["category_id"],
                    data["publisher"], data["publish_year"], data["description"],
                    data["file_path"], data["total_copies"], data["available_copies"],
                    data["cover_color"], book_id,
                ),
            )

    def delete(self, book_id):
        with self._db.get_connection() as connection:
            connection.execute("DELETE FROM books WHERE id = ?", (book_id,))

    def count_books(self):
        with self._db.get_connection() as connection:
            return connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    def count_copies(self):
        with self._db.get_connection() as connection:
            return connection.execute("SELECT COALESCE(SUM(total_copies), 0) FROM books").fetchone()[0]

    def recent(self, limit=6):
        with self._db.get_connection() as connection:
            return self._fetch(
                connection, f"{BOOK_SELECT} ORDER BY b.created_at DESC, b.id DESC LIMIT ?", (limit,)
            )

    def category_distribution(self):
        with self._db.get_connection() as connection:
            rows = connection.execute(
                """SELECT c.name, COUNT(b.id) AS total
                   FROM categories c
                   LEFT JOIN books b ON b.category_id = c.id
                   GROUP BY c.id
                   ORDER BY total DESC, c.name"""
            ).fetchall()
        return [{"name": row["name"], "total": row["total"]} for row in rows]
