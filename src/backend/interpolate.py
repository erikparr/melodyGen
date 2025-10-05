from typing import List, Dict, Optional
import numpy as np
from scale_utils import get_scale_intervals

class MelodyInterpolator:
    """
    Interpolate between two melodies using DTW alignment and contour morphing.
    Implements Tier 1 interpolation methods from proposal v2.0.
    """

    def __init__(self, scale_type: str, root_note: str):
        self.scale_type = scale_type
        self.root_note = root_note
        self.scale_intervals = get_scale_intervals(scale_type)

    def dtw_interpolate(self, melody_a: List[Dict], melody_b: List[Dict],
                       steps: int = 5) -> List[List[Dict]]:
        """
        Interpolate between two melodies using Dynamic Time Warping alignment.

        Args:
            melody_a: First melody (note dicts)
            melody_b: Second melody (note dicts)
            steps: Number of intermediate steps (excluding A and B)

        Returns:
            List of interpolated melodies (including A and B)
        """
        if not melody_a or not melody_b:
            return []

        # Extract pitch sequences
        pitches_a = [n['midi'] for n in melody_a]
        pitches_b = [n['midi'] for n in melody_b]

        # Compute DTW alignment
        alignment = self._dtw_align(pitches_a, pitches_b)

        # Generate interpolated sequences
        interpolated = []

        # Include original melody A
        interpolated.append(melody_a)

        # Generate intermediate steps
        for step in range(1, steps + 1):
            t = step / (steps + 1)  # Interpolation factor (0 to 1)
            interp_melody = self._interpolate_aligned(melody_a, melody_b, alignment, t)
            interpolated.append(interp_melody)

        # Include original melody B
        interpolated.append(melody_b)

        return interpolated

    def contour_interpolate(self, melody_a: List[Dict], melody_b: List[Dict],
                           steps: int = 5) -> List[List[Dict]]:
        """
        Interpolate using normalized contour space.

        Args:
            melody_a: First melody
            melody_b: Second melody
            steps: Number of intermediate steps

        Returns:
            List of interpolated melodies
        """
        if not melody_a or not melody_b:
            return []

        # Normalize contours to 0-1 range
        contour_a = self._normalize_contour([n['midi'] for n in melody_a])
        contour_b = self._normalize_contour([n['midi'] for n in melody_b])

        # Make contours same length (use longer length)
        max_len = max(len(contour_a), len(contour_b))
        contour_a = self._resample_contour(contour_a, max_len)
        contour_b = self._resample_contour(contour_b, max_len)

        interpolated = []
        interpolated.append(melody_a)

        # Generate intermediate contours
        for step in range(1, steps + 1):
            t = step / (steps + 1)
            interp_contour = [(1 - t) * a + t * b for a, b in zip(contour_a, contour_b)]

            # Convert back to MIDI pitches with scale snapping
            interp_melody = self._contour_to_melody(interp_contour, melody_a, melody_b, t)
            interpolated.append(interp_melody)

        interpolated.append(melody_b)

        return interpolated

    def feature_interpolate(self, melody_a: List[Dict], melody_b: List[Dict],
                           steps: int = 5) -> List[List[Dict]]:
        """
        Interpolate by blending musical features.

        Features: mean pitch, pitch variance, rhythm density, step/leap ratio

        Args:
            melody_a: First melody
            melody_b: Second melody
            steps: Number of intermediate steps

        Returns:
            List of interpolated melodies
        """
        if not melody_a or not melody_b:
            return []

        # Extract features
        features_a = self._extract_features(melody_a)
        features_b = self._extract_features(melody_b)

        interpolated = []
        interpolated.append(melody_a)

        for step in range(1, steps + 1):
            t = step / (steps + 1)

            # Interpolate features
            target_features = {
                'mean_pitch': (1 - t) * features_a['mean_pitch'] + t * features_b['mean_pitch'],
                'pitch_variance': (1 - t) * features_a['pitch_variance'] + t * features_b['pitch_variance'],
                'rhythm_density': (1 - t) * features_a['rhythm_density'] + t * features_b['rhythm_density'],
                'step_ratio': (1 - t) * features_a['step_ratio'] + t * features_b['step_ratio']
            }

            # Synthesize melody matching target features
            interp_melody = self._synthesize_from_features(target_features, melody_a, melody_b, t)
            interpolated.append(interp_melody)

        interpolated.append(melody_b)

        return interpolated

    # Helper methods

    def _dtw_align(self, seq_a: List[int], seq_b: List[int]) -> List[tuple]:
        """
        Compute DTW alignment between two sequences.

        Returns:
            List of (index_a, index_b) alignment pairs
        """
        n, m = len(seq_a), len(seq_b)

        # Initialize cost matrix
        cost = np.full((n + 1, m + 1), np.inf)
        cost[0, 0] = 0

        # Fill cost matrix
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                distance = abs(seq_a[i - 1] - seq_b[j - 1])
                cost[i, j] = distance + min(cost[i - 1, j],    # insertion
                                           cost[i, j - 1],    # deletion
                                           cost[i - 1, j - 1]) # match

        # Backtrack to find alignment
        alignment = []
        i, j = n, m

        while i > 0 and j > 0:
            alignment.append((i - 1, j - 1))

            # Find minimum predecessor
            candidates = [
                (cost[i - 1, j - 1], (i - 1, j - 1)),
                (cost[i - 1, j], (i - 1, j)),
                (cost[i, j - 1], (i, j - 1))
            ]
            _, (i, j) = min(candidates)

        alignment.reverse()
        return alignment

    def _interpolate_aligned(self, melody_a: List[Dict], melody_b: List[Dict],
                            alignment: List[tuple], t: float) -> List[Dict]:
        """
        Interpolate aligned melodies at factor t.
        """
        interp_melody = []

        for idx_a, idx_b in alignment:
            note_a = melody_a[idx_a]
            note_b = melody_b[idx_b]

            # Interpolate pitch
            pitch = int((1 - t) * note_a['midi'] + t * note_b['midi'])

            # Snap to scale
            pitch = self._snap_to_scale(pitch)

            # Interpolate other properties
            interp_note = {
                'midi': pitch,
                'time': (1 - t) * note_a['time'] + t * note_b['time'],
                'duration': (1 - t) * note_a['duration'] + t * note_b['duration'],
                'velocity': (1 - t) * note_a.get('velocity', 0.7) + t * note_b.get('velocity', 0.7)
            }

            interp_melody.append(interp_note)

        return interp_melody

    def _normalize_contour(self, pitches: List[int]) -> List[float]:
        """
        Normalize pitch sequence to 0-1 range.
        """
        if not pitches:
            return []

        min_pitch = min(pitches)
        max_pitch = max(pitches)

        if max_pitch == min_pitch:
            return [0.5] * len(pitches)

        return [(p - min_pitch) / (max_pitch - min_pitch) for p in pitches]

    def _resample_contour(self, contour: List[float], target_length: int) -> List[float]:
        """
        Resample contour to target length using linear interpolation.
        """
        if len(contour) == target_length:
            return contour

        if len(contour) == 0:
            return [0.5] * target_length

        # Linear interpolation
        indices = np.linspace(0, len(contour) - 1, target_length)
        resampled = []

        for idx in indices:
            low = int(np.floor(idx))
            high = min(int(np.ceil(idx)), len(contour) - 1)
            frac = idx - low

            if low == high:
                resampled.append(contour[low])
            else:
                value = (1 - frac) * contour[low] + frac * contour[high]
                resampled.append(value)

        return resampled

    def _contour_to_melody(self, contour: List[float], melody_a: List[Dict],
                          melody_b: List[Dict], t: float) -> List[Dict]:
        """
        Convert normalized contour back to melody with scale snapping.
        """
        # Determine pitch range from interpolated A/B ranges
        range_a = (min(n['midi'] for n in melody_a), max(n['midi'] for n in melody_a))
        range_b = (min(n['midi'] for n in melody_b), max(n['midi'] for n in melody_b))

        min_pitch = int((1 - t) * range_a[0] + t * range_b[0])
        max_pitch = int((1 - t) * range_a[1] + t * range_b[1])

        melody = []
        for i, c in enumerate(contour):
            # Map contour value to pitch range
            pitch = int(min_pitch + c * (max_pitch - min_pitch))
            pitch = self._snap_to_scale(pitch)

            # Interpolate timing from A/B
            idx_a = min(i, len(melody_a) - 1)
            idx_b = min(i, len(melody_b) - 1)

            note = {
                'midi': pitch,
                'time': (1 - t) * melody_a[idx_a]['time'] + t * melody_b[idx_b]['time'],
                'duration': (1 - t) * melody_a[idx_a]['duration'] + t * melody_b[idx_b]['duration'],
                'velocity': 0.7
            }

            melody.append(note)

        return melody

    def _extract_features(self, melody: List[Dict]) -> Dict:
        """
        Extract musical features from melody.
        """
        pitches = [n['midi'] for n in melody]

        # Mean pitch
        mean_pitch = np.mean(pitches)

        # Pitch variance
        pitch_variance = np.var(pitches)

        # Rhythm density (notes per second)
        total_duration = melody[-1]['time'] + melody[-1]['duration'] - melody[0]['time']
        rhythm_density = len(melody) / total_duration if total_duration > 0 else 0

        # Step/leap ratio
        intervals = [abs(pitches[i] - pitches[i - 1]) for i in range(1, len(pitches))]
        steps = sum(1 for i in intervals if i <= 2)
        step_ratio = steps / len(intervals) if intervals else 0.5

        return {
            'mean_pitch': mean_pitch,
            'pitch_variance': pitch_variance,
            'rhythm_density': rhythm_density,
            'step_ratio': step_ratio
        }

    def _synthesize_from_features(self, target_features: Dict, melody_a: List[Dict],
                                 melody_b: List[Dict], t: float) -> List[Dict]:
        """
        Synthesize melody matching target features.

        This is a simplified approach: blend A and B, then adjust to match features.
        """
        # Start with simple blend
        length = int((1 - t) * len(melody_a) + t * len(melody_b))
        melody = []

        for i in range(length):
            idx_a = min(int(i * len(melody_a) / length), len(melody_a) - 1)
            idx_b = min(int(i * len(melody_b) / length), len(melody_b) - 1)

            pitch = int((1 - t) * melody_a[idx_a]['midi'] + t * melody_b[idx_b]['midi'])

            # Adjust pitch toward target mean
            current_mean = target_features['mean_pitch']
            pitch = int(pitch + (current_mean - pitch) * 0.3)

            pitch = self._snap_to_scale(pitch)

            note = {
                'midi': pitch,
                'time': i / target_features['rhythm_density'],
                'duration': 0.5,  # Simplified
                'velocity': 0.7
            }

            melody.append(note)

        return melody

    def _snap_to_scale(self, midi_note: int) -> int:
        """
        Snap MIDI note to nearest note in the scale.
        """
        note_class = midi_note % 12
        octave = midi_note // 12

        # Find closest scale degree
        scale_degrees = list(set(self.scale_intervals))
        closest_degree = min(scale_degrees, key=lambda x: abs(x - note_class))

        # Reconstruct MIDI note
        result = octave * 12 + closest_degree

        # Handle edge cases
        if abs(result - midi_note) > 6:
            if result < midi_note:
                result += 12
            else:
                result -= 12

        return result
