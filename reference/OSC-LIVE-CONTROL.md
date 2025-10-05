# OSC Live Control - Sending Melody Messages to SuperCollider

## Overview

The layers system supports real-time melody control via OSC messages. Send melody data from external applications (DAWs, mobile apps, custom controllers) to trigger playback on any of the three layers.

## Quick Start

**Host:** `127.0.0.1` (local) or your computer's IP address (remote)
**Port:** `7000`
**Message Format:** `/liveMelody/update/layer[1-3]` + JSON string

## Basic Usage

### Simple Melody (C Major Scale)

```
OSC Address: /liveMelody/update/layer1
Argument: JSON string
```

```json
{
  "notes": [
    {"midi": 60, "vel": 0.8, "dur": 0.4},
    {"midi": 62, "vel": 0.8, "dur": 0.4},
    {"midi": 64, "vel": 0.8, "dur": 0.4},
    {"midi": 65, "vel": 0.8, "dur": 0.4},
    {"midi": 67, "vel": 0.8, "dur": 0.4}
  ],
  "metadata": {
    "totalDuration": 3.0,
    "noteCount": 5,
    "name": "C Major Scale"
  }
}
```

**Result:** Layer 1 immediately starts playing the melody and loops every 3 seconds.

## JSON Format Specification

### Required Fields

```json
{
  "notes": [
    {
      "midi": 60,      // MIDI note number (0-127)
      "vel": 0.8,      // Velocity (0.0-1.0)
      "dur": 0.4       // Duration scalar (optional per note)
    }
  ],
  "metadata": {
    "totalDuration": 3.0,    // Loop duration in seconds
    "noteCount": 5,          // Number of notes
    "name": "Melody Name"    // Optional: melody identifier
  }
}
```

### Optional: Expression Overrides

Add expression control parameters to override MIDI knob settings:

```json
{
  "notes": [...],
  "metadata": {...},
  "expressionOverrides": {
    "expressionCC": 11,
    "expressionMin": 20,
    "expressionMax": 100,
    "expressionShape": "exp",
    "expressionPeakPos": 0.7,
    "expressionDurationScalar": 1.2
  }
}
```

**Expression Shapes:** `sin`, `exp`, `linear`, `custom`

## Sending from Different Platforms

### TouchOSC / Lemur

1. Create an OSC message control
2. Set destination IP: `127.0.0.1` (or your Mac's IP)
3. Port: `7000`
4. Address: `/liveMelody/update/layer1`
5. Argument type: String
6. Value: Your JSON melody data

### Max/MSP

```
[prepend /liveMelody/update/layer1]
|
[udpsend 127.0.0.1 7000]
```

### Python (python-osc)

```python
from pythonosc import udp_client

client = udp_client.SimpleUDPClient("127.0.0.1", 7000)

melody_json = '''
{
  "notes": [
    {"midi": 60, "vel": 0.8, "dur": 0.4},
    {"midi": 64, "vel": 0.8, "dur": 0.4},
    {"midi": 67, "vel": 0.8, "dur": 0.4}
  ],
  "metadata": {
    "totalDuration": 2.0,
    "noteCount": 3,
    "name": "C Major Triad"
  }
}
'''

client.send_message("/liveMelody/update/layer1", melody_json)
```

### JavaScript (osc-js)

```javascript
const OSC = require('osc-js');

const osc = new OSC({ plugin: new OSC.DatagramPlugin() });

const melody = {
  notes: [
    { midi: 60, vel: 0.8, dur: 0.4 },
    { midi: 64, vel: 0.8, dur: 0.4 },
    { midi: 67, vel: 0.8, dur: 0.4 }
  ],
  metadata: {
    totalDuration: 2.0,
    noteCount: 3,
    name: "C Major Triad"
  }
};

const message = new OSC.Message(
  '/liveMelody/update/layer1',
  JSON.stringify(melody)
);

osc.send(message, { host: '127.0.0.1', port: 7000 });
```

## Layer Control

### Layer Addresses

- **Layer 1:** `/liveMelody/update/layer1`
- **Layer 2:** `/liveMelody/update/layer2`
- **Layer 3:** `/liveMelody/update/layer3`

### Independent Playback

Each layer plays independently:
- Sending to layer1 doesn't affect layer2 or layer3
- Layers can play different melodies simultaneously
- Sending a new melody to a playing layer updates it on the next loop

### Stopping Layers

Use the SuperCollider GUI or call:
```supercollider
~stopLayerIndependent.(\layer1);
```

## Example Melodies

### Pentatonic Pattern

```json
{
  "notes": [
    {"midi": 60, "vel": 0.9, "dur": 0.5},
    {"midi": 62, "vel": 0.8, "dur": 0.5},
    {"midi": 64, "vel": 0.8, "dur": 0.5},
    {"midi": 67, "vel": 0.9, "dur": 0.5},
    {"midi": 69, "vel": 0.8, "dur": 0.5}
  ],
  "metadata": {
    "totalDuration": 4.0,
    "noteCount": 5,
    "name": "C Pentatonic"
  }
}
```

### Rhythmic Variation

```json
{
  "notes": [
    {"midi": 60, "vel": 1.0, "dur": 0.3},
    {"midi": 60, "vel": 0.5, "dur": 0.3},
    {"midi": 64, "vel": 0.8, "dur": 0.4},
    {"midi": 67, "vel": 0.9, "dur": 0.5}
  ],
  "metadata": {
    "totalDuration": 2.0,
    "noteCount": 4,
    "name": "Rhythmic Pattern"
  }
}
```

### With Expression Control

```json
{
  "notes": [
    {"midi": 60, "vel": 0.8, "dur": 0.4},
    {"midi": 64, "vel": 0.8, "dur": 0.4},
    {"midi": 67, "vel": 0.8, "dur": 0.4},
    {"midi": 72, "vel": 0.8, "dur": 0.4}
  ],
  "metadata": {
    "totalDuration": 3.0,
    "noteCount": 4,
    "name": "Expressive Chord"
  },
  "expressionOverrides": {
    "expressionCC": 11,
    "expressionMin": 10,
    "expressionMax": 127,
    "expressionShape": "sin",
    "expressionPeakPos": 0.5,
    "expressionDurationScalar": 1.0
  }
}
```

## Behavior

### Auto-Start
- When a melody is sent via OSC, the layer **automatically starts playing**
- No need to manually trigger playback

### Loop Mode
- Melodies loop continuously using `metadata.totalDuration`
- Notes are evenly distributed across the duration
- Rest time between loops can be controlled via MIDI (Row 1 Knob 7)

### Live Updates
- Send a new melody while a layer is playing
- Update takes effect on the **next loop iteration**
- No audio glitches or interruptions

### Duration Priority
1. **Explicit duration** in OSC message metadata (highest)
2. **MIDI knob** (Row 1 Knob 1) if manual control is enabled
3. **Default duration** (4.0 seconds)

## Troubleshooting

### Melody Not Playing

1. Check SuperCollider is running
2. Verify port 7000 is open
3. Ensure JSON is valid (use a validator)
4. Check the Post window for error messages

### Wrong Notes Playing

1. Verify MIDI note numbers (60 = middle C)
2. Check velocity values are 0.0-1.0
3. Ensure VST instrument is loaded on the layer

### Timing Issues

1. Check `metadata.totalDuration` matches your intention
2. Verify note count matches array length
3. Use melody rest time control if loops run together

## Testing

SuperCollider includes a test script at `layers/test-live-melody-osc.scd`:

```supercollider
// Load test script
("/path/to/layers/test-live-melody-osc.scd").load;

// Run quick tests
~quickTest1.();  // Simple C major scale
~quickTest2.();  // Pentatonic pattern
~quickTest3.();  // Complex melody with expression
```

## Advanced Features

### Multiple Patterns (Future)

The JSON format supports multiple pattern arrays for windowing mode:

```json
{
  "patterns": [
    [60, 62, 64, 65, 67],
    [64, 65, 67, 69, 71]
  ],
  "metadata": {...}
}
```

Currently, only `patterns[0]` is used. Full multi-pattern support coming soon.

### Integration with DAW

Send melodies from your DAW's MIDI clips:
1. Convert MIDI clip to JSON (custom script)
2. Send via OSC on specific transport positions
3. Trigger different melodies for different song sections

## API Reference

### OSC Address Pattern
```
/liveMelody/update/layer{N}
```
- `{N}`: 1, 2, or 3

### Argument Type
- **Type:** String
- **Format:** JSON
- **Encoding:** UTF-8

### Response
- No OSC response sent
- Check SuperCollider Post window for confirmation:
  ```
  Received live melody update for layer1
  Queued melody update for layer1: 5 notes
  Auto-starting layer1 due to live melody update
  ```

## See Also

- **System Documentation:** `layers/CLAUDE.md`
- **Test Script:** `layers/test-live-melody-osc.scd`
- **Core Implementation:** `layers/layers-live-melody.scd`
