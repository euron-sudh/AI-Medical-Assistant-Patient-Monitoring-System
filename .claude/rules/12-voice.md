# Voice Channel Rules for MedAssist AI

## Architecture

```
Patient/Doctor Audio
       |
       v
  WebSocket Connection
       |
       v
  OpenAI Whisper API (STT)
       |
       v
  Text Transcript
       |
       v
  AI Agent Processing
       |
       v
  Response Text
       |
       v
  OpenAI TTS API (Synthesis)
       |
       v
  Audio Response
```

**CRITICAL: Never stream raw audio directly to the LLM. Always convert to text first via Whisper.**

## Speech-to-Text (STT)

- **Engine**: OpenAI Whisper API
- **Multi-language support**: 50+ languages via Whisper's multilingual model
- **Minimum audio quality**: 16kHz sample rate
- **Supported formats**: webm, mp3, wav, m4a, ogg
- **Max audio length per chunk**: 25MB (Whisper API limit)
- Real-time transcription via chunked streaming over WebSocket
- Always include `language` hint when known to improve accuracy
- Medical vocabulary: use prompt parameter to bias toward medical terminology

## Text-to-Speech (TTS)

- **Engine**: OpenAI TTS API
- **Voices**:
  - `alloy` -- default for patient interactions (neutral, clear)
  - `nova` -- alternative for patient interactions (warm, conversational)
- **Model**: `tts-1` for real-time, `tts-1-hd` for recorded content
- **Output format**: opus for streaming, mp3 for recordings
- **Speed**: 1.0x default, configurable per user preference (0.75x - 1.25x)

## Voice Session Flow

1. Client opens WebSocket connection to `/ws/voice/{session_id}`
2. Server authenticates and verifies consent
3. Client streams audio chunks (binary WebSocket frames)
4. Server sends chunks to Whisper API for transcription
5. Transcribed text is processed by the AI agent
6. Agent response text is sent to TTS API
7. Audio response streamed back to client (binary frames)
8. Session transcript saved to database

## Recording Consent (HIPAA)

- **Recording consent is REQUIRED before any voice session begins.**
- Present consent prompt at session start: "This session may be recorded for quality and medical documentation purposes. Do you consent?"
- Store consent record: `voice_consent` table with `patient_id`, `session_id`, `consented_at`, `consent_type`
- If consent is declined, proceed without recording but still allow real-time interaction.
- All recordings stored encrypted in S3 with restricted access.
- Retention per HIPAA: minimum 6 years.

## Use Cases

### Patient Voice Symptom Reporting

- Patient describes symptoms via voice
- Whisper transcribes in real time
- Symptom checker agent processes transcript
- Follow-up questions asked via TTS
- Final symptom summary generated as text record

### Doctor Ambient Clinical Notes

- Doctor enables ambient mode during patient consultation
- Continuous audio capture and transcription
- Post-consultation: AI generates SOAP notes from transcript
- Doctor reviews and approves notes before saving to patient record
- Ambient mode must show clear visual indicator that recording is active

## WebSocket Protocol

```json
// Client -> Server: Start session
{"type": "voice.start", "session_id": "uuid", "language": "en", "consent": true}

// Client -> Server: Audio chunk (binary frame follows)
{"type": "voice.audio_chunk", "sequence": 1}

// Server -> Client: Partial transcript
{"type": "voice.transcript", "text": "I have a headache...", "is_final": false}

// Server -> Client: Agent response audio (binary frame follows)
{"type": "voice.response_audio", "text": "Can you describe the headache..."}

// Client -> Server: End session
{"type": "voice.end"}
```

## Error Handling

- Network interruption: buffer audio locally, resume upload on reconnect
- Whisper API failure: retry once, then fall back to text input with apology
- TTS failure: deliver response as text instead of audio
- Poor audio quality: notify user to speak closer to microphone or improve environment
