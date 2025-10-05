#!/usr/bin/env python3
"""
Process JSON melodies from ototope-i.json and generate variations.
"""

import json
import os
from variations import VariationGenerator
from constraints import MelodyValidator
from music21 import stream, note, tempo, meter, duration

def convert_json_to_notes(layer_data):
    """
    Convert JSON melody format to our note format.

    Input format has:
    - notes: [{midi, vel, dur}, ...]
    - timing: [0, t1, t2, ...]  (normalized 0-1)
    - metadata: {totalDuration, key, scale, ...}

    Output format:
    - [{midi, time, duration, velocity}, ...]
    """
    notes_data = layer_data['notes']
    timing = layer_data['timing']
    metadata = layer_data['metadata']
    total_duration = metadata['totalDuration']

    converted_notes = []
    current_time = 0

    for i, note_data in enumerate(notes_data):
        # Convert timing from normalized to actual seconds
        time_increment = timing[i] * total_duration
        current_time += time_increment

        # Calculate actual duration
        if metadata['durationType'] == 'fractional':
            # Duration is fraction of time until next note
            if i < len(notes_data) - 1:
                time_to_next = timing[i + 1] * total_duration
                actual_duration = note_data['dur'] * time_to_next
            else:
                # Last note
                time_to_end = timing[i + 1] * total_duration if i + 1 < len(timing) else 0.5
                actual_duration = note_data['dur'] * time_to_end
        else:
            # Absolute duration
            actual_duration = note_data['dur']

        converted_notes.append({
            'midi': note_data['midi'],
            'time': current_time,
            'duration': actual_duration,
            'velocity': note_data['vel']
        })

    return converted_notes, metadata['key'], metadata['scale']

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
    # Load JSON file
    json_path = '../../data/ototope-i.json'

    if not os.path.exists(json_path):
        print(f"Error: File not found: {json_path}")
        print("Make sure you're running this from src/backend/")
        return

    print("=" * 60)
    print("Processing ototope-i.json Melodies")
    print("=" * 60)

    with open(json_path, 'r') as f:
        data = json.load(f)

    melodies = data['melodies']
    print(f"\nFound {len(melodies)} melodies:")
    for name in melodies.keys():
        print(f"  - {name}")

    # Process each melody
    os.makedirs('output', exist_ok=True)

    for melody_name, melody_data in melodies.items():
        print(f"\n{'=' * 60}")
        print(f"Processing: {melody_name}")
        print('=' * 60)

        # Get first layer (assuming layer1 exists)
        if 'layer1' not in melody_data['layers']:
            print(f"  Skipping {melody_name} - no layer1 found")
            continue

        layer1 = melody_data['layers']['layer1']

        # Convert to our format
        notes, key, scale = convert_json_to_notes(layer1)

        print(f"  Notes: {len(notes)}")
        print(f"  Key: {key} {scale}")
        print(f"  First note: MIDI {notes[0]['midi']}")
        print(f"  Last note: MIDI {notes[-1]['midi']}")

        # Generate variations
        print(f"\n  Generating variations...")
        generator = VariationGenerator(scale, key)
        variations = generator.generate_batch(notes, count=20)
        print(f"  Generated: {len(variations)} variations")

        # Validate
        print(f"  Validating...")
        validator = MelodyValidator(scale, key)
        valid = validator.filter_valid_variations(variations)
        print(f"  Valid: {len(valid)}/{len(variations)}")

        if not valid:
            print(f"  ⚠️  No valid variations for {melody_name}")
            print(f"  Exporting all variations anyway...")
            valid = variations[:10]  # Take first 10

        # Export
        melody_folder = f"output/{melody_name}"
        os.makedirs(melody_folder, exist_ok=True)

        # Export original
        export_to_midi(notes, f"{melody_folder}/00_original.mid")
        print(f"\n  ✓ {melody_folder}/00_original.mid")

        # Export variations
        for i, var in enumerate(valid[:10], 1):
            filename = f"{melody_folder}/{i:02d}_{var['metadata']['variation_type']}.mid"
            export_to_midi(var['notes'], filename)
            print(f"  ✓ {filename}")
            print(f"     {var['metadata']['method']}")

    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)
    print(f"\nProcessed {len(melodies)} melodies")
    print("Check output/ folder for results")
    print("\nFolder structure:")
    print("  output/")
    for melody_name in melodies.keys():
        print(f"    {melody_name}/")
        print(f"      00_original.mid")
        print(f"      01_*.mid")
        print(f"      ...")

if __name__ == "__main__":
    main()
