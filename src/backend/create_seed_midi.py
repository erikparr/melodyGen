#!/usr/bin/env python3
"""
Create simple seed melodies as MIDI files for testing.
"""

from music21 import stream, note, tempo, meter, duration

def create_melody(name, pitches, durations=None):
    """
    Create a MIDI file from a list of pitches.

    Args:
        name: Output filename (without .mid extension)
        pitches: List of MIDI note numbers
        durations: List of durations in quarter notes (default: all 1.0)
    """
    if durations is None:
        durations = [1.0] * len(pitches)

    s = stream.Stream()
    s.append(tempo.TempoIndication(number=120))
    s.append(meter.TimeSignature('4/4'))

    offset = 0
    for pitch, dur in zip(pitches, durations):
        n = note.Note(pitch)
        n.duration = duration.Duration(quarterLength=dur)
        s.insert(offset, n)
        offset += dur

    filename = f"{name}.mid"
    s.write('midi', fp=filename)
    print(f"✓ Created: {filename} ({len(pitches)} notes)")

print("=" * 60)
print("Creating Test Seed Melodies")
print("=" * 60)
print()

# 1. C Major Scale
create_melody(
    name="seed_c_major_scale",
    pitches=[60, 62, 64, 65, 67, 69, 71, 72],  # C D E F G A B C
    durations=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0]
)

# 2. Simple Arpeggio (C E G C)
create_melody(
    name="seed_c_major_arpeggio",
    pitches=[60, 64, 67, 72],  # C E G C
    durations=[1.0, 1.0, 1.0, 2.0]
)

# 3. Twinkle Twinkle Little Star (opening)
create_melody(
    name="seed_twinkle_twinkle",
    pitches=[60, 60, 67, 67, 69, 69, 67],  # C C G G A A G
    durations=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0]
)

# 4. Mary Had a Little Lamb (opening)
create_melody(
    name="seed_mary_little_lamb",
    pitches=[64, 62, 60, 62, 64, 64, 64],  # E D C D E E E
    durations=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0]
)

# 5. Happy Birthday (simplified opening)
create_melody(
    name="seed_happy_birthday",
    pitches=[60, 60, 62, 60, 65, 64],  # C C D C F E
    durations=[0.75, 0.25, 1.0, 1.0, 1.0, 2.0]
)

# 6. Short Melodic Fragment
create_melody(
    name="seed_fragment",
    pitches=[60, 64, 67, 65, 62, 60],  # C E G F D C
    durations=[0.5, 0.5, 1.0, 0.5, 0.5, 2.0]
)

# 7. Minor Scale (A minor)
create_melody(
    name="seed_a_minor_scale",
    pitches=[69, 71, 60, 62, 64, 65, 67, 69],  # A B C D E F G A
    durations=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0]
)

# 8. Blues-ish Phrase
create_melody(
    name="seed_blues_phrase",
    pitches=[60, 63, 65, 66, 67, 65, 60],  # C Eb F Gb G F C
    durations=[1.0, 0.5, 0.5, 0.5, 0.5, 1.0, 2.0]
)

print()
print("=" * 60)
print("Created 8 seed MIDI files")
print("=" * 60)
print("\nNow you can test with:")
print("  python import_and_vary.py seed_c_major_scale.mid")
print("  python import_and_vary.py seed_twinkle_twinkle.mid minor A")
print("  python import_and_vary.py seed_blues_phrase.mid blues C")
