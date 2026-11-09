import pytest

from errors import BusinessRuleError, PermissionDenied
from tests.conftest import find_book


def loan_for(facade, user_id, book_id):
    return next(
        record
        for record in facade.list_user_loans(user_id)
        if record.book_id == book_id and record.status in {"pending", "borrowed"}
    )


def test_reader_requests_and_admin_approves_then_returns(facade):
    reader = facade.get_user(2)
    admin = facade.get_user(1)
    book = find_book(facade, "Lập trình Python căn bản")
    available_before = book.available_copies

    record = facade.request_borrow(reader, book.id)
    assert record.status == "pending"
    assert any(
        "Trần Gia Hân" in n.message and book.title in n.message
        for n in facade.list_notifications(admin.id)
    ), "Observer phải gửi thông báo cho thủ thư khi có yêu cầu mới"

    approved = facade.approve_request(admin, record.id)
    assert approved.status == "borrowed"
    assert approved.borrow_date is not None
    assert approved.due_date is not None
    assert facade.get_book(book.id).available_copies == available_before - 1

    reader_messages = [n.message for n in facade.list_notifications(reader.id)]
    assert any("sẵn sàng" in message and book.title in message for message in reader_messages)

    returned = facade.return_book(reader, record.id)
    assert returned.status == "returned"
    assert returned.return_date is not None
    assert facade.get_book(book.id).available_copies == available_before


def test_duplicate_open_request_is_blocked(facade):
    reader = facade.get_user(2)
    book = find_book(facade, "Nhà Giả Kim")  # đã có phiếu borrowed trong seed

    with pytest.raises(BusinessRuleError):
        facade.request_borrow(reader, book.id)


def test_admin_cannot_request_books(facade):
    admin = facade.get_user(1)
    book = find_book(facade, "Clean Code")

    with pytest.raises(PermissionDenied):
        facade.request_borrow(admin, book.id)


def test_reader_cannot_return_someone_elses_loan(facade):
    reader = facade.get_user(2)
    minhthu = facade.get_user(3)
    record = loan_for(facade, reader.id, find_book(facade, "Nhà Giả Kim").id)

    with pytest.raises(PermissionDenied):
        facade.return_book(minhthu, record.id)


def test_only_pending_requests_can_be_approved(facade):
    admin = facade.get_user(1)
    reader = facade.get_user(2)
    record = loan_for(facade, reader.id, find_book(facade, "Nhà Giả Kim").id)

    with pytest.raises(BusinessRuleError):
        facade.approve_request(admin, record.id)  # phiếu đang borrowed


def test_rejection_notifies_reader(facade):
    admin = facade.get_user(1)
    reader = facade.get_user(3)
    pending = next(record for record in facade.list_requests("pending"))
    assert pending.user_id == reader.id

    rejected = facade.reject_request(admin, pending.id, "Sách đang được bảo trì")
    assert rejected.status == "rejected"
    assert any("bảo trì" in n.message for n in facade.list_notifications(reader.id))


def test_borrow_flow_over_http(reader_client, admin_client, facade):
    reader = facade.get_user(2)
    book = find_book(facade, "Tắt Đèn")

    response = reader_client.post(f"/books/{book.id}/borrow", follow_redirects=True)
    assert response.status_code == 200
    assert "Đã gửi yêu cầu mượn" in response.get_data(as_text=True)

    record = loan_for(facade, reader.id, book.id)
    response = admin_client.post(f"/admin/requests/{record.id}/approve", follow_redirects=True)
    assert "Đã duyệt yêu cầu mượn" in response.get_data(as_text=True)

    response = reader_client.get(f"/documents/{book.id}")
    assert response.status_code == 200
    assert "Tắt Đèn" in response.get_data(as_text=True)

    response = reader_client.post(f"/loans/{record.id}/return", follow_redirects=True)
    assert "Trả sách thành công" in response.get_data(as_text=True)
    assert reader_client.get(f"/documents/{book.id}").status_code == 403
