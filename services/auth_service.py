import re

from werkzeug.security import check_password_hash, generate_password_hash

from errors import AuthError, NotFoundError, ValidationError
from interfaces.repository_interface import IAuditRepository, IUserRepository

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")


class AuthService:
    def __init__(self, user_repository: IUserRepository, audit_repository: IAuditRepository):
        self._users = user_repository
        self._audit = audit_repository

    def login(self, username, password):
        username = (username or "").strip()
        password = password or ""
        if not username or not password:
            raise AuthError("Vui lòng nhập tên đăng nhập và mật khẩu.")

        user = self._users.get_by_username(username)
        if user is None or not check_password_hash(user.password_hash, password):
            raise AuthError("Tên đăng nhập hoặc mật khẩu không đúng.")
        if not user.is_active:
            raise AuthError("Tài khoản này đã bị khóa. Vui lòng liên hệ thủ thư.")
        self._audit.log(user.id, "Đăng nhập", f"{user.role_label}: {user.username}")
        return user

    def register(self, full_name, username, password, confirm_password, email=""):
        full_name = (full_name or "").strip()
        username = (username or "").strip()
        email = (email or "").strip()

        if len(full_name) < 2:
            raise ValidationError("Họ tên cần ít nhất 2 ký tự.")
        if not USERNAME_PATTERN.match(username):
            raise ValidationError("Tên đăng nhập 3–30 ký tự, chỉ gồm chữ, số, dấu chấm hoặc gạch dưới.")
        if len(password or "") < 6:
            raise ValidationError("Mật khẩu cần ít nhất 6 ký tự.")
        if password != confirm_password:
            raise ValidationError("Mật khẩu nhập lại không khớp.")
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise ValidationError("Email không hợp lệ.")
        if self._users.get_by_username(username):
            raise ValidationError("Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.")

        user = self._users.create(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            email=email,
            role="reader",
        )
        self._audit.log(user.id, "Đăng ký tài khoản", f"Độc giả: {full_name}")
        return user

    def get_user(self, user_id):
        return self._users.get_by_id(user_id)

    def list_readers(self, keyword=""):
        return self._users.list_readers(keyword)

    def count_readers(self):
        return self._users.count_readers()

    def list_admins(self):
        return self._users.list_admins()

    def set_reader_active(self, user_id, is_active):
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Không tìm thấy độc giả.")
        if user.is_admin:
            raise ValidationError("Chỉ có thể khóa/mở khóa tài khoản độc giả.")
        self._users.set_active(user_id, is_active)
        return self._users.get_by_id(user_id)
