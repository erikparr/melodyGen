#!/usr/bin/env python3
"""
Create and test your own custom melody.
"""

from variations import VariationGenerator
from constraints import MelodyValidator
from music21 import stream, note, tempo, meter, duration
import os

# ============================================================
# STEP 1: Define your melody
# ============================================================

# Example 1: Simple 4-note melody
my_melody = [
    {"midi": 60, "time": 0.0, "duration": 0.5, "velocity": 0.7},   # C
    {"midi": 64, "time": 0.5, "duration": 0.5, "velocity": 0.7},   # E
    {"midi": 67, "time": 1.0, "duration": 0.5, "velocity": 0.7},   # G
    {"midi": 60, "time": 1.5, "duration": 1.0, "velocity": 0.7},   # C (ending)
]

# Example 2: "Twinkle Twinkle Little Star" opening
twinkle = [
    {"midi": 60, "time": 0.0, "duration": 0.5, "velocity": 0.7},   # C - Twin-
    {"midi": 60, "time": 0.5, "duration": 0.5, "velocity": 0.7},   # C - kle
    {"midi": 67, "time": 1.0, "duration": 0.5, "velocity": 0.7},   # G - twin-
    {"midi": 67, "time": 1.5, "duration": 0.5, "velocity": 0.7},   # G - kle
    {"midi": 69, "time": 2.0, "duration": 0.5, "velocity": 0.7},   # A - lit-
    {"midi": 69, "time": 2.5, "duration": 0.5, "velocity": 0.7},   # A - tle
    {"midi": 67, "time": 3.0, "duration": 1.0, "velocity": 0.7},   # G - star
]

# ============================================================
# STEP 2: Choose which melody to use
# ============================================================

seed = twinkle  # <-- Change this to test different melodies

print("=" * 60)
print("Testing Custom Melody")
print("=" * 60)
print(f"\nSeed melody: {len(seed)} notes")
for i, note_data in enumerate(seed):
    print(f"  {i+1}. MIDI {note_data['midi']} at {note_data['time']}s for {note_data['duration']}s")

# ============================================================
# STEP 3: Generate variations
# ============================================================

print("\n" + "=" * 60)
print("Generating Variations")
print("=" * 60)

generator = VariationGenerator(scale_type="major", root_note="C")
variations = generator.generate_batch(seed, count=10)

print(f"\nGenerated {len(variations)} variations:")
for i, var in enumerate(variations, 1):
    print(f"  {i}. {var['metadata']['method']:<30} ({len(var['notes'])} notes)")

# ============================================================
# STEP 4: Validate variations
# ============================================================

print("\n" + "=" * 60)
print("Validating Variations")
print("=" * 60)

validator = MelodyValidator(scale_type="major", root_note="C")
valid_variations = validator.filter_valid_variations(variations)

print(f"\nValid variations: {len(valid_variations)}/{len(variations)}")

if valid_variations:
    print("\nValid variations:")
    for i, var in enumerate(valid_variations, 1):
        val = var.get('validation', {})
        checks = val.get('checks', {})
        key_pct = checks.get('key_membership', {}).get('in_scale_percentage', 0)
        cadence = checks.get('cadence', {}).get('cadence_type', 'Unknown')

        print(f"  {i}. {var['metadata']['method']}")
        print(f"      Key: {key_pct}% in scale, Cadence: {cadence}")
else:
    print("\n⚠️  No variations passed validation!")
    print("Try generating more (count=20) or disable constraints")

# ============================================================
# STEP 5: Export to MIDI files
# ============================================================

print("\n" + "=" * 60)
print("Exporting to MIDI")
print("=" * 60)

os.makedirs('output', exist_ok=True)

# Export original seed
s = stream.Stream()
s.append(tempo.TempoIndication(number=120))
s.append(meter.TimeSignature('4/4'))

for note_data in seed:
    n = note.Note(note_data['midi'])
    n.duration = duration.Duration(quarterLength=note_data['duration'] * 2)
    n.offset = note_data['time'] * 2
    n.volume.velocity = int(note_data.get('velocity', 0.7) * 127)
    s.insert(n.offset, n)

s.write('midi', fp='output/seed_melody.mid')
print("\n✓ Exported: output/seed_melody.mid (original)")

# Export valid variations
for i, var in enumerate(valid_variations[:5], 1):  # Top 5 only
    s = stream.Stream()
    s.append(tempo.TempoIndication(number=120))
    s.append(meter.TimeSignature('4/4'))

    for note_data in var['notes']:
        n = note.Note(note_data['midi'])
        n.duration = duration.Duration(quarterLength=note_data['duration'] * 2)
        n.offset = note_data['time'] * 2
        n.volume.velocity = int(note_data.get('velocity', 0.7) * 127)
        s.insert(n.offset, n)

    filename = f"output/variation_{i:02d}.mid"
    s.write('midi', fp=filename)
    print(f"✓ Exported: {filename} - {var['metadata']['method']}")

print("\n" + "=" * 60)
print("Complete!")
print("=" * 60)
print(f"\nCheck the 'output/' folder for MIDI files")
print("You can open them in any DAW or music notation software")
