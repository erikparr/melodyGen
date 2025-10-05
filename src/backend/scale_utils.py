from music21 import scale, pitch, note
from typing import List, Dict, Optional

def alter_scale_degrees(base_scale, alterations: Dict[int, int]):
    """
    Create a custom scale by altering specific degrees of a base scale.
    
    Args:
        base_scale: music21 scale object (e.g., scale.PhrygianScale('C'))
        alterations: dict {degree (1-7): semitone delta}
    
    Returns:
        scale.ConcreteScale with the alterations applied
    """
    tonic = base_scale.tonic or pitch.Pitch('C')
    # Get one octave of pitches (drop duplicate octave note)
    one_octave = base_scale.getPitches(tonic, tonic.transpose('P8'))[:-1]
    
    # Apply alterations
    new_pitches = []
    for i, p in enumerate(one_octave):
        degree = i + 1
        if degree in alterations:
            new_pitches.append(p.transpose(alterations[degree]))
        else:
            new_pitches.append(p)
    
    return scale.ConcreteScale(pitches=new_pitches)

def get_scale_intervals(scale_type: str) -> List[int]:
    """
    Get the semitone intervals for a given scale type.
    Includes standard scales and custom scales like Phrygian Dominant.
    
    Returns:
        List of semitone intervals from root
    """
    standard_scales = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "harmonic minor": [0, 2, 3, 5, 7, 8, 11],
        "melodic minor": [0, 2, 3, 5, 7, 9, 11],
        "pentatonic": [0, 2, 4, 7, 9],
        "minor pentatonic": [0, 3, 5, 7, 10],
        "blues": [0, 3, 5, 6, 7, 10],
        "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        "whole tone": [0, 2, 4, 6, 8, 10],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "aeolian": [0, 2, 3, 5, 7, 8, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
        # Custom scales
        "phrygian dominant": [0, 1, 4, 5, 7, 8, 10]  # Phrygian with raised 3rd
    }
    
    return standard_scales.get(scale_type, standard_scales["major"])

def create_custom_scale(root_note: str, octave: int, scale_type: str) -> Optional[scale.ConcreteScale]:
    """
    Create a custom scale using either standard intervals or music21 alterations.
    
    Args:
        root_note: Root note name (e.g., 'C', 'F#')
        octave: Octave number
        scale_type: Scale type name
    
    Returns:
        scale.ConcreteScale object or None if creation fails
    """
    if scale_type == "phrygian dominant":
        # Create Phrygian Dominant by altering Phrygian scale
        base_scale = scale.PhrygianScale(f'{root_note}{octave}')
        # Raise the 3rd degree by 1 semitone
        return alter_scale_degrees(base_scale, {3: 1})
    
    # For other custom scales, we can add more cases here
    return None

def generate_scale_notes(root_note: str, octave: int, scale_type: str, num_notes: int = 8) -> List[Dict[str, any]]:
    """
    Generate notes for a given scale, supporting both standard and custom scales.
    
    Returns:
        List of dicts with 'midi' and 'pitch_name' for each note
    """
    intervals = get_scale_intervals(scale_type)
    
    # Convert root note to MIDI number
    root_note_obj = note.Note(f"{root_note}{octave}")
    root_midi = root_note_obj.pitch.midi
    
    notes = []
    for i in range(num_notes):
        scale_degree = i % len(intervals)
        octave_offset = i // len(intervals)
        
        midi_note = root_midi + intervals[scale_degree] + (octave_offset * 12)
        note_obj = note.Note(midi=midi_note)
        
        notes.append({
            'midi': midi_note,
            'pitch_name': note_obj.nameWithOctave
        })
    
    return notes