from flask import Blueprint, g, render_template, send_file

from security import login_required
from views import get_facade

book_bp = Blueprint("book", __name__)

MIME_TYPES = {"pdf": "application/pdf", "txt": "text/plain; charset=utf-8"}


@book_bp.route("/books/<int:book_id>")
@login_required
def detail(book_id):
    detail_data = get_facade().book_detail(g.user, book_id)
    return render_template("reader/book_detail.html", **detail_data)


@book_bp.route("/documents/<int:book_id>")
@login_required
def document(book_id):
    view = get_facade().document_view(g.user, book_id)
    return render_template("reader/document.html", **view)


@book_bp.route("/documents/<int:book_id>/file")
@login_required
def document_file(book_id):
    path = get_facade().document_file(g.user, book_id)
    extension = path.suffix.lstrip(".").lower()
    return send_file(
        path,
        mimetype=MIME_TYPES.get(extension, "application/octet-stream"),
        as_attachment=False,
        download_name=path.name,
    )
