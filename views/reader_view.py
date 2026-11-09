from flask import Blueprint, g, redirect, render_template, request, url_for

from security import login_required
from views import get_facade

reader_bp = Blueprint("reader", __name__)


@reader_bp.route("/")
@login_required
def home():
    if g.user.is_admin:
        return redirect(url_for("admin.dashboard"))

    facade = get_facade()
    keyword = (request.args.get("q") or "").strip()
    criteria = request.args.get("by") or "all"
    category_id = request.args.get("category", type=int)
    categories = facade.list_categories()

    if keyword:
        result = facade.search_books(keyword, criteria)
        books = result["books"]
        if category_id:
            books = [book for book in books if book.category_id == category_id]
        context = {
            "books": books,
            "keyword": keyword,
            "criteria": criteria,
            "criteria_label": result["criteria_label"],
            "is_search": True,
        }
    else:
        books = facade.filter_books(category_id)
        context = {"books": books, "keyword": "", "criteria": "all", "is_search": False}

    all_books = facade.filter_books()
    context.update(
        {
            "categories": categories,
            "category_id": category_id,
            "dashboard": facade.reader_dashboard(g.user),
            "library_total": len(all_books),
            "available_total": sum(1 for book in all_books if book.is_available),
        }
    )
    return render_template("reader/home.html", **context)


@reader_bp.route("/me/loans")
@login_required
def loans():
    records = get_facade().list_user_loans(g.user.id)
    return render_template("reader/loans.html", records=records)


@reader_bp.route("/me/notifications")
@login_required
def notifications():
    items = get_facade().list_notifications(g.user.id)
    return render_template("reader/notifications.html", notifications=items)


@reader_bp.route("/me/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification(notification_id):
    get_facade().mark_notification_read(notification_id, g.user.id)
    return redirect(url_for("reader.notifications"))


@reader_bp.route("/me/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications():
    get_facade().mark_all_notifications_read(g.user.id)
    return redirect(url_for("reader.notifications"))
