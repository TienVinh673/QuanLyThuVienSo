from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from errors import AppError
from security import safe_next_url
from views import get_facade

login_bp = Blueprint("auth", __name__)


def home_for(user):
    if user.is_admin:
        return url_for("admin.dashboard")
    return url_for("reader.home")


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.get("user"):
        return redirect(home_for(g.user))

    username = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        try:
            user = get_facade().login(username, password)
        except AppError as error:
            flash(error.message, "error")
        else:
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            flash(f"Chào mừng {user.full_name} quay lại thư viện.", "success")
            return redirect(safe_next_url(request.args.get("next"), home_for(user)))

    return render_template("auth/login.html", username=username)


@login_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.get("user"):
        return redirect(home_for(g.user))

    form = {"full_name": "", "username": "", "email": ""}
    if request.method == "POST":
        form = {
            "full_name": (request.form.get("full_name") or "").strip(),
            "username": (request.form.get("username") or "").strip(),
            "email": (request.form.get("email") or "").strip(),
        }
        try:
            user = get_facade().register(
                full_name=form["full_name"],
                username=form["username"],
                password=request.form.get("password") or "",
                confirm_password=request.form.get("confirm_password") or "",
                email=form["email"],
            )
        except AppError as error:
            flash(error.message, "error")
        else:
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Tạo tài khoản thành công. Chúc bạn đọc sách vui vẻ!", "success")
            return redirect(url_for("reader.home"))

    return render_template("auth/register.html", form=form)


@login_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống.", "success")
    return redirect(url_for("auth.login"))
