"""Unit tests for NotificationService."""

import uuid

import pytest

from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification_schema import CreateNotificationRequest
from app.services.notification_service import NotificationService


@pytest.fixture
def notification_service():
    """NotificationService instance."""
    return NotificationService()


@pytest.fixture
def user(db):
    """Create a user for notification tests."""
    user = User(
        email="notif-user@test.com",
        first_name="Notif",
        last_name="User",
        role="patient",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_user(db):
    """Create another user for authorization tests."""
    user = User(
        email="other-notif-user@test.com",
        first_name="Other",
        last_name="User",
        role="patient",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


class TestCreateNotification:
    """Tests for NotificationService.create_notification."""

    def test_create_notification_returns_response(self, db, notification_service, user):
        """Creating a notification returns a NotificationResponse."""
        data = CreateNotificationRequest(
            user_id=str(user.id),
            type="alert",
            title="Vitals Alert",
            message="Your heart rate is elevated.",
            channel="in_app",
        )

        result = notification_service.create_notification(data)

        assert result.title == "Vitals Alert"
        assert result.message == "Your heart rate is elevated."
        assert result.type == "alert"
        assert result.channel == "in_app"
        assert result.read is False
        assert result.read_at is None

    def test_create_notification_persists_to_database(self, db, notification_service, user):
        """Creating a notification persists it in the database."""
        data = CreateNotificationRequest(
            user_id=str(user.id),
            type="reminder",
            title="Appointment Reminder",
            message="You have an appointment tomorrow.",
        )

        result = notification_service.create_notification(data)

        persisted = db.session.get(Notification, uuid.UUID(result.id))
        assert persisted is not None
        assert persisted.title == "Appointment Reminder"
        assert persisted.user_id == user.id

    def test_create_notification_with_data_json(self, db, notification_service, user):
        """Notifications can store additional data as JSON."""
        data = CreateNotificationRequest(
            user_id=str(user.id),
            type="alert",
            title="Lab Results Ready",
            message="Your lab results are available.",
            data={"report_id": str(uuid.uuid4()), "priority": "high"},
        )

        result = notification_service.create_notification(data)
        assert result.data is not None
        assert result.data["priority"] == "high"

    def test_create_in_app_notification_sets_sent_at(self, db, notification_service, user):
        """In-app notifications have sent_at set automatically."""
        data = CreateNotificationRequest(
            user_id=str(user.id),
            type="info",
            title="Welcome",
            message="Welcome to MedAssist AI.",
            channel="in_app",
        )

        result = notification_service.create_notification(data)
        assert result.sent_at is not None


class TestGetUserNotifications:
    """Tests for NotificationService.get_user_notifications."""

    def test_returns_user_notifications(self, db, notification_service, user):
        """Returns notifications for the specified user."""
        for i in range(3):
            data = CreateNotificationRequest(
                user_id=str(user.id),
                type="alert",
                title=f"Alert {i}",
                message=f"Alert message {i}",
            )
            notification_service.create_notification(data)

        results = notification_service.get_user_notifications(user.id)
        assert len(results) == 3

    def test_returns_only_own_notifications(self, db, notification_service, user, other_user):
        """Users only see their own notifications."""
        notification_service.create_notification(CreateNotificationRequest(
            user_id=str(user.id), type="alert", title="Mine", message="My notif",
        ))
        notification_service.create_notification(CreateNotificationRequest(
            user_id=str(other_user.id), type="alert", title="Theirs", message="Their notif",
        ))

        results = notification_service.get_user_notifications(user.id)
        assert len(results) == 1
        assert results[0].title == "Mine"

    def test_returns_empty_list_when_no_notifications(self, db, notification_service, user):
        """Returns empty list when user has no notifications."""
        results = notification_service.get_user_notifications(user.id)
        assert results == []

    def test_unread_only_filter(self, db, notification_service, user):
        """Filtering by unread_only returns only unread notifications."""
        for i in range(2):
            notification_service.create_notification(CreateNotificationRequest(
                user_id=str(user.id), type="alert", title=f"Alert {i}", message=f"Msg {i}",
            ))

        all_notifs = notification_service.get_user_notifications(user.id)
        notification_service.mark_as_read(uuid.UUID(all_notifs[0].id), user.id)

        unread = notification_service.get_user_notifications(user.id, unread_only=True)
        assert len(unread) == 1

    def test_respects_limit(self, db, notification_service, user):
        """Only returns up to the specified limit."""
        for i in range(5):
            notification_service.create_notification(CreateNotificationRequest(
                user_id=str(user.id), type="alert", title=f"Alert {i}", message=f"Msg {i}",
            ))

        results = notification_service.get_user_notifications(user.id, limit=2)
        assert len(results) == 2

    def test_ordered_by_created_at_desc(self, db, notification_service, user):
        """Notifications are returned in reverse chronological order."""
        for i in range(3):
            notification_service.create_notification(CreateNotificationRequest(
                user_id=str(user.id), type="alert", title=f"Alert {i}", message=f"Msg {i}",
            ))

        results = notification_service.get_user_notifications(user.id)
        for i in range(len(results) - 1):
            assert results[i].created_at >= results[i + 1].created_at


class TestMarkAsRead:
    """Tests for NotificationService.mark_as_read."""

    def test_mark_as_read_updates_status(self, db, notification_service, user):
        """Marking a notification as read updates its read flag and timestamp."""
        data = CreateNotificationRequest(
            user_id=str(user.id), type="alert", title="Test", message="Test msg",
        )
        created = notification_service.create_notification(data)

        result = notification_service.mark_as_read(uuid.UUID(created.id), user.id)

        assert result is not None
        assert result.read is True
        assert result.read_at is not None

    def test_mark_as_read_returns_none_for_wrong_user(self, db, notification_service, user, other_user):
        """Cannot mark another user's notification as read."""
        data = CreateNotificationRequest(
            user_id=str(user.id), type="alert", title="Test", message="Test msg",
        )
        created = notification_service.create_notification(data)

        result = notification_service.mark_as_read(uuid.UUID(created.id), other_user.id)
        assert result is None

    def test_mark_as_read_returns_none_for_nonexistent(self, db, notification_service, user):
        """Returns None for a non-existent notification ID."""
        result = notification_service.mark_as_read(uuid.uuid4(), user.id)
        assert result is None


class TestMarkAllAsRead:
    """Tests for NotificationService.mark_all_as_read."""

    def test_marks_all_unread_notifications(self, db, notification_service, user):
        """Marks all unread notifications as read."""
        for i in range(3):
            notification_service.create_notification(CreateNotificationRequest(
                user_id=str(user.id), type="alert", title=f"Alert {i}", message=f"Msg {i}",
            ))

        count = notification_service.mark_all_as_read(user.id)
        assert count == 3

        unread = notification_service.get_user_notifications(user.id, unread_only=True)
        assert len(unread) == 0

    def test_returns_zero_when_no_unread(self, db, notification_service, user):
        """Returns 0 when there are no unread notifications."""
        count = notification_service.mark_all_as_read(user.id)
        assert count == 0

    def test_does_not_affect_other_users(self, db, notification_service, user, other_user):
        """Marking all as read does not affect other users' notifications."""
        notification_service.create_notification(CreateNotificationRequest(
            user_id=str(user.id), type="alert", title="Mine", message="My notif",
        ))
        notification_service.create_notification(CreateNotificationRequest(
            user_id=str(other_user.id), type="alert", title="Theirs", message="Their notif",
        ))

        notification_service.mark_all_as_read(user.id)

        other_unread = notification_service.get_user_notifications(other_user.id, unread_only=True)
        assert len(other_unread) == 1


class TestGetUnreadCount:
    """Tests for NotificationService.get_unread_count."""

    def test_returns_correct_unread_count(self, db, notification_service, user):
        """Returns the correct count of unread notifications."""
        for i in range(3):
            notification_service.create_notification(CreateNotificationRequest(
                user_id=str(user.id), type="alert", title=f"Alert {i}", message=f"Msg {i}",
            ))

        count = notification_service.get_unread_count(user.id)
        assert count == 3

    def test_returns_zero_when_all_read(self, db, notification_service, user):
        """Returns 0 when all notifications are read."""
        notification_service.create_notification(CreateNotificationRequest(
            user_id=str(user.id), type="alert", title="Test", message="Test msg",
        ))
        notification_service.mark_all_as_read(user.id)

        count = notification_service.get_unread_count(user.id)
        assert count == 0
