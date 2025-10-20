from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Set
from music21 import stream, note, tempo, meter, duration
import json
import tempfile
import os
import threading
import asyncio
from pythonosc import dispatcher, osc_server

from transformations import MusicTransformer
from variations import VariationGenerator
from interpolate import MelodyInterpolator
from constraints import MelodyValidator
from services import OSCService, LoopManager, EventBroadcaster

app = FastAPI(title="MelodyGen API", version="1.0.0")

# Initialize services
osc_service = OSCService()
loop_manager = LoopManager()
event_broadcaster = EventBroadcaster()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to start background broadcaster
@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup."""
    asyncio.create_task(event_broadcaster.broadcast_pending_events())
    print("📡 Started WebSocket broadcast task")

# OSC message handler for melody completion
def handle_melody_complete(address, *args):
    """
    Handle OSC completion message from SuperCollider.
    Expected: /melody/complete [targetGroup] or /chord/complete [targetGroup]
    Accepts variable arguments since SuperCollider may send additional data.
    """
    if len(args) == 0:
        print(f"⚠️ Warning: No arguments received for {address}")
        return

    # First argument should be targetGroup (track number)
    target_group = args[0]
    print(f"✅ Completion received - Address: {address}, targetGroup: {target_group} (args: {args})")

    # Check if this targetGroup has a looping melody
    loop_data = loop_manager.get_loop(target_group)
    if loop_data:
        print(f"🔁 Re-triggering loop for targetGroup {target_group}")
        osc_service.resend_message(loop_data["address"], loop_data["payload"])

    # Store the completion event
    event_broadcaster.add_event(target_group)

# Setup OSC server to receive messages from SuperCollider
def start_osc_server():
    """Start OSC server in background thread to listen for completion messages."""
    disp = dispatcher.Dispatcher()
    disp.map("/melody/complete", handle_melody_complete)
    disp.map("/chord/complete", handle_melody_complete)  # Also handle chord completions

    server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 7001), disp)
    print("🎧 OSC Server listening on 127.0.0.1:7001 for SuperCollider completion messages")

    server.serve_forever()

# Start OSC receiver in background thread
osc_thread = threading.Thread(target=start_osc_server, daemon=True)
osc_thread.start()

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

class OSCNote(BaseModel):
    midi: int
    vel: float
    dur: float

class OSCMetadata(BaseModel):
    totalDuration: float
    noteCount: int
    name: str
    key: Optional[str] = None
    scale: Optional[str] = None

class OSCMelodyRequest(BaseModel):
    layer: int  # 1, 2, or 3
    notes: List[Dict]  # Accept raw dicts from frontend
    metadata: Dict  # Accept raw dict from frontend

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
            "export": "/variation/export-midi",
            "osc_send": "/osc/send-melody",
            "osc_completions": "/osc/completions"
        }
    }

@app.get("/osc/completions")
def get_completion_events(since: Optional[float] = None):
    """
    Get melody completion events from SuperCollider.

    Query params:
    - since: timestamp (float) - only return events after this time

    Returns:
    - events: list of completion events with layer and timestamp
    """
    events = event_broadcaster.get_events(since)
    return {
        "success": True,
        "events": events
    }

@app.websocket("/ws/completions")
async def websocket_completions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time melody completion notifications.

    Clients connect to this endpoint and receive completion events
    as they happen from SuperCollider.
    """
    await websocket.accept()
    event_broadcaster.add_websocket(websocket)

    try:
        # Keep connection alive and wait for client disconnect
        while True:
            # Just wait for messages (we don't expect any from client)
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_broadcaster.remove_websocket(websocket)

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

@app.post("/osc/send-melody")
def send_melody_to_supercollider(request: OSCMelodyRequest):
    """
    Send melody to SuperCollider via OSC.

    Routes to /chord if chordMode is true, otherwise /melody.
    Format: {notes: [{midi, vel, dur}, ...], metadata: {..., targetGroup: 0}}
    """
    try:
        # Send the melody via OSC service
        result = osc_service.send_melody(request.notes, request.metadata)

        # Handle looping
        is_loop = request.metadata.get("loop", False)
        target_group = request.metadata.get("targetGroup", 0)
        is_chord_mode = request.metadata.get("chordMode", False)
        osc_address = "/chord" if is_chord_mode else "/melody"

        if is_loop:
            # Store for re-triggering when completion received
            osc_payload = {
                "notes": request.notes,
                "metadata": request.metadata
            }
            json_payload = json.dumps(osc_payload)
            loop_manager.add_loop(target_group, osc_address, json_payload)
        else:
            # Remove from looping if it was previously looping
            loop_manager.remove_loop(target_group)

        return {
            **result,
            "layer": request.layer  # Keep for backward compatibility
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
