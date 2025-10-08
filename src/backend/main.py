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
from pythonosc import udp_client, dispatcher, osc_server

from transformations import MusicTransformer
from variations import VariationGenerator
from interpolate import MelodyInterpolator
from constraints import MelodyValidator

app = FastAPI(title="MelodyGen API", version="1.0.0")

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
    asyncio.create_task(broadcast_pending_events())
    print("📡 Started WebSocket broadcast task")

# OSC client for sending to SuperCollider
osc_client = udp_client.SimpleUDPClient("127.0.0.1", 7000)

# Store completion events for polling
completion_events = []

# WebSocket connections and pending events
active_websockets: Set[WebSocket] = set()
pending_events = []

# OSC message handler for melody completion
def handle_melody_complete(address, layer_number):
    """
    Handle OSC completion message from SuperCollider.
    Expected: /liveMelody/complete [layer_number]
    """
    print(f"✅ Melody completed on layer {layer_number}")

    # Store the completion event
    event = {
        "layer": layer_number,
        "timestamp": __import__('time').time()
    }
    completion_events.append(event)
    pending_events.append(event)

    # Keep only last 100 events to prevent memory leak
    if len(completion_events) > 100:
        completion_events.pop(0)

# Background task to broadcast pending events
async def broadcast_pending_events():
    """Continuously broadcast pending events to WebSocket clients."""
    while True:
        if pending_events and active_websockets:
            # Get all pending events
            events_to_send = pending_events.copy()
            pending_events.clear()

            # Broadcast to all connected clients
            disconnected = set()
            for event in events_to_send:
                for websocket in list(active_websockets):
                    try:
                        await websocket.send_json(event)
                    except Exception as e:
                        print(f"WebSocket send error: {e}")
                        disconnected.add(websocket)

            # Remove disconnected clients
            active_websockets.difference_update(disconnected)

        await asyncio.sleep(0.01)  # Check every 10ms

# Setup OSC server to receive messages from SuperCollider
def start_osc_server():
    """Start OSC server in background thread to listen for completion messages."""
    disp = dispatcher.Dispatcher()
    disp.map("/liveMelody/complete", handle_melody_complete)

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
    if since is None:
        # Return all events
        return {
            "success": True,
            "events": completion_events
        }
    else:
        # Return only events after the given timestamp
        filtered = [e for e in completion_events if e["timestamp"] > since]
        return {
            "success": True,
            "events": filtered
        }

@app.websocket("/ws/completions")
async def websocket_completions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time melody completion notifications.

    Clients connect to this endpoint and receive completion events
    as they happen from SuperCollider.
    """
    await websocket.accept()
    active_websockets.add(websocket)
    print(f"🔌 WebSocket client connected (total: {len(active_websockets)})")

    try:
        # Keep connection alive and wait for client disconnect
        while True:
            # Just wait for messages (we don't expect any from client)
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.discard(websocket)
        print(f"🔌 WebSocket client disconnected (total: {len(active_websockets)})")

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

    Sends to /liveMelody/update/layer[1-3] with JSON payload.
    Format: {notes: [{midi, vel, dur}, ...], metadata: {...}}
    """
    try:
        if request.layer < 1 or request.layer > 3:
            return {"success": False, "error": "Layer must be 1, 2, or 3"}

        # Create OSC address (layer is part of the address)
        osc_address = f"/liveMelody/update/layer{request.layer}"

        # Build the OSC payload (notes and metadata at top level)
        osc_payload = {
            "notes": request.notes,
            "metadata": request.metadata
        }

        # Convert to JSON string
        json_payload = json.dumps(osc_payload)

        # DEBUG: Print what we're sending
        print(f"🎵 Sending OSC to {osc_address}")
        print(f"Payload: {json.dumps(osc_payload, indent=2)}")

        # Send OSC message
        osc_client.send_message(osc_address, json_payload)

        return {
            "success": True,
            "layer": request.layer,
            "address": osc_address,
            "note_count": len(request.notes)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
