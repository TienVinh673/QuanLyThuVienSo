import unicodedata
from datetime import date, datetime, timedelta

LOAN_DAYS = 14


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return date.today()


def today_str():
    return today().isoformat()


def loan_due_date(start=None, days=LOAN_DAYS):
    start = start or today()
    return (start + timedelta(days=days)).isoformat()


def format_date(value, fmt="%d/%m/%Y"):
    if not value:
        return "—"
    if isinstance(value, (date, datetime)):
        return value.strftime(fmt)
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value)[:19], pattern).strftime(fmt)
        except ValueError:
            continue
    return str(value)


def format_datetime(value):
    return format_date(value, "%H:%M · %d/%m/%Y")


def normalize_text(value):
    """Bỏ dấu tiếng Việt và chữ hoa để tìm kiếm thân thiện hơn."""
    if not value:
        return ""
    text = str(value).replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.lower().split())


def parse_year(value):
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1000 <= year <= 2100 else None


def human_size(num_bytes):
    if num_bytes is None:
        return "—"
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"
