"""Singleton Pattern.

SingletonMeta đảm bảo mỗi lớp con chỉ có duy nhất một instance trong tiến trình.
Lớp áp dụng cụ thể là DatabaseManager (xem database/db_manager.py).
"""


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
