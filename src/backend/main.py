from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict
from music21 import stream, note, tempo, meter, duration
import json
import tempfile
import os

from transformations import MusicTransformer
from variations import VariationGenerator
from interpolate import MelodyInterpolator
from constraints import MelodyValidator

app = FastAPI(title="MelodyGen API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models

class NoteModel(BaseModel):
    midi: int
    time: float
    duration: float
    velocity: float = 0.7

class VariationRequest(BaseModel):
    notes: List[NoteModel]
    scale_type: str = "major"
    root_note: str = "C"
    count: int = 10
    variation_types: Optional[List[str]] = None
    apply_constraints: bool = True
    reference_range: Optional[List[int]] = None  # [min_midi, max_midi]

class InterpolateRequest(BaseModel):
    melody_a: List[NoteModel]
    melody_b: List[NoteModel]
    scale_type: str = "major"
    root_note: str = "C"
    steps: int = 5
    method: str = "dtw"  # "dtw", "contour", or "feature"

class ValidateRequest(BaseModel):
    notes: List[NoteModel]
    scale_type: str = "major"
    root_note: str = "C"
    check_key: bool = True
    check_cadence: bool = True
    check_range: bool = True
    reference_range: Optional[List[int]] = None

# Endpoints

@app.get("/")
def read_root():
    return {
        "message": "MelodyGen API",
        "version": "1.0.0",
        "endpoints": {
            "variations": "/variation/generate",
            "interpolation": "/variation/interpolate",
            "validation": "/variation/validate",
            "export": "/variation/export-midi"
        }
    }

@app.post("/variation/generate")
def generate_variations(request: VariationRequest):
    """
    Generate multiple melodic variations from a seed melody.

    Returns variations with metadata and optional constraint filtering.
    """
    try:
        # Convert Pydantic models to dicts
        seed_notes = [note.dict() for note in request.notes]

        # Create generator
        generator = VariationGenerator(request.scale_type, request.root_note)

        # Generate variations
        variations = generator.generate_batch(
            seed_notes,
            count=request.count,
            variation_types=request.variation_types
        )

        # Apply constraints if requested
        if request.apply_constraints:
            validator = MelodyValidator(request.scale_type, request.root_note)

            reference_range = tuple(request.reference_range) if request.reference_range else None
            variations = validator.filter_valid_variations(variations, reference_range)

        # Calculate statistics
        stats = generator.get_variation_statistics(variations)

        return {
            "success": True,
            "variations": variations,
            "statistics": stats,
            "seed_info": {
                "note_count": len(seed_notes),
                "scale": request.scale_type,
                "key": request.root_note
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/variation/interpolate")
def interpolate_melodies(request: InterpolateRequest):
    """
    Interpolate between two melodies using DTW, contour, or feature-based methods.

    Returns a sequence of intermediate melodies.
    """
    try:
        # Convert to dicts
        melody_a = [note.dict() for note in request.melody_a]
        melody_b = [note.dict() for note in request.melody_b]

        # Create interpolator
        interpolator = MelodyInterpolator(request.scale_type, request.root_note)

        # Perform interpolation
        if request.method == "dtw":
            interpolated = interpolator.dtw_interpolate(melody_a, melody_b, request.steps)
        elif request.method == "contour":
            interpolated = interpolator.contour_interpolate(melody_a, melody_b, request.steps)
        elif request.method == "feature":
            interpolated = interpolator.feature_interpolate(melody_a, melody_b, request.steps)
        else:
            return {"success": False, "error": f"Unknown interpolation method: {request.method}"}

        return {
            "success": True,
            "interpolated_melodies": interpolated,
            "method": request.method,
            "steps": request.steps,
            "total_melodies": len(interpolated)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/variation/validate")
def validate_melody(request: ValidateRequest):
    """
    Validate a melody against musical constraints.

    Checks: key membership, cadence, range, rhythm coherence.
    """
    try:
        notes = [note.dict() for note in request.notes]

        validator = MelodyValidator(request.scale_type, request.root_note)

        reference_range = tuple(request.reference_range) if request.reference_range else None

        validation_result = validator.validate_all(
            notes,
            check_key=request.check_key,
            check_cadence=request.check_cadence,
            check_range=request.check_range,
            reference_range=reference_range
        )

        return {
            "success": True,
            "validation": validation_result
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/variation/export-midi")
def export_variation_to_midi(notes: List[NoteModel]):
    """
    Export a melody variation to MIDI file.

    Returns MIDI file as downloadable response.
    """
    try:
        # Create stream
        s = stream.Stream()
        s.append(tempo.TempoIndication(number=120))
        s.append(meter.TimeSignature('4/4'))

        # Add notes
        for note_data in notes:
            n = note.Note(note_data.midi)
            n.duration = duration.Duration(quarterLength=note_data.duration * 2)
            n.offset = note_data.time * 2
            n.volume.velocity = int(note_data.velocity * 127)
            s.insert(n.offset, n)

        # Write to MIDI
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp_file:
            s.write('midi', fp=tmp_file.name)
            tmp_file.flush()
            with open(tmp_file.name, 'rb') as f:
                midi_bytes = f.read()
            os.unlink(tmp_file.name)

        return Response(
            content=midi_bytes,
            media_type="audio/midi",
            headers={"Content-Disposition": "attachment; filename=variation.mid"}
        )

    except Exception as e:
        return {"error": str(e)}

@app.post("/variation/import-midi")
async def import_midi_seed(file: UploadFile = File(...)):
    """
    Import MIDI file and extract melody for use as seed.

    Returns parsed note data.
    """
    try:
        if not file.filename.endswith(('.mid', '.midi')):
            return {"success": False, "error": "Invalid file type. Please upload a MIDI file."}

        import mido

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_path = tmp_file.name

        try:
            # Parse MIDI with mido
            mid = mido.MidiFile(tmp_path)

            # Get tempo
            tempo_value = 500000  # Default 120 BPM
            for msg in mid.tracks[0]:
                if msg.type == 'set_tempo':
                    tempo_value = msg.tempo
                    break

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

            os.unlink(tmp_path)

            notes.sort(key=lambda n: n['time'])

            return {
                "success": True,
                "notes": notes,
                "note_count": len(notes),
                "filename": file.filename
            }

        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise e

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
