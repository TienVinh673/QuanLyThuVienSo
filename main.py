import os
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

from database.db_manager import DatabaseManager
from errors import AppError
from patterns.behavioral.observer import AdminNotification, ReaderNotification
from patterns.structural.facade import LibraryFacade
from repositories.audit_repository import AuditRepository
from repositories.book_repository import BookRepository
from repositories.borrow_repository import BorrowRepository
from repositories.category_repository import CategoryRepository
from repositories.notification_repository import NotificationRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.book_service import BookService
from services.borrow_service import BorrowService
from services.category_service import CategoryService
from services.document_service import DocumentService
from services.notification_service import NotificationService
from utils import format_date, format_datetime

BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="digital-library-hk1-2026-2027",
        DATABASE=str(BASE_DIR / "database" / "library.db"),
        ASSETS_DIR=str(BASE_DIR / "assets"),
        SEED_DEMO=True,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(BASE_DIR / "database", exist_ok=True)

    database = DatabaseManager()
    database.configure(app.config["DATABASE"])
    database.initialize(
        BASE_DIR / "database" / "db_manager.sql",
        with_demo=app.config["SEED_DEMO"],
    )

    user_repository = UserRepository(database)
    book_repository = BookRepository(database)
    category_repository = CategoryRepository(database)
    borrow_repository = BorrowRepository(database)
    notification_repository = NotificationRepository(database)
    audit_repository = AuditRepository(database)

    notification_service = NotificationService(notification_repository)
    borrow_service = BorrowService(borrow_repository, book_repository, audit_repository)
    borrow_service.attach(AdminNotification(notification_service, user_repository))
    borrow_service.attach(ReaderNotification(notification_service))

    facade = LibraryFacade(
        auth_service=AuthService(user_repository, audit_repository),
        book_service=BookService(book_repository, category_repository, borrow_repository),
        category_service=CategoryService(category_repository),
        borrow_service=borrow_service,
        notification_service=notification_service,
        document_service=DocumentService(app.config["ASSETS_DIR"], borrow_repository),
    )
    app.extensions["facade"] = facade

    from views.admin_view import admin_bp
    from views.book_view import book_bp
    from views.borrow_view import borrow_bp
    from views.login_view import login_bp
    from views.reader_view import reader_bp

    app.register_blueprint(login_bp)
    app.register_blueprint(reader_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(admin_bp)

    app.jinja_env.filters["date"] = format_date
    app.jinja_env.filters["datetime"] = format_datetime

    @app.before_request
    def load_current_user():
        if request.endpoint == "static":
            return
        g.user = None
        user_id = session.get("user_id")
        if not user_id:
            return
        user = facade.get_user(user_id)
        if user is None or not user.is_active:
            session.clear()
            return
        g.user = user

    @app.context_processor
    def inject_globals():
        user = g.get("user")
        unread = facade.unread_count(user.id) if user else 0
        pending = facade.pending_request_count() if user and user.is_admin else 0
        return {
            "current_user": user,
            "unread_count": unread,
            "pending_count": pending,
            "search_options": facade.search_options(),
        }

    @app.errorhandler(AppError)
    def handle_app_error(error):
        if request.method == "POST":
            flash(error.message, "error")
            return redirect(request.referrer or url_for("auth.login"))
        return (
            render_template(
                "error.html",
                code=error.status_code,
                title="Không thể thực hiện",
                message=error.message,
            ),
            error.status_code,
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            render_template(
                "error.html",
                code=404,
                title="Không tìm thấy trang",
                message="Đường dẫn bạn truy cập không tồn tại.",
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(error):
        return (
            render_template(
                "error.html",
                code=500,
                title="Có lỗi xảy ra",
                message="Vui lòng thử lại sau ít phút.",
            ),
            500,
        )

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
