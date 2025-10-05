#!/usr/bin/env python3
"""
Import a MIDI file and generate variations from it.
"""

import sys
import os
import mido
from variations import VariationGenerator
from constraints import MelodyValidator
from music21 import stream, note, tempo, meter, duration

def import_midi_file(filepath):
    """
    Import MIDI file and extract notes.

    Args:
        filepath: Path to MIDI file

    Returns:
        List of note dicts
    """
    print(f"Importing: {filepath}")

    mid = mido.MidiFile(filepath)

    # Get tempo
    tempo_value = 500000  # Default 120 BPM
    for msg in mid.tracks[0]:
        if msg.type == 'set_tempo':
            tempo_value = msg.tempo
            break

    bpm = 60000000 / tempo_value
    print(f"  Tempo: {int(bpm)} BPM")

    # Extract notes from first track with notes
    notes = []
    for track in mid.tracks:
        active_notes = {}
        current_time = 0

        for msg in track:
            current_time += msg.time

            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = (current_time, msg.velocity)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start_time, velocity = active_notes[msg.note]
                    duration_ticks = current_time - start_time

                    time_seconds = mido.tick2second(start_time, mid.ticks_per_beat, tempo_value)
                    duration_seconds = mido.tick2second(duration_ticks, mid.ticks_per_beat, tempo_value)

                    notes.append({
                        'midi': msg.note,
                        'time': time_seconds,
                        'duration': duration_seconds,
                        'velocity': velocity / 127.0
                    })
                    del active_notes[msg.note]

        if notes:  # Use first track with notes
            break

    notes.sort(key=lambda n: n['time'])
    print(f"  Extracted: {len(notes)} notes")

    return notes

def export_to_midi(notes, filepath):
    """Export notes to MIDI file"""
    s = stream.Stream()
    s.append(tempo.TempoIndication(number=120))
    s.append(meter.TimeSignature('4/4'))

    for note_data in notes:
        n = note.Note(note_data['midi'])
        n.duration = duration.Duration(quarterLength=note_data['duration'] * 2)
        n.offset = note_data['time'] * 2
        n.volume.velocity = int(note_data.get('velocity', 0.7) * 127)
        s.insert(n.offset, n)

    s.write('midi', fp=filepath)

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_and_vary.py <midi_file> [scale_type] [root_note]")
        print("\nExample:")
        print("  python import_and_vary.py my_melody.mid")
        print("  python import_and_vary.py my_melody.mid minor D")
        print("\nSupported scales:")
        print("  major, minor, dorian, phrygian, lydian, mixolydian, pentatonic, blues")
        sys.exit(1)

    # Parse arguments
    midi_file = sys.argv[1]
    scale_type = sys.argv[2] if len(sys.argv) > 2 else "major"
    root_note = sys.argv[3] if len(sys.argv) > 3 else "C"

    if not os.path.exists(midi_file):
        print(f"Error: File not found: {midi_file}")
        sys.exit(1)

    print("=" * 60)
    print("MIDI Import and Variation Generator")
    print("=" * 60)

    # Import
    seed_notes = import_midi_file(midi_file)

    if not seed_notes:
        print("Error: No notes found in MIDI file")
        sys.exit(1)

    # Show melody info
    print(f"\nMelody info:")
    print(f"  Notes: {len(seed_notes)}")
    pitches = [n['midi'] for n in seed_notes]
    print(f"  Range: MIDI {min(pitches)}-{max(pitches)}")
    print(f"  Duration: {seed_notes[-1]['time'] + seed_notes[-1]['duration']:.2f} seconds")

    # Generate variations
    print("\n" + "=" * 60)
    print(f"Generating variations in {root_note} {scale_type}")
    print("=" * 60)

    generator = VariationGenerator(scale_type, root_note)
    variations = generator.generate_batch(seed_notes, count=20)

    print(f"\nGenerated {len(variations)} variations")

    # Validate
    print("\nValidating...")
    validator = MelodyValidator(scale_type, root_note)
    valid = validator.filter_valid_variations(variations)

    print(f"Valid: {len(valid)}/{len(variations)}")

    if not valid:
        print("\n⚠️  No variations passed validation!")
        print("This might mean:")
        print("  - The seed melody is outside the specified key/scale")
        print("  - Try a different scale_type or root_note")
        print("  - Try: python import_and_vary.py", midi_file, "minor C")
        return

    # Export
    print("\n" + "=" * 60)
    print("Exporting to output/")
    print("=" * 60)

    os.makedirs('output', exist_ok=True)

    # Export seed
    export_to_midi(seed_notes, 'output/00_original.mid')
    print(f"\n✓ output/00_original.mid")

    # Export top 10 variations
    for i, var in enumerate(valid[:10], 1):
        filename = f"output/{i:02d}_{var['metadata']['variation_type']}.mid"
        export_to_midi(var['notes'], filename)
        print(f"✓ {filename}")
        print(f"   {var['metadata']['method']}")

    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)
    print(f"\n{len(valid[:10])} MIDI files saved to output/")
    print("Open them in your DAW, notation software, or MIDI player")

if __name__ == "__main__":
    main()
