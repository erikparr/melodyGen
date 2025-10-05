from typing import List, Dict, Optional
from music21 import stream, note, analysis, key as m21_key
from scale_utils import get_scale_intervals

class MelodyValidator:
    """
    Validate melodic variations against musical constraints.
    Implements constraint checking from proposal v2.0 Tier 1.
    """

    def __init__(self, scale_type: str, root_note: str):
        self.scale_type = scale_type
        self.root_note = root_note
        self.scale_intervals = get_scale_intervals(scale_type)

    def validate_all(self, melody_notes: List[Dict],
                    check_key: bool = True,
                    check_cadence: bool = True,
                    check_range: bool = True,
                    reference_range: Optional[tuple] = None) -> Dict:
        """
        Run all validation checks on a melody.

        Args:
            melody_notes: List of note dicts
            check_key: Whether to validate key membership
            check_cadence: Whether to validate cadential patterns
            check_range: Whether to validate pitch range
            reference_range: (min_midi, max_midi) for range check

        Returns:
            Dict with validation results and pass/fail for each check
        """
        results = {
            'passed': False,
            'checks': {}
        }

        if not melody_notes:
            results['checks']['empty_melody'] = {'passed': False, 'message': 'Empty melody'}
            return results

        # Key check
        if check_key:
            key_result = self.check_key_membership(melody_notes)
            results['checks']['key_membership'] = key_result

        # Cadence check
        if check_cadence:
            cadence_result = self.check_cadence(melody_notes)
            results['checks']['cadence'] = cadence_result

        # Range check
        if check_range:
            range_result = self.check_range(melody_notes, reference_range)
            results['checks']['range'] = range_result

        # Rhythm coherence check
        rhythm_result = self.check_rhythm_coherence(melody_notes)
        results['checks']['rhythm_coherence'] = rhythm_result

        # Overall pass: all checked items must pass
        all_passed = all(
            check['passed']
            for check in results['checks'].values()
        )

        results['passed'] = all_passed

        return results

    def check_key_membership(self, melody_notes: List[Dict]) -> Dict:
        """
        Check if melody notes belong to the specified key/scale.

        Returns:
            Dict with passed (bool) and details
        """
        if not melody_notes:
            return {'passed': False, 'message': 'Empty melody'}

        # Get scale pitch classes
        scale_pc = set(self.scale_intervals)

        # Convert root note to pitch class
        from music21 import pitch
        root_pitch = pitch.Pitch(self.root_note)
        root_pc = root_pitch.pitchClass

        # Check each note
        non_scale_notes = []
        for i, n in enumerate(melody_notes):
            midi = n['midi']
            note_pc = midi % 12

            # Calculate interval from root
            interval = (note_pc - root_pc) % 12

            if interval not in scale_pc:
                non_scale_notes.append({
                    'index': i,
                    'midi': midi,
                    'interval_from_root': interval
                })

        # Pass if >= 90% of notes are in scale
        in_scale_count = len(melody_notes) - len(non_scale_notes)
        percentage = (in_scale_count / len(melody_notes)) * 100

        passed = percentage >= 90

        return {
            'passed': passed,
            'in_scale_percentage': round(percentage, 2),
            'in_scale_count': in_scale_count,
            'total_notes': len(melody_notes),
            'non_scale_notes': non_scale_notes[:5]  # Limit to first 5 violations
        }

    def check_cadence(self, melody_notes: List[Dict]) -> Dict:
        """
        Check if melody has valid cadential patterns.

        Valid cadences (in scale degrees from root):
        - 7 → 1 (leading tone to tonic)
        - 2 → 1 (supertonic to tonic)
        - 5 → 1 (dominant to tonic)
        - 4 → 1 (subdominant to tonic)

        Returns:
            Dict with passed (bool) and cadence type
        """
        if len(melody_notes) < 2:
            return {'passed': False, 'message': 'Melody too short for cadence'}

        # Get last 2-4 notes for cadence detection
        cadence_notes = melody_notes[-4:] if len(melody_notes) >= 4 else melody_notes[-2:]

        # Convert to scale degrees
        scale_degrees = [self._get_scale_degree(n['midi']) for n in cadence_notes]

        # Check for valid cadential patterns
        last_two = scale_degrees[-2:]

        # Valid ending patterns
        valid_cadences = [
            ([7, 1], 'Leading tone to tonic'),
            ([2, 1], 'Supertonic to tonic'),
            ([5, 1], 'Dominant to tonic'),
            ([4, 1], 'Subdominant to tonic'),
            ([1, 1], 'Tonic to tonic'),  # Acceptable
        ]

        for pattern, description in valid_cadences:
            if last_two == pattern:
                return {
                    'passed': True,
                    'cadence_type': description,
                    'scale_degrees': scale_degrees
                }

        # Check if at least ends on tonic
        if last_two[-1] == 1:
            return {
                'passed': True,
                'cadence_type': 'Ends on tonic',
                'scale_degrees': scale_degrees
            }

        return {
            'passed': False,
            'cadence_type': 'No valid cadence',
            'scale_degrees': scale_degrees,
            'last_interval': last_two
        }

    def check_range(self, melody_notes: List[Dict],
                   reference_range: Optional[tuple] = None) -> Dict:
        """
        Check if melody stays within acceptable pitch range.

        Args:
            melody_notes: Notes to check
            reference_range: (min_midi, max_midi) or None for default (C3-C6)

        Returns:
            Dict with passed (bool) and range info
        """
        if not melody_notes:
            return {'passed': False, 'message': 'Empty melody'}

        pitches = [n['midi'] for n in melody_notes]
        min_pitch = min(pitches)
        max_pitch = max(pitches)

        # Use reference range or default
        if reference_range:
            min_allowed, max_allowed = reference_range
        else:
            min_allowed = 48  # C3
            max_allowed = 84  # C6

        # Check if within bounds
        within_bounds = min_pitch >= min_allowed and max_pitch <= max_allowed

        return {
            'passed': within_bounds,
            'melody_range': {
                'lowest': min_pitch,
                'highest': max_pitch,
                'span': max_pitch - min_pitch
            },
            'reference_range': {
                'lowest': min_allowed,
                'highest': max_allowed
            },
            'violations': {
                'below_minimum': min_pitch < min_allowed,
                'above_maximum': max_pitch > max_allowed
            }
        }

    def check_rhythm_coherence(self, melody_notes: List[Dict]) -> Dict:
        """
        Check for rhythmic coherence.

        Failures:
        - More than 50% rest density
        - Excessive very short notes (orphaned 32nd notes)

        Returns:
            Dict with passed (bool) and rhythm analysis
        """
        if not melody_notes:
            return {'passed': False, 'message': 'Empty melody'}

        # Calculate total duration
        start_time = melody_notes[0]['time']
        end_time = melody_notes[-1]['time'] + melody_notes[-1]['duration']
        total_time = end_time - start_time

        # Calculate sounding time
        sounding_time = sum(n['duration'] for n in melody_notes)

        # Rest density
        rest_time = total_time - sounding_time
        rest_density = rest_time / total_time if total_time > 0 else 0

        # Check for very short notes (< 0.1 seconds)
        very_short_notes = [n for n in melody_notes if n['duration'] < 0.1]
        short_note_ratio = len(very_short_notes) / len(melody_notes)

        # Pass criteria
        rest_ok = rest_density <= 0.5
        short_notes_ok = short_note_ratio <= 0.3

        passed = rest_ok and short_notes_ok

        return {
            'passed': passed,
            'rest_density': round(rest_density, 3),
            'short_note_ratio': round(short_note_ratio, 3),
            'total_notes': len(melody_notes),
            'very_short_notes_count': len(very_short_notes),
            'checks': {
                'rest_density_ok': rest_ok,
                'short_notes_ok': short_notes_ok
            }
        }

    def _get_scale_degree(self, midi_note: int) -> int:
        """
        Get scale degree (1-7) for a MIDI note in the current key.
        """
        from music21 import pitch

        note_pc = midi_note % 12
        root_pitch = pitch.Pitch(self.root_note)
        root_pc = root_pitch.pitchClass

        # Calculate interval from root
        interval = (note_pc - root_pc) % 12

        # Find closest scale degree
        for i, scale_interval in enumerate(self.scale_intervals):
            if scale_interval == interval:
                return (i % 7) + 1  # Return 1-7

        # Not in scale - return closest
        closest = min(self.scale_intervals, key=lambda x: abs(x - interval))
        idx = self.scale_intervals.index(closest)
        return (idx % 7) + 1

    def filter_valid_variations(self, variations: List[Dict],
                               reference_range: Optional[tuple] = None) -> List[Dict]:
        """
        Filter list of variations to only those passing all constraints.

        Args:
            variations: List of variation dicts (with 'notes' key)
            reference_range: Optional pitch range constraint

        Returns:
            Filtered list of variations
        """
        valid = []

        for variation in variations:
            notes = variation.get('notes', [])
            validation = self.validate_all(notes, reference_range=reference_range)

            if validation['passed']:
                # Add validation metadata
                variation['validation'] = validation
                valid.append(variation)

        return valid
