from functools import wraps

from flask import flash, g, redirect, request, url_for

from errors import PermissionDenied


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Vui lòng đăng nhập để tiếp tục.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Vui lòng đăng nhập để tiếp tục.", "error")
            return redirect(url_for("auth.login", next=request.path))
        if not g.user.is_admin:
            raise PermissionDenied("Chỉ thủ thư mới được truy cập khu vực quản trị.")
        return view(*args, **kwargs)

    return wrapped


def safe_next_url(value, fallback):
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return fallback
