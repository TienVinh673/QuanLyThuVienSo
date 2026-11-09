from interfaces.repository_interface import INotificationRepository


class NotificationService:
    def __init__(self, notification_repository: INotificationRepository):
        self._notifications = notification_repository

    def notify(self, user_id, title, message, kind="system"):
        self._notifications.create(user_id, title, message, kind)

    def list_for_user(self, user_id):
        return self._notifications.list_by_user(user_id)

    def unread_count(self, user_id):
        return self._notifications.count_unread(user_id)

    def mark_read(self, notification_id, user_id):
        self._notifications.mark_read(notification_id, user_id)

    def mark_all_read(self, user_id):
        self._notifications.mark_all_read(user_id)
