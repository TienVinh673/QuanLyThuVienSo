from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from security import admin_required, login_required
from views import get_facade

borrow_bp = Blueprint("borrow", __name__)


@borrow_bp.route("/books/<int:book_id>/borrow", methods=["POST"])
@login_required
def request_borrow(book_id):
    get_facade().request_borrow(g.user, book_id)
    flash("Đã gửi yêu cầu mượn sách. Thủ thư sẽ phản hồi trong thời gian sớm nhất.", "success")
    return redirect(url_for("book.detail", book_id=book_id))


@borrow_bp.route("/loans/<int:record_id>/return", methods=["POST"])
@login_required
def return_loan(record_id):
    get_facade().return_book(g.user, record_id)
    flash("Trả sách thành công. Cảm ơn bạn đã sử dụng thư viện.", "success")
    if g.user.is_admin:
        return redirect(url_for("admin.loans"))
    return redirect(url_for("reader.loans"))


@borrow_bp.route("/admin/requests/<int:record_id>/approve", methods=["POST"])
@admin_required
def approve(record_id):
    note = request.form.get("note") or ""
    get_facade().approve_request(g.user, record_id, note)
    flash("Đã duyệt yêu cầu mượn và gửi thông báo đến độc giả.", "success")
    return redirect(url_for("admin.requests_list"))


@borrow_bp.route("/admin/requests/<int:record_id>/reject", methods=["POST"])
@admin_required
def reject(record_id):
    note = request.form.get("note") or ""
    get_facade().reject_request(g.user, record_id, note)
    flash("Đã từ chối yêu cầu mượn và gửi thông báo đến độc giả.", "success")
    return redirect(url_for("admin.requests_list"))
