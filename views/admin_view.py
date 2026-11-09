from flask import Blueprint, flash, redirect, render_template, request, url_for

from errors import AppError
from security import admin_required
from views import get_facade

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_TABS = [
    ("pending", "Chờ duyệt"),
    ("borrowed", "Đang mượn"),
    ("returned", "Đã trả"),
    ("rejected", "Từ chối"),
]
COVER_COLORS = [
    "#145c4c", "#7a3b2e", "#3f5d7d", "#6b5b3e",
    "#8a4b5c", "#2f5d62", "#8c6b2f", "#414a6b",
]


@admin_bp.route("")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", **get_facade().admin_dashboard())


@admin_bp.route("/books")
@admin_required
def books():
    facade = get_facade()
    keyword = (request.args.get("q") or "").strip()
    category_id = request.args.get("category", type=int)
    return render_template(
        "admin/books.html",
        books=facade.filter_books(category_id, keyword),
        categories=facade.list_categories(),
        keyword=keyword,
        category_id=category_id,
    )


def _book_form_context(mode, book=None, form=None):
    facade = get_facade()
    if form is None:
        form = {}
        if book is not None:
            form = {
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "category_id": book.category_id or "",
                "publisher": book.publisher,
                "publish_year": book.publish_year or "",
                "description": book.description,
                "file_path": book.file_path,
                "total_copies": book.total_copies,
                "cover_color": book.cover_color,
            }
        else:
            form = {"total_copies": 1, "cover_color": COVER_COLORS[0]}
    return {
        "mode": mode,
        "book": book,
        "form": form,
        "categories": facade.list_categories(),
        "asset_files": facade.asset_files(),
        "cover_colors": COVER_COLORS,
    }


@admin_bp.route("/books/new", methods=["GET", "POST"])
@admin_required
def book_new():
    if request.method == "POST":
        try:
            book = get_facade().create_book(request.form.to_dict())
        except AppError as error:
            flash(error.message, "error")
            return render_template("admin/book_form.html", **_book_form_context("create", form=request.form))
        flash(f"Đã thêm sách “{book.title}”.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", **_book_form_context("create"))


@admin_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@admin_required
def book_edit(book_id):
    book = get_facade().get_book(book_id)
    if request.method == "POST":
        try:
            updated = get_facade().update_book(book_id, request.form.to_dict())
        except AppError as error:
            flash(error.message, "error")
            return render_template(
                "admin/book_form.html", **_book_form_context("edit", book=book, form=request.form)
            )
        flash(f"Đã cập nhật sách “{updated.title}”.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", **_book_form_context("edit", book=book))


@admin_bp.route("/books/<int:book_id>/delete", methods=["POST"])
@admin_required
def book_delete(book_id):
    book = get_facade().get_book(book_id)
    get_facade().delete_book(book_id)
    flash(f"Đã xóa sách “{book.title}”.", "success")
    return redirect(url_for("admin.books"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    facade = get_facade()
    edit_id = request.args.get("edit", type=int)
    editing = None
    if edit_id:
        editing = next((item for item in facade.list_categories() if item.id == edit_id), None)

    form = {"name": editing.name if editing else "", "description": editing.description if editing else ""}
    if request.method == "POST":
        form = {
            "name": (request.form.get("name") or "").strip(),
            "description": (request.form.get("description") or "").strip(),
        }
        try:
            facade.create_category(form["name"], form["description"])
        except AppError as error:
            flash(error.message, "error")
        else:
            flash(f"Đã thêm danh mục “{form['name']}”.", "success")
            return redirect(url_for("admin.categories"))

    return render_template(
        "admin/categories.html",
        categories=facade.list_categories(),
        editing=editing,
        form=form,
    )


@admin_bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@admin_required
def category_edit(category_id):
    try:
        get_facade().update_category(
            category_id,
            request.form.get("name") or "",
            request.form.get("description") or "",
        )
    except AppError as error:
        flash(error.message, "error")
        return redirect(url_for("admin.categories", edit=category_id))
    flash("Đã cập nhật danh mục.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def category_delete(category_id):
    get_facade().delete_category(category_id)
    flash("Đã xóa danh mục.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/readers")
@admin_required
def readers():
    keyword = (request.args.get("q") or "").strip()
    return render_template(
        "admin/readers.html",
        readers=get_facade().list_readers(keyword),
        keyword=keyword,
    )


@admin_bp.route("/readers/<int:user_id>/toggle", methods=["POST"])
@admin_required
def reader_toggle(user_id):
    reader = get_facade().get_user(user_id)
    updated = get_facade().set_reader_active(user_id, not reader.is_active)
    state = "mở khóa" if updated.is_active else "khóa"
    flash(f"Đã {state} tài khoản {updated.full_name}.", "success")
    return redirect(url_for("admin.readers"))


@admin_bp.route("/requests")
@admin_required
def requests_list():
    facade = get_facade()
    status = request.args.get("status") or "pending"
    if status == "all":
        records = facade.list_requests()
    elif status in dict(STATUS_TABS):
        records = facade.list_requests(status)
    else:
        status = "pending"
        records = facade.list_requests(status)
    return render_template(
        "admin/requests.html",
        records=records,
        status=status,
        tabs=STATUS_TABS,
        stats=facade.borrow_statistics(),
    )


@admin_bp.route("/loans")
@admin_required
def loans():
    facade = get_facade()
    records = facade.list_requests("borrowed")
    return render_template(
        "admin/loans.html",
        records=records,
        stats=facade.borrow_statistics(),
    )
