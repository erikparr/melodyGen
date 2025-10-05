from typing import List, Dict, Optional, Tuple
from transformations import MusicTransformer
import random
import json
from datetime import datetime

class VariationGenerator:
    """
    Generate multiple melodic variations from a seed melody.
    Implements Tier 1 (symbolic operations) from proposal v2.0.
    """

    def __init__(self, scale_type: str, root_note: str):
        self.transformer = MusicTransformer(scale_type, root_note)
        self.scale_type = scale_type
        self.root_note = root_note

    def generate_batch(self, seed_notes: List[Dict],
                       count: int = 10,
                       variation_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Generate multiple variations from a seed melody.

        Args:
            seed_notes: List of note dicts with midi, time, duration, velocity
            count: Number of variations to generate
            variation_types: List of transformation types to use (None = all)

        Returns:
            List of variation dicts with notes and metadata
        """
        if not seed_notes:
            return []

        # Default to all variation types
        if variation_types is None:
            variation_types = [
                'transpose_up', 'transpose_down',
                'transpose_diatonic_up', 'transpose_diatonic_down',
                'invert_center', 'invert_first', 'invert_last',
                'augment', 'diminish',
                'ornament_classical', 'ornament_jazz',
                'develop_sequence', 'develop_retrograde',
                'harmonize_third', 'harmonize_fifth',
                'counter_contrary', 'counter_parallel'
            ]

        variations = []

        for i in range(count):
            # Select random variation type
            var_type = random.choice(variation_types)

            # Generate variation based on type
            if var_type == 'transpose_up':
                notes = self.transformer.transpose(seed_notes, semitones=random.randint(1, 7))
                method = f"Transpose +{notes[0]['midi'] - seed_notes[0]['midi']} semitones"

            elif var_type == 'transpose_down':
                notes = self.transformer.transpose(seed_notes, semitones=random.randint(-7, -1))
                method = f"Transpose {notes[0]['midi'] - seed_notes[0]['midi']} semitones"

            elif var_type == 'transpose_diatonic_up':
                steps = random.randint(1, 4)
                notes = self.transformer.transpose_diatonic(seed_notes, scale_steps=steps)
                method = f"Diatonic transpose +{steps} steps"

            elif var_type == 'transpose_diatonic_down':
                steps = random.randint(-4, -1)
                notes = self.transformer.transpose_diatonic(seed_notes, scale_steps=steps)
                method = f"Diatonic transpose {steps} steps"

            elif var_type == 'invert_center':
                notes = self.transformer.invert(seed_notes, axis='center')
                method = "Invert around center"

            elif var_type == 'invert_first':
                notes = self.transformer.invert(seed_notes, axis='first-note')
                method = "Invert around first note"

            elif var_type == 'invert_last':
                notes = self.transformer.invert(seed_notes, axis='last-note')
                method = "Invert around last note"

            elif var_type == 'augment':
                factor = random.choice([1.5, 2.0, 2.5])
                notes = self.transformer.augment(seed_notes, factor=factor)
                method = f"Augment ×{factor}"

            elif var_type == 'diminish':
                factor = random.choice([0.5, 0.66, 0.75])
                notes = self.transformer.diminish(seed_notes, factor=factor)
                method = f"Diminish ×{factor}"

            elif var_type == 'ornament_classical':
                notes = self.transformer.ornament(seed_notes, style='classical')
                method = "Classical ornamentation"

            elif var_type == 'ornament_jazz':
                notes = self.transformer.ornament(seed_notes, style='jazz')
                method = "Jazz ornamentation"

            elif var_type == 'develop_sequence':
                notes = self.transformer.develop(seed_notes, method='sequence')
                method = "Sequential development"

            elif var_type == 'develop_retrograde':
                notes = self.transformer.develop(seed_notes, method='retrograde')
                method = "Retrograde"

            elif var_type == 'harmonize_third':
                notes = self.transformer.harmonize(seed_notes, interval_degree=3)
                method = "Harmonize at 3rd"

            elif var_type == 'harmonize_fifth':
                notes = self.transformer.harmonize(seed_notes, interval_degree=5)
                method = "Harmonize at 5th"

            elif var_type == 'counter_contrary':
                notes = self.transformer.counter_melody(seed_notes, style='contrary')
                method = "Counter melody (contrary)"

            elif var_type == 'counter_parallel':
                notes = self.transformer.counter_melody(seed_notes, style='parallel')
                method = "Counter melody (parallel)"

            else:
                # Fallback: simple transpose
                notes = self.transformer.transpose(seed_notes, semitones=random.randint(-5, 5))
                method = "Transpose (random)"

            # Create variation record
            variation = {
                'id': f'var_{i+1}_{datetime.now().timestamp()}',
                'notes': notes,
                'metadata': {
                    'method': method,
                    'variation_type': var_type,
                    'seed_length': len(seed_notes),
                    'output_length': len(notes),
                    'scale': self.scale_type,
                    'key': self.root_note,
                    'timestamp': datetime.now().isoformat()
                }
            }

            variations.append(variation)

        return variations

    def generate_combined(self, seed_notes: List[Dict],
                         transformations: List[Tuple[str, Dict]]) -> List[Dict]:
        """
        Apply multiple transformations in sequence.

        Args:
            seed_notes: Starting melody
            transformations: List of (transform_name, params) tuples

        Returns:
            Transformed notes
        """
        notes = seed_notes.copy()

        for transform_name, params in transformations:
            if transform_name == 'transpose':
                notes = self.transformer.transpose(notes, **params)
            elif transform_name == 'transpose_diatonic':
                notes = self.transformer.transpose_diatonic(notes, **params)
            elif transform_name == 'invert':
                notes = self.transformer.invert(notes, **params)
            elif transform_name == 'augment':
                notes = self.transformer.augment(notes, **params)
            elif transform_name == 'diminish':
                notes = self.transformer.diminish(notes, **params)
            elif transform_name == 'ornament':
                notes = self.transformer.ornament(notes, **params)
            elif transform_name == 'develop':
                notes = self.transformer.develop(notes, **params)
            elif transform_name == 'harmonize':
                notes = self.transformer.harmonize(notes, **params)
            elif transform_name == 'counter_melody':
                notes = self.transformer.counter_melody(notes, **params)

        return notes

    def get_variation_statistics(self, variations: List[Dict]) -> Dict:
        """
        Calculate statistics across a set of variations.

        Args:
            variations: List of variation dicts

        Returns:
            Statistics dict
        """
        if not variations:
            return {}

        total_notes = sum(len(v['notes']) for v in variations)
        avg_notes = total_notes / len(variations)

        # Count variation types
        type_counts = {}
        for v in variations:
            var_type = v['metadata']['variation_type']
            type_counts[var_type] = type_counts.get(var_type, 0) + 1

        # Pitch range analysis
        all_pitches = []
        for v in variations:
            all_pitches.extend([n['midi'] for n in v['notes']])

        return {
            'total_variations': len(variations),
            'average_notes_per_variation': round(avg_notes, 2),
            'variation_type_distribution': type_counts,
            'pitch_range': {
                'lowest': min(all_pitches) if all_pitches else 0,
                'highest': max(all_pitches) if all_pitches else 0,
                'span': max(all_pitches) - min(all_pitches) if all_pitches else 0
            },
            'timestamp': datetime.now().isoformat()
        }
