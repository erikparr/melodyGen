#!/usr/bin/env python3
"""
Generate variations from ototope-i.json and export as JSON (not MIDI).
"""

import json
import os
from variations import VariationGenerator
from constraints import MelodyValidator

def convert_json_to_notes(layer_data):
    """
    Convert JSON melody format to our note format.
    """
    notes_data = layer_data['notes']
    timing = layer_data['timing']
    metadata = layer_data['metadata']
    total_duration = metadata['totalDuration']

    converted_notes = []
    current_time = 0

    for i, note_data in enumerate(notes_data):
        time_increment = timing[i] * total_duration
        current_time += time_increment

        if metadata['durationType'] == 'fractional':
            if i < len(notes_data) - 1:
                time_to_next = timing[i + 1] * total_duration
                actual_duration = note_data['dur'] * time_to_next
            else:
                time_to_end = timing[i + 1] * total_duration if i + 1 < len(timing) else 0.5
                actual_duration = note_data['dur'] * time_to_end
        else:
            actual_duration = note_data['dur']

        converted_notes.append({
            'midi': note_data['midi'],
            'time': current_time,
            'duration': actual_duration,
            'velocity': note_data['vel']
        })

    return converted_notes, metadata

def convert_notes_to_json_format(notes, original_metadata):
    """
    Convert our note format back to JSON layer format.

    Input: [{midi, time, duration, velocity}, ...]
    Output: {metadata, notes, timing}
    """
    if not notes:
        return None

    # Calculate total duration
    total_duration = notes[-1]['time'] + notes[-1]['duration']

    # Build notes array
    json_notes = []
    for note in notes:
        json_notes.append({
            "midi": note['midi'],
            "vel": note['velocity'],
            "dur": note['duration']  # Keeping as absolute for now
        })

    # Build timing array (normalized 0-1)
    timing = []
    for i, note in enumerate(notes):
        if i == 0:
            timing.append(0)
        else:
            time_diff = note['time'] - notes[i-1]['time']
            timing.append(time_diff / total_duration)

    # Add final spacing
    if notes:
        final_gap = total_duration - notes[-1]['time']
        timing.append(final_gap / total_duration)

    # Create output structure
    return {
        "metadata": {
            "durationType": "absolute",  # Using absolute for simplicity
            "totalDuration": round(total_duration, 3),
            "key": original_metadata.get('key', 'C'),
            "scale": original_metadata.get('scale', 'major')
        },
        "notes": json_notes,
        "timing": [round(t, 4) for t in timing]
    }

def main():
    # Load JSON file
    json_path = '../../data/ototope-i.json'

    if not os.path.exists(json_path):
        print(f"Error: File not found: {json_path}")
        return

    print("=" * 60)
    print("Generating JSON Variations from ototope-i.json")
    print("=" * 60)

    with open(json_path, 'r') as f:
        data = json.load(f)

    melodies = data['melodies']
    print(f"\nFound {len(melodies)} melodies")

    # Create output structure
    output_data = {
        "source": "ototope-i.json",
        "generator": "melodyGen",
        "melodies": {}
    }

    # Process each melody
    for melody_name, melody_data in melodies.items():
        print(f"\nProcessing: {melody_name}")

        if 'layer1' not in melody_data['layers']:
            print(f"  Skipping - no layer1")
            continue

        layer1 = melody_data['layers']['layer1']

        # Convert to our format
        notes, original_metadata = convert_json_to_notes(layer1)
        key = original_metadata['key']
        scale = original_metadata['scale']

        print(f"  Notes: {len(notes)}, Key: {key} {scale}")

        # Generate variations
        generator = VariationGenerator(scale, key)
        variations = generator.generate_batch(notes, count=20)
        print(f"  Generated: {len(variations)} variations")

        # Validate
        validator = MelodyValidator(scale, key)
        valid = validator.filter_valid_variations(variations)
        print(f"  Valid: {len(valid)}/{len(variations)}")

        # Use all variations if none are valid
        if not valid:
            print(f"  Using all variations (validation disabled)")
            valid = variations[:10]

        # Convert variations to JSON format
        melody_variations = {
            "original": {
                "layer1": layer1
            },
            "variations": {}
        }

        for i, var in enumerate(valid[:10], 1):
            var_name = f"var_{i:02d}_{var['metadata']['variation_type']}"
            json_layer = convert_notes_to_json_format(var['notes'], original_metadata)

            if json_layer:
                melody_variations["variations"][var_name] = {
                    "method": var['metadata']['method'],
                    "layer1": json_layer
                }
                print(f"  ✓ {var_name}: {var['metadata']['method']}")

        output_data["melodies"][melody_name] = melody_variations

    # Save to JSON file
    output_path = 'output/variations.json'
    os.makedirs('output', exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)
    print(f"\nSaved to: {output_path}")
    print(f"Processed: {len(output_data['melodies'])} melodies")

    # Show example structure
    print("\nExample output structure:")
    print(json.dumps({
        "melodies": {
            "melody_name": {
                "original": {
                    "layer1": "..."
                },
                "variations": {
                    "var_01_transpose_up": {
                        "method": "Transpose +3 semitones",
                        "layer1": {
                            "metadata": {"durationType": "...", "totalDuration": "..."},
                            "notes": [{"midi": 60, "vel": 0.7, "dur": 0.5}],
                            "timing": "[...]"
                        }
                    }
                }
            }
        }
    }, indent=2))

if __name__ == "__main__":
    main()
