/**
 * Convert internal melody format to OSC format
 * Internal: {midi, time, duration, velocity}
 * OSC: {notes: [{midi, vel, dur}], metadata: {totalDuration, noteCount, name, loop, targetGroup}}
 */
export function convertToOSCFormat(melody, loop = false, targetGroup = 0, oscType = null) {
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
    loop: loop,
    targetGroup: targetGroup  // NEW: 0-based track index
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

  // Use oscType from track if provided, otherwise fall back to melody's chordMode
  if (oscType !== null) {
    metadata.chordMode = oscType === 'chord';
  } else if (melody.metadata?.chordMode !== undefined) {
    metadata.chordMode = melody.metadata.chordMode;
  }

  return {
    notes: oscNotes,
    metadata: metadata
  };
}

/**
 * Send melody to SuperCollider via backend OSC proxy
 */
export async function sendMelodyToLayer(melody, layer, loop = false, targetGroup = 0, oscType = null) {
  const BACKEND_URL = 'http://localhost:8000';

  try {
    // Convert to OSC format with targetGroup and oscType
    const oscData = convertToOSCFormat(melody, loop, targetGroup, oscType);

    // Prepare the message payload
    // Layer kept for backward compatibility, but targetGroup is in metadata
    const payload = {
      layer: layer,
      notes: oscData.notes,
      metadata: oscData.metadata
    };

    // Determine OSC address based on chordMode
    const isChordMode = oscData.metadata.chordMode || false;
    const oscAddress = isChordMode ? '/chord' : '/melody';

    // DEBUG: Log the complete message being sent
    console.log(`🎵 Sending to ${oscAddress} - targetGroup: ${targetGroup}, layer: ${layer}, loop: ${loop}`);
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
