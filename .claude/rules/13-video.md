# Video Channel Rules for MedAssist AI

## Platform

- **WebRTC Provider**: Daily.co SDK
- **Frontend**: Daily.co React components (`@daily-co/daily-react`)
- **Backend**: Room management API via Daily.co REST API

## Features

| Feature | Description |
|---------|-------------|
| HD Video | Adaptive quality up to 1080p |
| Screen Sharing | For reviewing reports, lab results, imaging |
| AI Assistant Sidebar | In-call AI panel for real-time assistance |
| Real-time Transcription | Live caption overlay via Whisper integration |
| Waiting Room | Patients wait until provider joins |
| Post-call AI Notes | Automatic SOAP note generation from call transcript |
| Call Recording | With explicit consent, stored encrypted in S3 |
| Multi-participant | Patient + Doctor + Specialist + Interpreter |

## Multi-Participant Roles

| Role | Capabilities |
|------|-------------|
| **Patient** | Video/audio, chat, screen share (limited), view shared screens |
| **Doctor** | Video/audio, chat, screen share, AI sidebar, recording control, notes |
| **Specialist** | Video/audio, chat, screen share, AI sidebar (read-only notes) |
| **Interpreter** | Audio only (default), video optional, priority audio routing |

## Backend Room Management API

### Endpoints

```
POST   /api/v1/video/rooms              -- Create a new video room
GET    /api/v1/video/rooms/{room_id}     -- Get room details
DELETE /api/v1/video/rooms/{room_id}     -- End and delete room
POST   /api/v1/video/rooms/{room_id}/tokens  -- Generate participant token
GET    /api/v1/video/sessions            -- List telemedicine sessions
GET    /api/v1/video/sessions/{id}       -- Get session details with notes
```

### Room Creation

```json
{
  "appointment_id": "uuid",
  "scheduled_start": "2026-03-16T14:00:00Z",
  "max_participants": 4,
  "enable_recording": true,
  "enable_transcription": true,
  "waiting_room": true,
  "expiry_minutes": 90
}
```

### Token Generation

Each participant receives a scoped Daily.co meeting token:

```json
{
  "participant_id": "uuid",
  "role": "doctor",
  "room_name": "medassist-session-abc123",
  "permissions": {
    "can_record": true,
    "can_screen_share": true,
    "can_admin": true
  }
}
```

## Database Schema

### `telemedicine_sessions` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `appointment_id` | UUID | FK to appointments |
| `room_name` | VARCHAR | Daily.co room name |
| `status` | ENUM | waiting, in_progress, completed, cancelled |
| `started_at` | TIMESTAMP | Actual start time |
| `ended_at` | TIMESTAMP | Actual end time |
| `duration_seconds` | INTEGER | Computed duration |
| `recording_url` | TEXT | S3 URL (encrypted) |
| `transcript` | TEXT | Full session transcript |
| `ai_notes` | JSONB | AI-generated SOAP notes |
| `participant_count` | INTEGER | Number of participants |
| `created_at` | TIMESTAMP | Record creation |

## Frontend Integration

```jsx
import { DailyProvider, DailyVideo, DailyAudio } from '@daily-co/daily-react';

// Wrap telemedicine page in DailyProvider
// Use DailyVideo for participant video tiles
// Use custom hooks: useLocalParticipant, useParticipantIds, useScreenShare
// AI sidebar is a separate React component overlaid on the call UI
```

Key frontend requirements:
- Responsive layout: adapt tile arrangement for 1-4 participants
- AI sidebar collapsible and resizable
- Transcription overlay toggleable by user preference
- Network quality indicator visible at all times
- Pre-call device check (camera, microphone, speaker test)

## Quality Adaptation

- Monitor network conditions via Daily.co `network-quality-change` event
- Degrade gracefully:
  1. Reduce video resolution (1080p -> 720p -> 480p -> 360p)
  2. Reduce frame rate (30fps -> 15fps)
  3. Disable incoming video for low-bandwidth participants
  4. **Fallback to voice-only** if video is unsustainable
- Always prioritize audio quality over video quality
- Notify participants when quality is degraded

## Recording and Consent

- Recording requires explicit consent from ALL participants before starting.
- Consent prompt displayed in-call with accept/decline per participant.
- If any participant declines, recording is disabled for the session.
- Recordings stored in S3 with AES-256 encryption.
- Access restricted to authorized providers and the patient.
- Retention per HIPAA minimum 6 years.

## Post-Call Processing

1. Call ends and recording is finalized
2. Celery task triggered for post-processing:
   - Transcription finalized (if real-time was partial)
   - AI generates SOAP notes from full transcript
   - Notes saved to `telemedicine_sessions.ai_notes`
3. Doctor receives notification to review and approve AI notes
4. Approved notes attached to patient medical record
