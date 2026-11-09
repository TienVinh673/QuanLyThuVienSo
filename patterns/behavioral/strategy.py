"""Strategy Pattern — mỗi tiêu chí tìm kiếm là một chiến lược riêng.

Muốn thêm tiêu chí mới (ví dụ tìm theo nhà xuất bản), chỉ cần thêm một lớp
SearchStrategy mới và đăng ký vào SEARCH_STRATEGIES, không sửa BookService.
"""

from abc import ABC, abstractmethod

from utils import normalize_text


class SearchStrategy(ABC):
    key = ""
    label = ""

    def search(self, books, keyword):
        normalized = normalize_text(keyword)
        if not normalized:
            return list(books)
        return [book for book in books if self.matches(book, normalized)]

    @abstractmethod
    def matches(self, book, keyword): ...


class SearchByTitle(SearchStrategy):
    key = "title"
    label = "Tên sách"

    def matches(self, book, keyword):
        return keyword in normalize_text(book.title)


class SearchByAuthor(SearchStrategy):
    key = "author"
    label = "Tác giả"

    def matches(self, book, keyword):
        return keyword in normalize_text(book.author)


class SearchByISBN(SearchStrategy):
    key = "isbn"
    label = "Mã ISBN"

    def matches(self, book, keyword):
        compact = keyword.replace(" ", "").replace("-", "")
        return compact in book.isbn.lower().replace("-", "").replace(" ", "")


class SearchByCategory(SearchStrategy):
    key = "category"
    label = "Thể loại"

    def matches(self, book, keyword):
        return keyword in normalize_text(book.category_name)


class SearchAllFields(SearchStrategy):
    key = "all"
    label = "Tất cả"

    def matches(self, book, keyword):
        haystack = " ".join(
            [book.title, book.author, book.isbn, book.category_name, book.publisher or ""]
        )
        return keyword in normalize_text(haystack)


SEARCH_STRATEGIES = {
    strategy.key: strategy
    for strategy in (
        SearchAllFields(),
        SearchByTitle(),
        SearchByAuthor(),
        SearchByISBN(),
        SearchByCategory(),
    )
}


class SearchContext:
    """Context giữ chiến lược hiện tại và ủy quyền việc tìm kiếm cho nó."""

    def __init__(self, book_repository):
        self._books = book_repository

    @staticmethod
    def options():
        return [{"key": key, "label": strategy.label} for key, strategy in SEARCH_STRATEGIES.items()]

    @staticmethod
    def strategy_for(criteria):
        return SEARCH_STRATEGIES.get(criteria, SEARCH_STRATEGIES["all"])

    def search(self, keyword, criteria="all"):
        strategy = self.strategy_for(criteria)
        return strategy.search(self._books.list_all(), keyword)
