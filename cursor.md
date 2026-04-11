# Cursor Task: Improve Realtime Voice Conversation Quality in Med Assist App
## Context
I have a Med Assist app using `gpt-4o-realtime-preview` for two-way voice conversation.
Current problems:
1. The assistant replies too early and does not properly wait for the user to finish.
2. The voice sounds robotic instead of natural.
3. Interruptions do not feel human and smooth.

The goal is to make the voice assistant feel more like a real human conversation with better pause handling, natural timing, and smoother audio output.

---
### 1. Assistant replies too early
The current turn detection is likely too aggressive. OpenAI’s realtime docs describe `server_vad` as the default voice activity detection mode, and they also document `semantic_vad`, which is designed to wait based on conversational meaning rather than only silence timing.
## 2. Robotic voice quality
Current setup is likely optimized more for responsiveness than for natural delivery. Current guidance also points to `gpt-realtime` as the better production choice, while `gpt-4o-realtime-preview` is more of a preview/development model.
### 3. Poor interruption behavior
The app likely does not stop assistant playback fast enough when the user starts speaking. The realtime docs expose speech start and stop events, and interruption handling patterns cancel the current response and stop playback as soon as the user cuts in.

---

## Required Changes

### A. Improve turn-taking
Switch turn detection from `server_vad` to `semantic_vad`. OpenAI’s docs say `semantic_vad` is less likely to interrupt the user before they are done speaking.

Use a calmer configuration:
- `turn_detection.type = "semantic_vad"` 
- `turn_detection.eagerness = "low"` or `"medium"` 
- `turn_detection.create_response = true` 
- `turn_detection.interrupt_response = true` 

Important rule:
Use only one response trigger strategy.
- Either let turn detection auto-create responses with `create_response: true`, or
- Manually create a response only after speech-stop events,
- But do not do both together. 

If we must stay on `server_vad`, increase `silence_duration_ms` so the assistant waits longer before assuming the user is done. Shorter silence values make it answer too quickly.

---

### B. Improve voice naturalness
Replace `gpt-4o-realtime-preview` with `gpt-realtime` for production-quality voice behavior. Current docs describe `gpt-realtime` as the preferred production model. 

Test these voice options:
- `alloy`
- `echo`
- `shimmer`
- `marin`
- `cedar` 

Add stronger speaking instructions in the session prompt:
- Speak naturally.
- Use short, clear sentences.
- Pause briefly before important medical advice.
- Do not answer until the user is clearly finished.
- Ask one question at a time.
- Avoid sounding overly formal or robotic.

Prompting guidance for realtime voice recommends short and explicit instruction style for pacing, tone, and response behavior

### C. Improve transport and latency
If the app is browser-based or mobile-client based, prefer WebRTC over WebSocket for realtime audio. Microsoft’s realtime guidance recommends WebRTC for low-latency client-side speech scenarios and positions it as the lower-latency option. 

Keep audio format clean and stable:
- Use `audio/pcm`
- Use 24000 Hz sample rate for input and output where possible 

Avoid extra transcoding and avoid aggressive gating or poor echo handling, because those can make turn detection think speech has ended when it has not. 

---

### D. Fix interruptions properly
On user speech start, the assistant must immediately stop speaking. Realtime VAD events include `input_audio_buffer.speech_started` and `input_audio_buffer.speech_stopped`, and interruption examples show canceling the current response when the user cuts in. 

Implementation behavior:
- On `speech_started`: stop playback immediately and cancel the current response.
- On `speech_stopped`: let auto-response happen if enabled, otherwise manually create a response only once. 
- Keep `interrupt_response = true` so the assistant yields when the user starts speaking. 

---

## Recommended Target Configuration

Use this as the new baseline:
- Model: `gpt-realtime`
- Turn detection: `semantic_vad` 
- Eagerness: `low` 
- Auto response: enabled with `create_response: true` 
- Interruption: enabled with `interrupt_response: true` 
- Transport: WebRTC for browser/mobile 
- Audio: PCM 24 kHz 
- Voice candidates to test first: `marin`, `cedar`, `alloy` 

---

## Cursor Implementation Tasks

1. Audit the current realtime session configuration.
2. Check whether turn detection is using `server_vad` or `semantic_vad`.
3. Remove duplicate response triggering if both auto-response and manual-response logic exist.
4. Add proper handling for `speech_started` and `speech_stopped`.
5. Stop TTS playback instantly when the user begins speaking.
6. Add response cancel logic when interruption happens.
7. Migrate from `gpt-4o-realtime-preview` to `gpt-realtime`.
8. Add a configurable voice selector for testing multiple voices.
9. Update the session/system prompt for natural pacing and human-like delivery.
10. Verify whether transport is WebRTC or WebSocket and migrate to WebRTC if this is a browser/mobile client.
11. Confirm audio pipeline stays PCM 24 kHz end-to-end if possible.
12. Review microphone input processing for over-aggressive silence detection, gating, or echo issues.

---

## Acceptance Criteria

The app should behave like this:
- The assistant does not answer while the user is still speaking. 
- Small pauses in the user’s speech do not trigger premature replies. 
- The assistant stops talking immediately when the user interrupts. 
- Voice output sounds smoother and less robotic after switching model/voice/prompting. 
- Only one response is created per completed user turn. 
- End-to-end latency feels conversational rather than laggy, especially when using WebRTC. 

---

## Notes For Cursor

Prioritize correctness in conversation flow over raw speed.
A slightly slower but well-timed response is better than a fast interruption-heavy experience.
The main focus is:
1. natural end-of-turn detection,
2. immediate interruption handling,
3. better model + voice selection,
4. lower-latency audio transport,
5. stronger session prompting for human-like speech. 

# Cursor Task: Reduce Background Noise Handling Issues in Med Assist Realtime Voice App

## Context

The Med Assist app uses OpenAI Realtime voice conversation.
Current problem:
- While the user is talking, the system is also picking up background noise.
- That noise is affecting turn detection and overall conversation quality.
- The app should focus on the user’s speech and reduce false activation from room sounds, fan noise, keyboard noise, TV, other people talking, and echo.

Goal:
Design and update the app so that background noise is reduced before audio reaches turn detection and before it is sent to the model.

***

## Problem To Solve

The app is currently treating non-speech noise as useful input.
That can cause:
- false speech detection,
- premature responses,
- interruptions,
- reduced transcription quality,
- poor realtime conversation flow.

We need a layered solution, not a single fix.

***

## Required Solution Design

### 1. Add input noise reduction in the OpenAI Realtime session
Configure OpenAI Realtime input noise reduction so noise is filtered before VAD and before the model processes the audio.

Use one of these modes depending on the device:
- `near_field` for headset, earphones, phone-near-mouth, or close microphone use
- `far_field` for laptop mic, room mic, speakerphone, or when the user is farther from the microphone

Initial default for Med Assist:
- Prefer `near_field` for mobile/headset experiences
- Use `far_field` only when the app is operating in open-room/laptop mode

Example target config:

```json
{
  "type": "session.update",
  "session": {
    "audio": {
      "input": {
        "noise_reduction": {
          "type": "near_field"
        },
        "turn_detection": {
          "type": "server_vad",
          "threshold": 0.65,
          "prefix_padding_ms": 300,
          "silence_duration_ms": 700,
          "create_response": true,
          "interrupt_response": true
        }
      }
    }
  }
}
```

***

### 2. Improve browser microphone capture settings
If this app runs in the browser, request microphone access with built-in audio cleanup enabled.

Use:
- `noiseSuppression: true`
- `echoCancellation: true`
- `autoGainControl: true`

Example:

```js
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    noiseSuppression: true,
    echoCancellation: true,
    autoGainControl: true
  },
  video: false
});
```

This should happen before the audio stream is connected to the Realtime session.

***

### 3. Tune VAD so background noise does not trigger speech detection easily
The current turn detection is likely too sensitive.
Tune these values carefully:

- Increase `threshold` so only stronger speech is treated as voice
- Increase `silence_duration_ms` so tiny sound gaps or noise bursts do not end speech early
- Keep `prefix_padding_ms` so initial user speech is not clipped

Starting recommendation:
- `threshold`: try `0.6` to `0.7`
- `silence_duration_ms`: try `600` to `900`
- `prefix_padding_ms`: around `300`

Rules:
- If the app reacts to fan noise or room noise, raise `threshold`
- If the assistant replies too quickly after tiny pauses, increase `silence_duration_ms`
- If user speech beginnings are clipped, increase `prefix_padding_ms`

***

### 4. Support different listening modes
Create app-level listening profiles instead of using one fixed audio mode for every environment.

Add at least these modes:

#### A. Quiet mode
Use when the user is in a calm room.
- Noise reduction: `near_field`
- Normal VAD threshold
- Faster turn response

#### B. Noisy environment mode
Use in hospital, clinic, street, waiting area, home with TV/fan, or shared room.
- Stronger noise filtering
- Higher VAD threshold
- Longer silence duration
- Slightly slower response is acceptable if accuracy improves

#### C. Speaker/laptop mode
Use when the user is not close to the mic.
- Noise reduction: `far_field`
- More conservative VAD tuning
- Better echo handling

These modes should be configurable in code and optionally selectable in UI.

***

### 5. Handle interruptions correctly when noise appears
Do not treat every detected sound as a real interruption.
Only stop assistant playback when the detected input is likely human speech.

Implementation goal:
- Differentiate likely speech from brief noise bursts
- Avoid canceling assistant output due to clicks, keyboard taps, or static
- Only interrupt response when speech confidence is meaningful

If needed, add a short debounce/window before treating a new signal as a true interruption.

***

### 6. Improve UI/UX for noisy environments
Design the interface so the user understands how to get better voice performance.

Add:
- A visible “Listening” state
- A visible “Background noise detected” warning when audio environment is poor
- A suggestion like “Move closer to the microphone” or “Use earphones for better accuracy”
- Optional mic input meter to show when noise floor is too high
- Optional environment selector: Quiet / Noisy / Speaker mode

The product should guide the user, not silently fail.

***

### 7. Prefer close-mic usage in Med Assist workflows
For a medical assistant experience, optimize for speech clarity.

Product guidance:
- Prefer headset or earphones when possible
- Prefer phone-near-mouth or close mic positioning
- Avoid open-speaker/laptop mode unless necessary
- Show onboarding hints for better audio quality on first use

***

### 8. Add diagnostics for what the system actually heard
Add logging/inspection tools so we can debug whether the app is reacting to speech or noise.

Need:
- Log VAD-related events
- Log when speech starts/stops
- Log when interruptions are triggered
- Log active noise reduction mode
- Log active listening profile
- Add a dev/debug panel for audio state if possible

This will help identify whether false triggers are caused by mic capture, VAD sensitivity, or app logic.

***

## Recommended Baseline Configuration

Use this as the first implementation target:

### Browser audio capture
```js
{
  noiseSuppression: true,
  echoCancellation: true,
  autoGainControl: true
}
```

### Realtime input audio
```json
{
  "noise_reduction": { "type": "near_field" },
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.65,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 700,
    "create_response": true,
    "interrupt_response": true
  }
}
```

### If false activations continue
- Raise `threshold` gradually
- Increase `silence_duration_ms`
- Test `far_field` for laptop/open-room scenarios
- Add environment profiles and UI guidance

***

## Cursor Implementation Tasks

1. Inspect the current microphone capture logic.
2. Ensure browser audio constraints enable noise suppression, echo cancellation, and auto gain control.
3. Inspect the current OpenAI Realtime session config.
4. Add `input` noise reduction using `near_field` by default.
5. Add support for switching between `near_field` and `far_field`.
6. Tune `server_vad` values for noisy environments.
7. Add configurable listening profiles: Quiet, Noisy, Speaker.
8. Prevent brief background sounds from acting like full user interruptions.
9. Add UI indicators for listening state and noisy environment detection.
10. Add user guidance for better mic usage.
11. Add logs/debug tools for speech start, speech stop, interruptions, and current listening profile.
12. Test with these background noise cases:
   - fan noise
   - keyboard typing
   - TV in background
   - another person speaking nearby
   - street/traffic noise
   - laptop speaker echo

***

## Acceptance Criteria

The updated app should behave like this:
- Background noise should not easily trigger speech detection.
- The assistant should focus more on actual user speech.
- Fan noise, keyboard noise, and room hum should not cause frequent false starts.
- Tiny bursts of non-speech sound should not immediately interrupt the assistant.
- Close-mic usage should perform noticeably better than before.
- The app should expose listening mode and audio-state behavior clearly enough for debugging.
- The user should get guidance when the environment is too noisy.

***

## Notes For Cursor

Prioritize speech reliability over ultra-fast response timing in noisy environments.
It is acceptable to make the assistant slightly more conservative if that reduces false triggers.
This should be implemented as a layered system:
1. browser-level cleanup,
2. OpenAI input noise reduction,
3. tuned VAD,
4. environment-specific listening modes,
5. UI guidance,
6. diagnostics and logging.