"""DatabaseManager — Singleton quản lý kết nối SQLite của toàn ứng dụng."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from patterns.creational.singleton import SingletonMeta

DATA_MARKER = "-- DATA --"


class DatabaseManager(metaclass=SingletonMeta):
    """Chỉ có một đối tượng cấu hình CSDL, nhưng mỗi thao tác mở kết nối riêng.

    Singleton không có nghĩa là giữ một kết nối dùng chung vĩnh viễn: kết nối
    được mở/đóng ngắn hạn qua context manager để tránh lỗi đa luồng.
    """

    def __init__(self):
        self._db_path = None

    @property
    def db_path(self):
        return self._db_path

    def configure(self, db_path):
        self._db_path = str(db_path)

    @contextmanager
    def get_connection(self):
        if not self._db_path:
            raise RuntimeError("DatabaseManager chưa được cấu hình đường dẫn CSDL.")

        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self, sql_path, with_demo=True):
        """Tạo bảng từ file .sql; chỉ nạp dữ liệu mẫu khi bảng users còn trống."""
        script = Path(sql_path).read_text(encoding="utf-8")
        schema, _, data = script.partition(DATA_MARKER)
        with self.get_connection() as connection:
            connection.executescript(schema)
            if with_demo and data.strip():
                user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                if user_count == 0:
                    connection.executescript(data)
