# OSC Communication Specification

This document specifies the OSC message protocol between the MelodyGen web app and SuperCollider.

## Overview

- **Web App → SuperCollider**: Send melodies to play (port 7000)
- **SuperCollider → Web App**: Send completion notifications (port 7001)

## 1. Sending Melodies (Web App → SuperCollider)

**Target**: `127.0.0.1:7000`

**OSC Addresses**:
- `/melody` - For sequential melodies (chordMode: false or not specified)
- `/chord` - For chord mode melodies (chordMode: true)

**Argument**: Single JSON string (OSC type 's', NOT Symbol 'S')

The JSON payload is sent as an OSC String argument containing:

```json
{
  "notes": [
    {
      "midi": 78,
      "vel": 0.7,
      "dur": 0.25
    },
    {
      "midi": 73,
      "vel": 0.7,
      "dur": 0.25
    }
  ],
  "metadata": {
    "totalDuration": 3.0,
    "noteCount": 5,
    "name": "Original",
    "key": "C",
    "scale": "major",
    "loop": true,
    "chordMode": false,
    "targetGroup": 0
  }
}
```

### Field Descriptions

**notes** (array): List of notes to play
- `midi` (int): MIDI note number (0-127)
- `vel` (float): Velocity (0.0-1.0)
- `dur` (float): Duration in seconds

**metadata** (object): Melody information
- `totalDuration` (float): Total length of melody in seconds
- `noteCount` (int): Number of notes
- `name` (string): Melody name for display
- `key` (string, optional): Musical key (e.g., "C", "D", "F#")
- `scale` (string, optional): Scale type (e.g., "major", "minor")
- `loop` (boolean): **IMPORTANT** - Controls playback mode
  - `true`: Loop melody continuously (DO NOT send completion message)
  - `false`: Play once and send completion message when done
- `chordMode` (boolean, optional): Indicates if notes are chords (simultaneous notes)
  - `true`: Notes with same time should be played as a chord
  - `false`: Sequential melody playback (default)
- `targetGroup` (int): **NEW** - 0-based track index for routing
  - Track 0 → `targetGroup: 0`
  - Track 1 → `targetGroup: 1`
  - Track 2 → `targetGroup: 2`, etc.
  - Maps to synth groups/busses in SuperCollider

### Routing Behavior

The web app automatically routes messages based on the `chordMode` flag:

**Sequential Melodies** (`chordMode: false` or not specified):
- Sent to: `/melody`
- Use case: Traditional melodic sequences where notes play one after another

**Chord Mode** (`chordMode: true`):
- Sent to: `/chord`
- Use case: Simultaneous notes recorded as chords
- Example payload sent to `/chord`:
```json
{
  "notes": [
    {"midi": 66, "vel": 0.28, "dur": 0.625},
    {"midi": 54, "vel": 0.47, "dur": 0.625},
    {"midi": 61, "vel": 0.59, "dur": 0.5}
  ],
  "metadata": {
    "totalDuration": 1.125,
    "noteCount": 3,
    "name": "New Melody",
    "loop": false,
    "targetGroup": 0,
    "key": "C",
    "scale": "major",
    "chordMode": true
  }
}
```

## 2. Completion Notifications (SuperCollider → Web App)

**Target**: `127.0.0.1:7001`

**OSC Addresses**:
- `/melody/complete` - Sent when sequential melody finishes (loop: false)
- `/chord/complete` - Sent when chord mode melody finishes (loop: false)

**Argument**: Single integer - targetGroup (0-based track index)

### When to Send

**✅ Send completion message when:**
- `loop: false` in metadata
- The last note has finished playing (after its duration)

**❌ DO NOT send completion message when:**
- `loop: true` in metadata
- Melody is still playing

### Examples

```
/melody/complete 0    // targetGroup 0 finished playing one-shot melody
/melody/complete 1    // targetGroup 1 finished playing one-shot melody
/chord/complete 0     // targetGroup 0 finished playing one-shot chord
/chord/complete 2     // targetGroup 2 finished playing one-shot chord
```

## 3. Use Cases

### Loop Mode (Continuous Playback)
```json
{
  "notes": [...],
  "metadata": {
    "loop": true,
    ...
  }
}
```
- Melody loops continuously
- User must manually stop via UI
- No completion message sent

### One-Shot Mode (Single Playback)
```json
{
  "notes": [...],
  "metadata": {
    "loop": false,
    ...
  }
}
```
- Melody plays once
- SuperCollider sends `/melody/complete [targetGroup]` when done
- Web app can trigger next action (e.g., play next in sequence)

### Sequencer Mode
- Web app sends multiple melodies with `loop: false`
- After each completion message, web app automatically sends next melody
- Enables automated playback of melody variations

## 4. Testing

You can test the OSC receiver using Python:

```python
from pythonosc import udp_client

# Send completion message for targetGroup 0
client = udp_client.SimpleUDPClient('127.0.0.1', 7001)
client.send_message('/melody/complete', 0)
```

The web app backend will log:
```
✅ Melody completed on targetGroup 0
```

## 5. Implementation Notes

### Timing Accuracy
- Send completion message AFTER the last note's duration has elapsed
- Not when the last note starts, but when it finishes
- Example: If last note starts at 2.5s with duration 1.0s, send at 3.5s

### Error Handling
- If melody playback is interrupted, do not send completion message
- If a new melody arrives while one is playing, handle according to your SuperCollider implementation

### Debug Logging
The web app logs all OSC messages:
- Browser console: Shows JSON payload with targetGroup before sending
- Backend console: Shows full message with address and payload
- Completion events: Shows targetGroup when received

## 6. Port Summary

| Direction | Port | Purpose |
|-----------|------|---------|
| Web → SC  | 7000 | Send melodies to play |
| SC → Web  | 7001 | Send completion notifications |

## 7. Backend Endpoints

For debugging and monitoring:

**HTTP Polling** (fallback if WebSocket unavailable):
- `GET http://localhost:8000/osc/completions` - Get all completion events
- `GET http://localhost:8000/osc/completions?since=<timestamp>` - Get events after timestamp

**WebSocket** (real-time notifications):
- `WS ws://localhost:8000/ws/completions` - Connect for live completion events

**Send Melody**:
- `POST http://localhost:8000/osc/send-melody` - Send melody to SuperCollider
