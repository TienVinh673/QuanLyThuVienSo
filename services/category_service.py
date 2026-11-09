from errors import BusinessRuleError, NotFoundError, ValidationError
from interfaces.repository_interface import ICategoryRepository


class CategoryService:
    def __init__(self, category_repository: ICategoryRepository):
        self._categories = category_repository

    def list_categories(self):
        return self._categories.list_all()

    def get_category(self, category_id):
        category = self._categories.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Không tìm thấy danh mục.")
        return category

    def create_category(self, name, description=""):
        name = (name or "").strip()
        if len(name) < 2:
            raise ValidationError("Tên danh mục cần ít nhất 2 ký tự.")
        if self._categories.find_by_name(name):
            raise ValidationError("Danh mục này đã tồn tại.")
        return self._categories.create(name, (description or "").strip())

    def update_category(self, category_id, name, description=""):
        category = self.get_category(category_id)
        name = (name or "").strip()
        if len(name) < 2:
            raise ValidationError("Tên danh mục cần ít nhất 2 ký tự.")
        existing = self._categories.find_by_name(name)
        if existing and existing.id != category.id:
            raise ValidationError("Tên danh mục đã được sử dụng.")
        self._categories.update(category_id, name, (description or "").strip())

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        if category.book_count > 0:
            raise BusinessRuleError(
                f"Danh mục “{category.name}” còn {category.book_count} đầu sách, không thể xóa."
            )
        self._categories.delete(category_id)
