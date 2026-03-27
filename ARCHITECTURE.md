# Voice Assistant Architecture

Complete voice control system with two components: Pi (client) and mirapc (server).

## System Diagram

```
┌─────────────────┐                 ┌──────────────────┐
│  Raspberry Pi   │                 │     mirapc       │
│                 │                 │                  │
│ 1. Wake Word    │                 │                  │
│    Detection    │                 │                  │
│    ↓            │                 │                  │
│ 2. Audio        │                 │                  │
│    Recording    │                 │                  │
│    (VAD)        │                 │                  │
│    ↓            │                 │                  │
│ 3. Transcribe   │                 │                  │
│    (Whisper)    │   HTTP POST     │ 4. Generate      │
│    ↓            ├────────────────►│    Response      │
│ POST /voice/ask │  {"question"}   │    (Ollama)      │
│                 │                 │    ↓             │
│ 7. Speak Each   │  Stream back    │ 5. Stream        │
│    Chunk        │◄────────────────┤    Sentences     │
│    (Piper TTS)  │  {"text": ""}   │    (Real-time)   │
│                 │                 │                  │
└─────────────────┘                 └──────────────────┘
```

## Components

### 1. Pi Client (`src/voice_assistant.py`)

**Purpose:** Voice input and output on Raspberry Pi

**Dependencies:**
- `openwakeword` - Wake word detection (Alexa, Hey Jarvis, etc.)
- `webrtcvad` - Voice activity detection (silence cutoff)
- `faster-whisper` - Speech-to-text (tiny model, int8)
- `sounddevice` - Audio capture
- `piper-tts` - Text-to-speech
- `paplay` - Audio playback (PulseAudio)

**Flow:**
1. Continuously listen for wake words
2. When detected, record audio until silence (1.5s)
3. Transcribe with Whisper
4. POST question to mirapc voice server
5. Stream response chunks back
6. Speak each chunk immediately with Piper

**Wake Words:**
- "Alexa"
- "Hey Jarvis"
- "Hey Mycroft"
- "Hey Rhasspy"

**Audio Config:**
- Sample rate: 16kHz
- VAD aggressiveness: 2 (moderate)
- Max recording: 12 seconds
- Silence cutoff: 1.5 seconds

### 2. mirapc Server (`mirapc/voice_server.py`)

**Purpose:** Generate voice-optimized responses

**Dependencies:**
- `flask` - HTTP server
- `curl` - Ollama API streaming

**Flow:**
1. Receive POST with `{"question": "..."}`
2. Build voice-optimized prompt
3. Stream from Ollama (qwen2.5:14b)
4. Parse sentences in real-time
5. Yield each sentence as JSON: `{"text": "..."}`

**Ollama Config:**
- Model: `qwen2.5:14b-instruct`
- Endpoint: `http://citadel:11434/v1/chat/completions`
- Temperature: 0.7
- Max tokens: 200 (keep responses short)

**Voice Optimization:**
Prompt instructs model to:
- Keep responses to 1-3 sentences max
- Use natural spoken language
- No markdown or formatting
- Direct answers, no preamble

## Data Flow Example

**User says:** "Alexa, what's the weather?"

1. **Pi:** Wake word detected → record audio
2. **Pi:** Transcribe → "what's the weather?"
3. **Pi:** POST to `mirapc:8765/voice/ask` with `{"question": "what's the weather?"}`
4. **mirapc:** Generate response via Ollama
5. **mirapc:** Stream back:
   ```
   {"text": "It's currently 70 degrees and sunny."}
   {"text": "Perfect day outside."}
   ```
6. **Pi:** Speak first chunk → "It's currently 70 degrees and sunny."
7. **Pi:** Speak second chunk → "Perfect day outside."

**Total latency:** ~1-2 seconds from question to first spoken word

## Network Requirements

**Pi must reach:**
- `mirapc:8765` (voice server)

**mirapc must reach:**
- `citadel:11434` (Ollama API)

**Solution:** Tailscale or local network connectivity

## Optional: GUI Mode

**File:** `src/voice_assistant_gui.py`

**Features:**
- Blue orb visualization (idle/listening/processing/speaking states)
- Settings dialog for audio device switching
- Volume controls
- Wake word configuration

**Integration Status:** GUI skeleton ready, needs integration with voice loop

## Running the System

### On mirapc (server):

```bash
cd ~/voice-assistant/mirapc
python voice_server.py
```

**Output:**
```
🎤 Voice server starting on port 8765...
   Model: qwen2.5:14b-instruct
   Endpoint: http://citadel:11434/v1/chat/completions
```

### On Raspberry Pi (client):

```bash
cd ~/voice-assistant
source venv/bin/activate
python src/voice_assistant.py
```

**Output:**
```
🎤 Voice assistant (HTTP MODE)
   Voice server: http://mirapc:8765/voice/ask
   Device: default @ 16000Hz
   Say: Alexa / Hey Jarvis / Hey Mycroft / Hey Rhasspy
```

## Deployment

### Auto-start on Pi (systemd):

See `SETUP.md` for systemd service configuration.

### Auto-start on mirapc:

```bash
# Add to crontab
@reboot cd /home/mira/voice-assistant/mirapc && python voice_server.py
```

## Troubleshooting

**Pi can't reach mirapc:**
- Verify network connectivity: `ping mirapc`
- Check server is running: `curl http://mirapc:8765/health`

**No wake word detection:**
- Check microphone: `arecord -d 3 test.wav && aplay test.wav`
- Increase volume/gain
- Try different wake word

**Slow responses:**
- Check Ollama is running: `curl http://citadel:11434/api/tags`
- Model loaded: `qwen2.5:14b-instruct`
- Network latency between mirapc ↔ citadel

**TTS not working:**
- Check Piper model exists: `ls ~/voices/*.onnx`
- Test paplay: `speaker-test -t wav`
- Verify audio output device

## Future Enhancements

- **GUI integration:** Connect blue orb to actual voice states
- **Multi-user support:** Voice identification
- **Context awareness:** Remember conversation history
- **Smart home control:** Integrate with lights, thermostats, etc.
- **Calendar/reminders:** Voice-controlled scheduling
- **Music control:** Play/pause/skip via voice

## Performance

**Latency breakdown:**
- Wake word detection: ~100ms
- Recording (with VAD): 1-3 seconds (user dependent)
- Whisper transcription: ~500ms
- LLM first token: ~200ms
- LLM subsequent tokens: ~50ms each
- TTS generation: ~100ms per sentence
- Audio playback: real-time

**Total time (wake → first word spoken):** ~2-3 seconds

**Resource usage (Pi):**
- CPU: 10-30% during active listening
- RAM: ~200MB
- Idle: <5% CPU, ~50MB RAM

**Resource usage (mirapc):**
- CPU: Minimal (Ollama runs on citadel)
- RAM: ~50MB
- Idle: <1% CPU
