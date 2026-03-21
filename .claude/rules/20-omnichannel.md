# Communication Channels for MedAssist AI

## Overview

MedAssist AI uses multiple communication channels to deliver notifications, alerts, and real-time data to patients and care providers. This is NOT a support ticket system. These channels serve clinical communication: vital alerts, appointment reminders, medication reminders, and care team messaging.

## Channels

### 1. WebSocket (Real-Time)

**Use cases:** Real-time vital monitoring, alert delivery, live chat, telemedicine signaling.

| Event Type           | Payload                                      | Recipients          |
| -------------------- | -------------------------------------------- | ------------------- |
| `vitals.update`      | Patient vitals data point from InfluxDB      | Assigned care team  |
| `alert.new`          | Monitoring alert (severity, vital, message)  | Nurse, then doctor  |
| `alert.acknowledged` | Alert acknowledgment confirmation             | Care team           |
| `chat.message`       | Chat message between patient and care team   | Sender, recipients  |
| `appointment.status` | Appointment status change                     | Patient, doctor     |
| `telemedicine.signal`| WebRTC signaling for Daily.co                | Session participants|

Implementation:
- Flask-SocketIO with Redis adapter for horizontal scaling.
- Namespace per interface: `/patient`, `/doctor`, `/admin`.
- Room per patient for targeted vital updates.
- JWT authentication on WebSocket handshake.
- Heartbeat interval: 25 seconds; timeout: 60 seconds.

### 2. SMS via Twilio

**Use cases:** Appointment reminders, medication reminders, critical alert notifications.

| Message Type           | Trigger                                    | Timing              |
| ---------------------- | ------------------------------------------ | -------------------- |
| Appointment reminder   | Scheduled appointment approaching           | 24h and 1h before   |
| Medication reminder    | Medication schedule time                    | At scheduled time    |
| Critical alert         | Emergency/critical vital alert unacknowledged| After 2 min timeout |
| Appointment confirmation | New appointment booked                    | Immediately          |
| Telemedicine link      | Telemedicine session starting               | 15 min before        |

Implementation:
- Twilio REST API via `twilio` Python SDK.
- Celery task for async SMS delivery.
- Webhook endpoint: `POST /api/v1/webhooks/twilio/status` for delivery status callbacks.
- Phone numbers stored encrypted in `users` table.
- Opt-in required; respect `notification_preferences.sms_enabled`.

### 3. Email via SendGrid

**Use cases:** Report delivery, appointment confirmations, account notifications, weekly health summaries.

| Email Type                | Trigger                              | Template             |
| ------------------------- | ------------------------------------ | -------------------- |
| Report ready              | AI report generation complete         | `report_ready`       |
| Appointment confirmation  | Appointment booked/changed/cancelled  | `appointment_update` |
| Weekly health summary     | Scheduled (every Monday 8 AM)         | `weekly_summary`     |
| Account activation        | New user registration                 | `welcome`            |
| Password reset            | Password reset request                | `password_reset`     |
| Care plan update          | Doctor updates care plan              | `care_plan_update`   |

Implementation:
- SendGrid v3 API via `sendgrid` Python SDK.
- HTML email templates in `backend/templates/email/`.
- Celery task for async email delivery.
- Webhook endpoint: `POST /api/v1/webhooks/sendgrid/events` for delivery/open/click tracking.
- Unsubscribe link in every email (CAN-SPAM compliance).
- No PHI in email subject lines.

### 4. Push Notifications (Web Push API)

**Use cases:** Browser notifications for alerts, messages, appointment reminders when the app is in background.

| Notification Type     | Priority | Trigger                                |
| --------------------- | -------- | -------------------------------------- |
| Critical vital alert  | High     | Vital threshold breach                  |
| New chat message      | Normal   | Incoming message from care team/patient |
| Appointment reminder  | Normal   | Upcoming appointment (15 min before)    |
| Report available      | Low      | AI report generation complete           |
| Medication reminder   | Normal   | Medication schedule time                |

Implementation:
- Web Push API with VAPID keys.
- Service worker in Next.js frontend for background notification handling.
- Push subscription stored in `push_subscriptions` table.
- Celery task for sending push payloads.
- Fallback to SMS if push delivery fails for critical alerts.

## Notification Preferences

Each user has notification preferences stored in the `notification_preferences` table:

```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    websocket_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    critical_override BOOLEAN DEFAULT true,  -- bypass quiet hours for emergencies
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Rules:
- Users can enable/disable each channel independently.
- Quiet hours suppress non-critical notifications.
- `critical_override = true` means emergency/critical alerts always deliver regardless of quiet hours.
- Default preferences are created on user registration.
- Preferences are editable via the profile settings page.

## Channel-Specific Adapters

Each channel is implemented as an adapter conforming to a common interface:

```python
from abc import ABC, abstractmethod

class NotificationAdapter(ABC):
    @abstractmethod
    async def send(self, recipient_id: str, message: dict) -> bool:
        """Send notification. Returns True on success."""
        pass

    @abstractmethod
    async def check_delivery_status(self, message_id: str) -> str:
        """Check delivery status of a sent notification."""
        pass

class TwilioAdapter(NotificationAdapter): ...
class SendGridAdapter(NotificationAdapter): ...
class WebPushAdapter(NotificationAdapter): ...
class WebSocketAdapter(NotificationAdapter): ...
```

- All adapters are registered in a `NotificationService` that routes messages based on user preferences and channel availability.
- Adapter selection priority for critical alerts: WebSocket > Push > SMS > Email.
- All sent notifications are logged in the `notifications` table.

## Notifications Table

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    channel VARCHAR(20) NOT NULL,  -- 'websocket', 'sms', 'email', 'push'
    type VARCHAR(50) NOT NULL,     -- 'alert', 'reminder', 'message', 'report'
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'sent', 'delivered', 'failed', 'read'
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Webhook Handlers

### Twilio Status Callback

```
POST /api/v1/webhooks/twilio/status
```
- Validates Twilio request signature.
- Updates `notifications.status` based on `MessageStatus` (sent, delivered, failed, undelivered).
- Triggers fallback channel on delivery failure for critical messages.

### SendGrid Event Webhook

```
POST /api/v1/webhooks/sendgrid/events
```
- Validates SendGrid webhook signature.
- Processes events: delivered, opened, clicked, bounced, dropped, spam_report.
- Updates `notifications.status` accordingly.
- Disables email for users who mark as spam.

### Daily.co Webhook

```
POST /api/v1/webhooks/dailyco/events
```
- Handles: `meeting.started`, `meeting.ended`, `participant.joined`, `participant.left`.
- Updates telemedicine session records.
- Triggers post-session actions (summary generation, follow-up scheduling).

## Rules

- Never send PHI (Protected Health Information) via SMS or email body. Use generic messages with links to the secure portal.
- SMS example: "You have a new health report available. Log in to MedAssist AI to view it."
- All notification content must be reviewed for PHI leakage before sending.
- Rate limit notifications: max 10 SMS/day per user, max 20 emails/day per user.
- Failed deliveries trigger retry (max 3 attempts with exponential backoff).
- All notification sends are audit logged with channel, recipient, timestamp, and delivery status.
