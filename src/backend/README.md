# MelodyGen - Melody Variation & Interpolation System

A modern melody variation and interpolation system using symbolic music transformations and intelligent constraint validation.

## Overview

MelodyGen generates coherent melodic permutations from seed melodies using:
- **Symbolic operations** (transpose, invert, augment, ornament, etc.)
- **DTW-based interpolation** for smooth A→B morphing
- **Constraint validation** (key membership, cadence, range, rhythm)
- **Batch generation** with diversity selection

Built with FastAPI, music21, and numpy.

## Architecture

### Backend (Tier 1 - Symbolic Operations)

```
src/backend/
├── main.py              # FastAPI server & endpoints
├── variations.py        # Batch variation generation
├── interpolate.py       # DTW/contour/feature interpolation
├── constraints.py       # Constraint validators
├── transformations.py   # Core music transformations (from gesture)
├── scale_utils.py       # Scale/interval utilities (from gesture)
└── requirements.txt     # Python dependencies
```

### Key Features

**17 Variation Types:**
- Transpose (chromatic & diatonic)
- Invert (center/first-note/last-note axis)
- Augment/Diminish (rhythmic stretching/compression)
- Ornament (classical/jazz/baroque styles)
- Develop (sequence/retrograde/fragment/extend)
- Harmonize (3rd/5th intervals)
- Counter melody (contrary/parallel motion)

**3 Interpolation Methods:**
- DTW alignment with scale snapping
- Contour-based morphing
- Feature-based blending (mean pitch, variance, rhythm density)

**Constraint Validation:**
- Key membership (≥90% in-scale notes)
- Cadence detection (7→1, 5→1, 2→1 patterns)
- Pitch range enforcement
- Rhythm coherence (rest density, note duration checks)

## Installation

### Backend Setup

```bash
cd src/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_api.py

# Start server
uvicorn main:app --reload
```

Backend runs on http://localhost:8000

## API Endpoints

### 1. Generate Variations

```bash
POST /variation/generate
```

**Request:**
```json
{
  "notes": [
    {"midi": 60, "time": 0.0, "duration": 0.5, "velocity": 0.7},
    {"midi": 62, "time": 0.5, "duration": 0.5, "velocity": 0.7}
  ],
  "scale_type": "major",
  "root_note": "C",
  "count": 10,
  "apply_constraints": true
}
```

**Response:**
```json
{
  "success": true,
  "variations": [
    {
      "id": "var_1_1234567890",
      "notes": [...],
      "metadata": {
        "method": "Transpose +3 semitones",
        "variation_type": "transpose_up",
        "scale": "major",
        "key": "C"
      }
    }
  ],
  "statistics": {
    "total_variations": 10,
    "average_notes_per_variation": 8.5,
    "pitch_range": {"lowest": 55, "highest": 79}
  }
}
```

### 2. Interpolate Melodies

```bash
POST /variation/interpolate
```

**Request:**
```json
{
  "melody_a": [...],
  "melody_b": [...],
  "scale_type": "major",
  "root_note": "C",
  "steps": 5,
  "method": "dtw"
}
```

**Methods:** `"dtw"`, `"contour"`, `"feature"`

**Response:**
```json
{
  "success": true,
  "interpolated_melodies": [
    [...],  // Original A
    [...],  // Step 1
    [...],  // Step 2
    [...]   // Original B
  ],
  "total_melodies": 7
}
```

### 3. Validate Melody

```bash
POST /variation/validate
```

**Request:**
```json
{
  "notes": [...],
  "scale_type": "major",
  "root_note": "C",
  "check_key": true,
  "check_cadence": true,
  "check_range": true
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "passed": true,
    "checks": {
      "key_membership": {
        "passed": true,
        "in_scale_percentage": 100.0
      },
      "cadence": {
        "passed": true,
        "cadence_type": "Leading tone to tonic"
      },
      "range": {
        "passed": true,
        "melody_range": {"lowest": 60, "highest": 72}
      }
    }
  }
}
```

### 4. Export to MIDI

```bash
POST /variation/export-midi
```

Returns MIDI file for download.

### 5. Import MIDI

```bash
POST /variation/import-midi
```

Upload MIDI file, returns parsed note data.

## Test Results

```
✓ Variation Generation: 5/5 variations generated
✓ Interpolation: DTW, contour, and feature methods working
✓ Validation: Key, cadence, range, rhythm checks passing
✓ MIDI Export: 136-byte MIDI file created successfully
```

## Usage Examples

### Python

```python
from variations import VariationGenerator
from constraints import MelodyValidator

# Create seed melody
seed = [
    {"midi": 60, "time": 0.0, "duration": 0.5, "velocity": 0.7},
    {"midi": 62, "time": 0.5, "duration": 0.5, "velocity": 0.7},
    {"midi": 64, "time": 1.0, "duration": 0.5, "velocity": 0.7}
]

# Generate variations
generator = VariationGenerator("major", "C")
variations = generator.generate_batch(seed, count=10)

# Validate
validator = MelodyValidator("major", "C")
valid = validator.filter_valid_variations(variations)

print(f"Generated {len(valid)} valid variations")
```

### cURL

```bash
# Generate variations
curl -X POST http://localhost:8000/variation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "notes": [{"midi": 60, "time": 0, "duration": 0.5, "velocity": 0.7}],
    "scale_type": "major",
    "root_note": "C",
    "count": 5
  }'
```

## Project Structure

```
melodyGen/
├── README.md                    # This file
├── proposal_v2.md               # Design proposal
├── context.md                   # Original requirements
├── src/
│   └── backend/
│       ├── main.py              # API server
│       ├── variations.py        # Variation generator
│       ├── interpolate.py       # Interpolation methods
│       ├── constraints.py       # Validators
│       ├── transformations.py   # Core transformations
│       ├── scale_utils.py       # Scale utilities
│       ├── test_api.py          # Test suite
│       └── requirements.txt
└── temp/
    └── gesture/                 # Reference implementation
```

## Supported Scales

Major, Minor, Harmonic Minor, Melodic Minor, Pentatonic (Major/Minor), Blues, Chromatic, Whole Tone, and all 7 modes (Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian)

## Dependencies

- **FastAPI 0.104.1** - REST API framework
- **music21 9.1.0** - Music analysis and MIDI I/O
- **mido 1.3.0** - MIDI file handling
- **numpy 1.26.0** - Numerical operations (DTW, interpolation)
- **uvicorn 0.24.0** - ASGI server

## Roadmap

### Tier 1 (Current) ✓
- Symbolic transformations
- DTW/contour interpolation
- Constraint validation

### Tier 2 (Future)
- N-gram language model scoring
- MusicVAE embedding distance
- Diversity selection (farthest-point sampling)

### Tier 3 (Optional)
- MusicVAE latent space interpolation
- Rule-guided diffusion models

## License

MIT

## References

- **gesture** - Base implementation (Erik Parr)
- **music21** - Michael Scott Cuthbert (MIT)
- **MusicVAE** - Google Magenta
- Proposal based on research from ICML 2024, AAAI 2024, MIT Media Lab

## Author

Built with Claude Code (Sonnet 4.5)
Date: 2025-10-04
