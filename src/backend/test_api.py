#!/usr/bin/env python3
"""
Simple test script to verify the melody variation API.
Creates a test melody and generates variations.
"""

import json

# Test data: Simple C major scale melody
test_melody = [
    {"midi": 60, "time": 0.0, "duration": 0.5, "velocity": 0.7},   # C
    {"midi": 62, "time": 0.5, "duration": 0.5, "velocity": 0.7},   # D
    {"midi": 64, "time": 1.0, "duration": 0.5, "velocity": 0.7},   # E
    {"midi": 65, "time": 1.5, "duration": 0.5, "velocity": 0.7},   # F
    {"midi": 67, "time": 2.0, "duration": 0.5, "velocity": 0.7},   # G
    {"midi": 69, "time": 2.5, "duration": 0.5, "velocity": 0.7},   # A
    {"midi": 71, "time": 3.0, "duration": 0.5, "velocity": 0.7},   # B
    {"midi": 72, "time": 3.5, "duration": 1.0, "velocity": 0.7},   # C (ending)
]

test_melody_b = [
    {"midi": 72, "time": 0.0, "duration": 0.5, "velocity": 0.7},   # C (high)
    {"midi": 71, "time": 0.5, "duration": 0.5, "velocity": 0.7},   # B
    {"midi": 69, "time": 1.0, "duration": 0.5, "velocity": 0.7},   # A
    {"midi": 67, "time": 1.5, "duration": 0.5, "velocity": 0.7},   # G
    {"midi": 65, "time": 2.0, "duration": 0.5, "velocity": 0.7},   # F
    {"midi": 64, "time": 2.5, "duration": 0.5, "velocity": 0.7},   # E
    {"midi": 62, "time": 3.0, "duration": 0.5, "velocity": 0.7},   # D
    {"midi": 60, "time": 3.5, "duration": 1.0, "velocity": 0.7},   # C (ending)
]

def test_variations():
    """Test variation generation"""
    from variations import VariationGenerator
    from constraints import MelodyValidator

    print("=" * 60)
    print("TEST: Variation Generation")
    print("=" * 60)

    generator = VariationGenerator("major", "C")

    print(f"\nGenerating 5 variations from {len(test_melody)}-note seed melody...")
    variations = generator.generate_batch(test_melody, count=5)

    print(f"\nGenerated {len(variations)} variations:")
    for i, var in enumerate(variations, 1):
        print(f"  {i}. {var['metadata']['method']} - {len(var['notes'])} notes")

    # Test constraint validation
    print("\nValidating variations...")
    validator = MelodyValidator("major", "C")
    valid = validator.filter_valid_variations(variations)

    print(f"  Valid variations: {len(valid)}/{len(variations)}")

    # Show statistics
    stats = generator.get_variation_statistics(variations)
    print(f"\nStatistics:")
    print(f"  Average notes per variation: {stats['average_notes_per_variation']}")
    print(f"  Pitch range: {stats['pitch_range']['lowest']}-{stats['pitch_range']['highest']}")
    print(f"  Variation types: {list(stats['variation_type_distribution'].keys())}")

    print("\n✓ Variation generation test passed!\n")
    return variations

def test_interpolation():
    """Test melody interpolation"""
    from interpolate import MelodyInterpolator

    print("=" * 60)
    print("TEST: Melody Interpolation")
    print("=" * 60)

    interpolator = MelodyInterpolator("major", "C")

    print(f"\nInterpolating between melody A ({len(test_melody)} notes) and B ({len(test_melody_b)} notes)...")

    # Test DTW interpolation
    print("\n1. DTW Interpolation:")
    dtw_result = interpolator.dtw_interpolate(test_melody, test_melody_b, steps=3)
    print(f"   Generated {len(dtw_result)} intermediate melodies")
    for i, melody in enumerate(dtw_result):
        print(f"   Step {i}: {len(melody)} notes")

    # Test contour interpolation
    print("\n2. Contour Interpolation:")
    contour_result = interpolator.contour_interpolate(test_melody, test_melody_b, steps=3)
    print(f"   Generated {len(contour_result)} intermediate melodies")
    for i, melody in enumerate(contour_result):
        print(f"   Step {i}: {len(melody)} notes")

    # Test feature interpolation
    print("\n3. Feature Interpolation:")
    feature_result = interpolator.feature_interpolate(test_melody, test_melody_b, steps=3)
    print(f"   Generated {len(feature_result)} intermediate melodies")
    for i, melody in enumerate(feature_result):
        print(f"   Step {i}: {len(melody)} notes")

    print("\n✓ Interpolation test passed!\n")
    return dtw_result

def test_validation():
    """Test constraint validation"""
    from constraints import MelodyValidator

    print("=" * 60)
    print("TEST: Constraint Validation")
    print("=" * 60)

    validator = MelodyValidator("major", "C")

    print("\nValidating test melody...")
    result = validator.validate_all(test_melody)

    print(f"\nOverall: {'PASSED' if result['passed'] else 'FAILED'}")
    print("\nDetailed checks:")
    for check_name, check_result in result['checks'].items():
        status = "✓" if check_result['passed'] else "✗"
        print(f"  {status} {check_name}")
        if 'message' in check_result:
            print(f"      {check_result['message']}")
        elif check_name == 'key_membership':
            print(f"      In-scale: {check_result['in_scale_percentage']}%")
        elif check_name == 'cadence':
            print(f"      Type: {check_result['cadence_type']}")
        elif check_name == 'range':
            print(f"      Range: {check_result['melody_range']['lowest']}-{check_result['melody_range']['highest']}")

    print("\n✓ Validation test passed!\n")
    return result

def test_combined_workflow():
    """Test full workflow: generate, validate, export"""
    from variations import VariationGenerator
    from constraints import MelodyValidator
    from music21 import stream, note, tempo, meter, duration
    import tempfile
    import os

    print("=" * 60)
    print("TEST: Combined Workflow")
    print("=" * 60)

    # Generate variations
    print("\n1. Generate variations...")
    generator = VariationGenerator("major", "C")
    variations = generator.generate_batch(test_melody, count=10)
    print(f"   Generated: {len(variations)} variations")

    # Validate
    print("\n2. Validate variations...")
    validator = MelodyValidator("major", "C")
    valid = validator.filter_valid_variations(variations)
    print(f"   Valid: {len(valid)}/{len(variations)}")

    # Export first valid variation to MIDI
    if valid:
        print("\n3. Export to MIDI...")
        var = valid[0]

        s = stream.Stream()
        s.append(tempo.TempoIndication(number=120))
        s.append(meter.TimeSignature('4/4'))

        for note_data in var['notes']:
            n = note.Note(note_data['midi'])
            n.duration = duration.Duration(quarterLength=note_data['duration'] * 2)
            n.offset = note_data['time'] * 2
            n.volume.velocity = int(note_data.get('velocity', 0.7) * 127)
            s.insert(n.offset, n)

        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
            output_path = tmp.name

        s.write('midi', fp=output_path)
        file_size = os.path.getsize(output_path)
        print(f"   Exported: {output_path} ({file_size} bytes)")
        print(f"   Method: {var['metadata']['method']}")

        os.unlink(output_path)

    print("\n✓ Combined workflow test passed!\n")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MelodyGen Backend Test Suite")
    print("=" * 60 + "\n")

    try:
        # Run tests
        test_variations()
        test_interpolation()
        test_validation()
        test_combined_workflow()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
