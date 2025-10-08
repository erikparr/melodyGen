/**
 * Convert internal melody format to OSC format
 * Internal: {midi, time, duration, velocity}
 * OSC: {notes: [{midi, vel, dur}], metadata: {totalDuration, noteCount, name, loop}}
 */
export function convertToOSCFormat(melody, loop = false) {
  if (!melody || !melody.notes || melody.notes.length === 0) {
    throw new Error('Invalid melody data');
  }

  // Calculate total duration (last note time + duration)
  const lastNote = melody.notes[melody.notes.length - 1];
  const totalDuration = lastNote.time + lastNote.duration;

  // Convert notes
  const oscNotes = melody.notes.map(note => ({
    midi: note.midi,
    vel: note.velocity,
    dur: note.duration
  }));

  // Build metadata
  const metadata = {
    totalDuration: totalDuration,
    noteCount: melody.notes.length,
    name: melody.name || 'Unnamed',
    loop: loop
  };

  // Add key/scale if available
  if (melody.metadata) {
    if (melody.metadata.key) {
      metadata.key = melody.metadata.key;
    }
    if (melody.metadata.scale) {
      metadata.scale = melody.metadata.scale;
    }
  }

  return {
    notes: oscNotes,
    metadata: metadata
  };
}

/**
 * Send melody to SuperCollider via backend OSC proxy
 */
export async function sendMelodyToLayer(melody, layer, loop = false) {
  const BACKEND_URL = 'http://localhost:8000';

  try {
    // Convert to OSC format
    const oscData = convertToOSCFormat(melody, loop);

    // Prepare the message payload
    // Layer goes in the request body for backend routing,
    // but the actual OSC message only contains notes and metadata
    const payload = {
      layer: layer,
      notes: oscData.notes,
      metadata: oscData.metadata
    };

    // DEBUG: Log the complete message being sent
    console.log('🎵 Sending OSC message to layer', layer);
    console.log('OSC payload:', JSON.stringify({
      notes: oscData.notes,
      metadata: oscData.metadata
    }, null, 2));

    // Send to backend
    const response = await fetch(`${BACKEND_URL}/osc/send-melody`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Failed to send OSC message');
    }

    return result;

  } catch (error) {
    console.error('OSC send error:', error);
    throw error;
  }
}
