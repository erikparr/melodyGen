from music21 import stream, note, interval, analysis, pitch
from typing import List, Dict, Optional
from scale_utils import get_scale_intervals
import random

class MusicTransformer:
    def __init__(self, scale_type: str, root_note: str):
        self.scale_type = scale_type
        self.root_note = root_note
        self.scale_intervals = get_scale_intervals(scale_type)
        self.root_pitch = pitch.Pitch(root_note)
        
    def analyze_melody(self, notes: List[Dict]) -> Dict:
        """Analyze melody for intervals, contour, and patterns"""
        if not notes:
            return {
                'intervals': [],
                'contour': [],
                'scale_degrees': [],
                'phrases': []
            }
            
        # Calculate intervals
        intervals = []
        for i in range(1, len(notes)):
            intervals.append(notes[i]['midi'] - notes[i-1]['midi'])
            
        # Analyze contour (up/down/same)
        contour = []
        for interv in intervals:
            if interv > 0:
                contour.append('up')
            elif interv < 0:
                contour.append('down')
            else:
                contour.append('same')
                
        # Calculate scale degrees
        scale_degrees = []
        for note_data in notes:
            degree = self.get_scale_degree(note_data['midi'])
            scale_degrees.append(degree)
            
        # Detect phrases (simplified - based on time gaps)
        phrases = self.detect_phrases(notes)
        
        return {
            'intervals': intervals,
            'contour': contour,
            'scale_degrees': scale_degrees,
            'phrases': phrases,
            'range': {
                'lowest': min(n['midi'] for n in notes),
                'highest': max(n['midi'] for n in notes),
                'span': max(n['midi'] for n in notes) - min(n['midi'] for n in notes)
            }
        }
        
    def counter_melody(self, notes: List[Dict], style: str = "contrary") -> List[Dict]:
        """Generate counter melody using contrary/parallel/oblique motion"""
        if not notes:
            return []
            
        result = []
        
        for i, note_data in enumerate(notes):
            if style == "contrary":
                # Move in opposite direction
                if i > 0:
                    prev_motion = note_data['midi'] - notes[i-1]['midi']
                    if prev_motion > 0:  # Melody went up
                        # Counter melody goes down - try 3rd, 5th, or 6th below
                        interval = self.find_diatonic_interval(note_data['midi'], -3)
                    elif prev_motion < 0:  # Melody went down
                        # Counter melody goes up
                        interval = self.find_diatonic_interval(note_data['midi'], 3)
                    else:  # No motion
                        # Move to nearest consonant interval
                        interval = self.find_diatonic_interval(note_data['midi'], -5)
                else:
                    # Start a third below
                    interval = self.find_diatonic_interval(note_data['midi'], -3)
                    
                counter_pitch = note_data['midi'] + interval
                
            elif style == "parallel":
                # Move in same direction at fixed interval
                counter_pitch = note_data['midi'] + self.find_diatonic_interval(note_data['midi'], -3)
                
            elif style == "oblique":
                # One voice stays same while other moves
                if i % 2 == 0:
                    counter_pitch = notes[0]['midi']  # Pedal tone
                else:
                    counter_pitch = note_data['midi'] + self.find_diatonic_interval(note_data['midi'], -5)
                    
            else:  # mixed
                # Combine different motion types
                if i % 4 == 0:
                    style_temp = "contrary"
                elif i % 4 == 1:
                    style_temp = "parallel"
                else:
                    style_temp = "oblique"
                return self.counter_melody([note_data], style_temp)[0:1] + self.counter_melody(notes[i+1:], style)
                
            # Ensure reasonable range
            if counter_pitch < 36:  # C2
                counter_pitch += 12
            elif counter_pitch > 96:  # C7
                counter_pitch -= 12
                
            result.append({
                **note_data,
                'midi': counter_pitch,
                'velocity': note_data.get('velocity', 0.7) * 0.8
            })
            
        return result
        
    def harmonize(self, notes: List[Dict], interval_degree: int = 3) -> List[Dict]:
        """Create harmony line at specified diatonic interval"""
        harmonized = []
        
        for note_data in notes:
            # Find the diatonic interval in the scale
            harmony_pitch = note_data['midi'] + self.find_diatonic_interval(note_data['midi'], interval_degree)
            
            # Keep in reasonable range
            while harmony_pitch > 96:  # If too high
                harmony_pitch -= 12
            while harmony_pitch < 36:  # If too low
                harmony_pitch += 12
                
            harmonized.append({
                **note_data,
                'midi': harmony_pitch,
                'velocity': note_data.get('velocity', 0.7) * 0.85
            })
            
        return harmonized
        
    def transpose(self, notes: List[Dict], semitones: int) -> List[Dict]:
        """Transpose melody by semitones"""
        return [{
            **note,
            'midi': note['midi'] + semitones
        } for note in notes]
        
    def transpose_diatonic(self, notes: List[Dict], scale_steps: int) -> List[Dict]:
        """Transpose melody by scale degrees (diatonic transposition)"""
        transposed = []
        
        for note_data in notes:
            new_pitch = self.transpose_by_scale_degree(note_data['midi'], scale_steps)
            transposed.append({
                **note_data,
                'midi': new_pitch
            })
            
        return transposed
        
    def invert(self, notes: List[Dict], axis: str = "center") -> List[Dict]:
        """Melodic inversion around axis point"""
        if not notes:
            return []
            
        # Determine axis point
        if axis == "center":
            lowest = min(n['midi'] for n in notes)
            highest = max(n['midi'] for n in notes)
            axis_pitch = (lowest + highest) // 2
        elif axis == "first-note":
            axis_pitch = notes[0]['midi']
        elif axis == "last-note":
            axis_pitch = notes[-1]['midi']
        else:
            axis_pitch = int(axis) if axis.isdigit() else notes[0]['midi']
            
        # Invert around axis
        inverted = []
        for note_data in notes:
            distance = note_data['midi'] - axis_pitch
            new_pitch = axis_pitch - distance
            
            inverted.append({
                **note_data,
                'midi': new_pitch
            })
            
        return inverted
        
    def augment(self, notes: List[Dict], factor: float = 2.0) -> List[Dict]:
        """Rhythmic augmentation - stretch timing"""
        if not notes:
            return []
            
        # Find the start time
        start_time = min(n['time'] for n in notes) if notes else 0
        
        return [{
            **note,
            'time': start_time + (note['time'] - start_time) * factor,
            'duration': note['duration'] * factor
        } for note in notes]
        
    def diminish(self, notes: List[Dict], factor: float = 0.5) -> List[Dict]:
        """Rhythmic diminution - compress timing"""
        if not notes:
            return []
            
        # Find the start time
        start_time = min(n['time'] for n in notes) if notes else 0
        
        return [{
            **note,
            'time': start_time + (note['time'] - start_time) * factor,
            'duration': note['duration'] * factor
        } for note in notes]
        
    def ornament(self, notes: List[Dict], style: str = "classical") -> List[Dict]:
        """Add melodic ornamentations"""
        result = []
        
        for i, note_data in enumerate(notes):
            if style == "classical":
                # Add turns and trills on longer notes
                if note_data['duration'] > 0.5 and random.random() < 0.3:
                    # Add a turn
                    result.extend(self.create_turn(note_data))
                else:
                    result.append(note_data)
                    
            elif style == "jazz":
                # Add grace notes and chromatic approaches
                if random.random() < 0.2 and i > 0:
                    # Add chromatic approach
                    grace = {
                        **note_data,
                        'midi': note_data['midi'] - 1,
                        'time': note_data['time'] - 0.1,
                        'duration': 0.1,
                        'velocity': note_data.get('velocity', 0.7) * 0.6
                    }
                    result.append(grace)
                result.append(note_data)
                
            elif style == "baroque":
                # Add mordents and trills
                if note_data['duration'] > 0.3 and random.random() < 0.25:
                    result.extend(self.create_mordent(note_data))
                else:
                    result.append(note_data)
                    
            else:  # minimal
                # Very sparse ornamentation
                if i == len(notes) - 1 and note_data['duration'] > 1.0:
                    # Simple ending ornament
                    result.extend(self.create_simple_ending(note_data))
                else:
                    result.append(note_data)
                    
        return result
        
    def develop(self, notes: List[Dict], method: str = "sequence") -> List[Dict]:
        """Apply melodic development techniques"""
        if not notes:
            return []
            
        if method == "sequence":
            # Repeat pattern at different scale degrees
            developed = []
            pattern_length = min(4, len(notes))
            pattern = notes[:pattern_length]
            
            # Original
            developed.extend(pattern)
            
            # Sequence up by scale steps
            for degree_offset in [2, 4, -1]:  # up 2nd, up 4th, down 2nd
                time_offset = len(developed) * 0.5
                for note_data in pattern:
                    new_pitch = self.transpose_by_scale_degree(note_data['midi'], degree_offset)
                    developed.append({
                        **note_data,
                        'midi': new_pitch,
                        'time': note_data['time'] + time_offset
                    })
                    
        elif method == "fragment":
            # Break into fragments and recombine
            fragments = self.extract_fragments(notes)
            developed = self.recombine_fragments(fragments)
            
        elif method == "extend":
            # Extend the melody with variations
            developed = notes.copy()
            # Add varied repetition
            variation = self.create_variation(notes)
            time_offset = (notes[-1]['time'] + notes[-1]['duration']) if notes else 0
            for note_data in variation:
                developed.append({
                    **note_data,
                    'time': note_data['time'] + time_offset
                })
                
        elif method == "retrograde":
            # Reverse the melody
            developed = []
            if notes:
                total_duration = notes[-1]['time'] + notes[-1]['duration']
                for note_data in reversed(notes):
                    new_time = total_duration - (note_data['time'] + note_data['duration'])
                    developed.append({
                        **note_data,
                        'time': new_time
                    })
                    
        return developed
        
    # Helper methods
    def get_scale_degree(self, midi_note: int) -> int:
        """Get scale degree of a MIDI note"""
        note_class = midi_note % 12
        root_class = self.root_pitch.pitchClass
        
        # Calculate interval from root
        interval_from_root = (note_class - root_class) % 12
        
        # Find closest scale degree
        for i, scale_interval in enumerate(self.scale_intervals):
            if scale_interval == interval_from_root:
                return i + 1
                
        # Not in scale, return closest
        closest = min(self.scale_intervals, key=lambda x: abs(x - interval_from_root))
        return self.scale_intervals.index(closest) + 1
        
    def find_diatonic_interval(self, midi_note: int, interval_steps: int) -> int:
        """Find diatonic interval (in scale steps, not semitones)"""
        current_degree = self.get_scale_degree(midi_note) - 1
        target_degree = (current_degree + interval_steps) % len(self.scale_intervals)
        
        if target_degree < 0:
            target_degree += len(self.scale_intervals)
            
        octave_adjustment = (current_degree + interval_steps) // len(self.scale_intervals)
        
        # Calculate semitone difference
        current_pos = self.scale_intervals[current_degree]
        target_pos = self.scale_intervals[target_degree]
        
        semitones = target_pos - current_pos + (octave_adjustment * 12)
        
        return semitones
        
    def transpose_by_scale_degree(self, midi_note: int, degree_offset: int) -> int:
        """Transpose by scale degrees"""
        return midi_note + self.find_diatonic_interval(midi_note, degree_offset)
        
    def detect_phrases(self, notes: List[Dict]) -> List[List[int]]:
        """Detect musical phrases based on time gaps"""
        if not notes:
            return []
            
        phrases = []
        current_phrase = [0]
        
        for i in range(1, len(notes)):
            time_gap = notes[i]['time'] - (notes[i-1]['time'] + notes[i-1]['duration'])
            
            # If gap is more than 0.5 seconds, start new phrase
            if time_gap > 0.5:
                phrases.append(current_phrase)
                current_phrase = [i]
            else:
                current_phrase.append(i)
                
        if current_phrase:
            phrases.append(current_phrase)
            
        return phrases
        
    def create_turn(self, note_data: Dict) -> List[Dict]:
        """Create a classical turn ornament"""
        result = []
        base_time = note_data['time']
        base_pitch = note_data['midi']
        
        # Upper neighbor, main note, lower neighbor, main note
        pitches = [
            base_pitch + self.find_diatonic_interval(base_pitch, 1),
            base_pitch,
            base_pitch + self.find_diatonic_interval(base_pitch, -1),
            base_pitch
        ]
        
        duration_each = note_data['duration'] / 4
        
        for i, pitch in enumerate(pitches):
            result.append({
                **note_data,
                'midi': pitch,
                'time': base_time + i * duration_each,
                'duration': duration_each,
                'velocity': note_data.get('velocity', 0.7) * (0.8 if i != 1 else 1.0)
            })
            
        return result
        
    def create_mordent(self, note_data: Dict) -> List[Dict]:
        """Create a mordent ornament"""
        result = []
        base_pitch = note_data['midi']
        
        # Quick alternation with lower neighbor
        result.append({
            **note_data,
            'duration': 0.1,
            'velocity': note_data.get('velocity', 0.7) * 0.8
        })
        
        result.append({
            **note_data,
            'midi': base_pitch + self.find_diatonic_interval(base_pitch, -1),
            'time': note_data['time'] + 0.1,
            'duration': 0.1,
            'velocity': note_data.get('velocity', 0.7) * 0.7
        })
        
        result.append({
            **note_data,
            'time': note_data['time'] + 0.2,
            'duration': note_data['duration'] - 0.2
        })
        
        return result
        
    def create_simple_ending(self, note_data: Dict) -> List[Dict]:
        """Create a simple ending ornament"""
        # Just add a gentle slide down
        return [
            note_data,
            {
                **note_data,
                'midi': note_data['midi'] - 2,
                'time': note_data['time'] + note_data['duration'],
                'duration': 0.2,
                'velocity': note_data.get('velocity', 0.7) * 0.5
            }
        ]
        
    def extract_fragments(self, notes: List[Dict], min_length: int = 2, max_length: int = 4) -> List[List[Dict]]:
        """Extract melodic fragments"""
        fragments = []
        
        for length in range(min_length, min(max_length + 1, len(notes) + 1)):
            for i in range(len(notes) - length + 1):
                fragments.append(notes[i:i + length])
                
        return fragments
        
    def recombine_fragments(self, fragments: List[List[Dict]]) -> List[Dict]:
        """Recombine fragments in interesting ways"""
        if not fragments:
            return []
            
        # Select random fragments and concatenate
        result = []
        time_offset = 0
        
        for _ in range(4):  # Create 4 fragment combinations
            if fragments:
                fragment = random.choice(fragments)
                for note_data in fragment:
                    result.append({
                        **note_data,
                        'time': note_data['time'] + time_offset
                    })
                if fragment:
                    time_offset = result[-1]['time'] + result[-1]['duration'] + 0.1
                    
        return result
        
    def create_variation(self, notes: List[Dict]) -> List[Dict]:
        """Create a variation of the melody"""
        variation = []
        
        for i, note_data in enumerate(notes):
            # Occasionally change pitches
            if random.random() < 0.3:
                # Move to nearby scale tone
                direction = random.choice([-1, 1])
                new_pitch = self.transpose_by_scale_degree(note_data['midi'], direction)
                variation.append({
                    **note_data,
                    'midi': new_pitch
                })
            else:
                variation.append(note_data.copy())
                
        return variation