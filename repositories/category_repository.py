from interfaces.repository_interface import ICategoryRepository
from models.category import Category


class CategoryRepository(ICategoryRepository):
    def __init__(self, db_manager):
        self._db = db_manager

    def list_all(self):
        with self._db.get_connection() as connection:
            rows = connection.execute(
                """SELECT c.*, COUNT(b.id) AS book_count
                   FROM categories c
                   LEFT JOIN books b ON b.category_id = c.id
                   GROUP BY c.id
                   ORDER BY c.name COLLATE NOCASE"""
            ).fetchall()
        return [Category.from_row(row) for row in rows]

    def get_by_id(self, category_id):
        with self._db.get_connection() as connection:
            row = connection.execute(
                """SELECT c.*, (SELECT COUNT(*) FROM books b WHERE b.category_id = c.id) AS book_count
                   FROM categories c WHERE c.id = ?""",
                (category_id,),
            ).fetchone()
        return Category.from_row(row) if row else None

    def find_by_name(self, name):
        with self._db.get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM categories WHERE lower(name) = lower(?)", (name.strip(),)
            ).fetchone()
        return Category.from_row(row) if row else None

    def create(self, name, description=""):
        with self._db.get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?)", (name, description)
            )
            return cursor.lastrowid

    def update(self, category_id, name, description=""):
        with self._db.get_connection() as connection:
            connection.execute(
                "UPDATE categories SET name = ?, description = ? WHERE id = ?",
                (name, description, category_id),
            )

    def delete(self, category_id):
        with self._db.get_connection() as connection:
            connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))
