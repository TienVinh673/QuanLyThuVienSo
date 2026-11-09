-- ============================================================
-- Schema — chạy mỗi khi app khởi động (an toàn vì IF NOT EXISTS)
-- ============================================================
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    email         TEXT,
    role          TEXT NOT NULL CHECK (role IN ('admin', 'reader')),
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS books (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    author           TEXT NOT NULL,
    isbn             TEXT NOT NULL UNIQUE,
    category_id      INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    publisher        TEXT,
    publish_year     INTEGER,
    description      TEXT,
    file_path        TEXT,
    total_copies     INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    cover_color      TEXT NOT NULL DEFAULT '#145c4c',
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS borrow_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    book_id      INTEGER NOT NULL REFERENCES books(id),
    request_date TEXT NOT NULL,
    borrow_date  TEXT,
    due_date     TEXT,
    return_date  TEXT,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'borrowed', 'returned', 'rejected', 'cancelled')),
    note         TEXT,
    processed_by INTEGER REFERENCES users(id),
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    message    TEXT NOT NULL,
    kind       TEXT NOT NULL DEFAULT 'system',
    is_read    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action     TEXT NOT NULL,
    detail     TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_borrow_user   ON borrow_records(user_id);
CREATE INDEX IF NOT EXISTS idx_borrow_book   ON borrow_records(book_id);
CREATE INDEX IF NOT EXISTS idx_borrow_status ON borrow_records(status);
CREATE INDEX IF NOT EXISTS idx_notify_user   ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_books_title   ON books(title);

-- ============================================================
-- Dữ liệu mẫu: chỉ nạp khi bảng users còn trống (rào chặn trong db_manager.py)
-- DATA --
-- ============================================================

INSERT INTO categories (name, description) VALUES
    ('Văn học', 'Tiểu thuyết, truyện ngắn và thơ'),
    ('Kỹ năng sống', 'Phát triển bản thân và tư duy'),
    ('Công nghệ', 'Lập trình, khoa học máy tính'),
    ('Kinh tế', 'Kinh tế học, quản trị và tài chính'),
    ('Thiếu nhi', 'Sách dành cho bạn đọc nhỏ tuổi');

INSERT INTO users (username, password_hash, full_name, email, role, is_active, created_at) VALUES
    ('admin', 'scrypt:32768:8:1$JwZrxaj4JgvO1ACE$6a75af1c2cb9ccd6acaa9402ade4bd1b8af4f1a2a282b159f87568c21415425219708f6d8084b02a01812b3f2b98ebb1cc56e6648e2acdd0e1d4f596e3b5038b',
     'Nguyễn Minh Anh', 'admin@thuvien.vn', 'admin', 1, '2026-10-04 09:00:00'),
    ('reader', 'scrypt:32768:8:1$URekpZcmEWfupGMQ$d0f702a211dd600a7394dba623ddd758b874f428b8c95f2a48ed799255480136b747530cedfe9ff255af480dabc951a1f5924d6246fc27e0c071d45fd6932a06',
     'Trần Gia Hân', 'giahan@example.com', 'reader', 1, '2026-10-04 09:05:00'),
    ('minhthu', 'scrypt:32768:8:1$7mHLaMyhEl7mA8s2$4f54cf0a04b683f8c1eb0a25931e6ba21eb1b79185fd5577673ee91bba9b197a0050910b2aec08995bb75a7f5e4a2b8a1ec5e149def121df8994dc2c709ec300',
     'Đặng Minh Thư', 'minhthu@example.com', 'reader', 1, '2026-10-04 09:10:00'),
    ('hoangnam', 'scrypt:32768:8:1$ec5o8MJqNz6soyMa$568e710a94c1236b5f1c8172ebd92bc3a5b2d74a2b0634f5cdb8c01ecd14682b3d7b74a5ef7bb68db4a63e54d8a7cc68663c01c61ee2a932b0723c6f33da81d6',
     'Lê Hoàng Nam', 'hoangnam@example.com', 'reader', 1, '2026-10-04 09:15:00');

INSERT INTO books
    (title, author, isbn, category_id, publisher, publish_year, description,
     file_path, total_copies, available_copies, cover_color, created_at)
VALUES
    ('Đắc Nhân Tâm', 'Dale Carnegie', '978-604-1-00001-1',
     (SELECT id FROM categories WHERE name = 'Kỹ năng sống'), 'NXB Tổng hợp TP.HCM', 2020,
     'Nghệ thuật ứng xử và xây dựng quan hệ giữa con người.',
     'books/dac-nhan-tam.txt', 4, 4, '#7a3b2e', '2026-10-05 09:00:00'),
    ('Nhà Giả Kim', 'Paulo Coelho', '978-604-1-00002-8',
     (SELECT id FROM categories WHERE name = 'Văn học'), 'NXB Hội Nhà Văn', 2019,
     'Hành trình theo đuổi vận mệnh của chàng chăn cừu Santiago.',
     'books/nha-gia-kim.pdf', 3, 2, '#8c6b2f', '2026-10-05 09:05:00'),
    ('Số Đỏ', 'Vũ Trọng Phụng', '978-604-1-00003-5',
     (SELECT id FROM categories WHERE name = 'Văn học'), 'NXB Văn học', 2018,
     'Tiểu thuyết trào phúng về xã hội Việt Nam nửa đầu thế kỷ XX.',
     'books/so-do.txt', 3, 3, '#8a4b5c', '2026-10-05 09:10:00'),
    ('Lập trình Python căn bản', 'Nguyễn Văn An', '978-604-1-00004-2',
     (SELECT id FROM categories WHERE name = 'Công nghệ'), 'NXB Bách Khoa', 2023,
     'Giáo trình nhập môn Python: cú pháp, hàm, lớp và cơ sở dữ liệu.',
     'books/lap-trinh-python.txt', 5, 5, '#145c4c', '2026-10-05 09:15:00'),
    ('Python nâng cao và Design Patterns', 'Trần Minh Bình', '978-604-1-00005-9',
     (SELECT id FROM categories WHERE name = 'Công nghệ'), 'NXB Khoa học', 2024,
     'Áp dụng các mẫu thiết kế phổ biến trong dự án Python thực tế.',
     'books/python-design-patterns.pdf', 2, 2, '#3f5d7d', '2026-10-05 09:20:00'),
    ('Tắt Đèn', 'Ngô Tất Tố', '978-604-1-00006-6',
     (SELECT id FROM categories WHERE name = 'Văn học'), 'NXB Văn học', 2017,
     'Bức tranh hiện thực về người nông dân trước Cách mạng tháng Tám.',
     'books/tat-den.txt', 3, 3, '#6b5b3e', '2026-10-05 09:25:00'),
    ('Kinh tế học vĩ mô', 'Paul Krugman', '978-604-1-00007-3',
     (SELECT id FROM categories WHERE name = 'Kinh tế'), 'NXB Kinh tế', 2022,
     'Giáo trình kinh tế vĩ mô với nhiều ví dụ thực tiễn.',
     '', 2, 2, '#414a6b', '2026-10-05 09:30:00'),
    ('Dế Mèn Phiêu Lưu Ký', 'Tô Hoài', '978-604-1-00008-0',
     (SELECT id FROM categories WHERE name = 'Thiếu nhi'), 'NXB Kim Đồng', 2020,
     'Cuộc phiêu lưu của Dế Mèn và những bài học về tình bạn.',
     'books/de-men-phieu-luu-ky.txt', 4, 4, '#2f5d62', '2026-10-05 09:35:00'),
    ('Tư Duy Nhanh Và Chậm', 'Daniel Kahneman', '978-604-1-00009-7',
     (SELECT id FROM categories WHERE name = 'Kỹ năng sống'), 'NXB Thế Giới', 2021,
     'Hai hệ thống tư duy chi phối cách con người ra quyết định.',
     'books/tu-duy-nhanh-va-cham.pdf', 2, 2, '#8c6b2f', '2026-10-05 09:40:00'),
    ('Clean Code', 'Robert C. Martin', '978-604-1-00010-3',
     (SELECT id FROM categories WHERE name = 'Công nghệ'), 'NXB Lao động', 2020,
     'Nguyên tắc viết mã nguồn sạch, dễ đọc và dễ bảo trì.',
     'books/clean-code.txt', 2, 2, '#145c4c', '2026-10-05 09:45:00');

-- Độc giả "reader" đang mượn Nhà Giả Kim -> minh họa Proxy được phép mở.
INSERT INTO borrow_records
    (user_id, book_id, request_date, borrow_date, due_date, return_date, status, note, processed_by, processed_at)
VALUES
    ((SELECT id FROM users WHERE username = 'reader'),
     (SELECT id FROM books WHERE title = 'Nhà Giả Kim'),
     '2026-10-28 09:15:00', '2026-10-29', '2026-11-09', NULL, 'borrowed', '',
     (SELECT id FROM users WHERE username = 'admin'), '2026-10-29 09:15:00');

-- Một yêu cầu đang chờ duyệt để Admin demo luồng duyệt.
INSERT INTO borrow_records
    (user_id, book_id, request_date, status, note)
VALUES
    ((SELECT id FROM users WHERE username = 'minhthu'),
     (SELECT id FROM books WHERE title = 'Số Đỏ'),
     '2026-11-03 08:15:00', 'pending', '');

-- Một phiếu đã trả để phần lịch sử có dữ liệu.
INSERT INTO borrow_records
    (user_id, book_id, request_date, borrow_date, due_date, return_date, status, note, processed_by, processed_at)
VALUES
    ((SELECT id FROM users WHERE username = 'reader'),
     (SELECT id FROM books WHERE title = 'Đắc Nhân Tâm'),
     '2026-10-08 09:15:00', '2026-10-09', '2026-10-20', '2026-10-15', 'returned', '',
     (SELECT id FROM users WHERE username = 'admin'), '2026-10-09 09:15:00');

INSERT INTO notifications (user_id, title, message, kind, is_read, created_at) VALUES
    ((SELECT id FROM users WHERE username = 'admin'), 'Yêu cầu mượn mới',
     'Đặng Minh Thư vừa gửi yêu cầu mượn “Số Đỏ”.', 'request', 0, '2026-11-03 08:15:00'),
    ((SELECT id FROM users WHERE username = 'reader'), 'Yêu cầu mượn được duyệt',
     '“Nhà Giả Kim” đã sẵn sàng. Hạn trả: 09/11/2026.', 'approved', 0, '2026-10-29 09:15:00'),
    ((SELECT id FROM users WHERE username = 'reader'), 'Chào mừng đến với Thư viện số',
     'Bạn có thể tìm sách, gửi yêu cầu mượn và đọc tài liệu điện tử.', 'system', 1, '2026-10-04 09:20:00'),
    ((SELECT id FROM users WHERE username = 'minhthu'), 'Đã gửi yêu cầu mượn',
     'Yêu cầu mượn “Số Đỏ” đang chờ thủ thư duyệt.', 'system', 1, '2026-11-03 08:15:00');

INSERT INTO audit_logs (user_id, action, detail, created_at) VALUES
    ((SELECT id FROM users WHERE username = 'reader'), 'Gửi yêu cầu mượn', '“Đắc Nhân Tâm”', '2026-10-08 09:15:00'),
    ((SELECT id FROM users WHERE username = 'admin'), 'Duyệt yêu cầu mượn', 'Trần Gia Hân — “Nhà Giả Kim”', '2026-10-29 09:15:00'),
    ((SELECT id FROM users WHERE username = 'reader'), 'Trả sách', 'Trần Gia Hân — “Đắc Nhân Tâm”', '2026-10-15 09:15:00'),
    ((SELECT id FROM users WHERE username = 'minhthu'), 'Gửi yêu cầu mượn', '“Số Đỏ”', '2026-11-03 08:15:00');
