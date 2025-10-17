/**
 * Quantizer - Converts raw recorded MIDI notes into quantized melodies
 */

/**
 * Calculate total duration of a note list
 * @param {Array} notes - Array of note objects with time and duration
 * @returns {number} Total duration in seconds
 */
export function calculateTotalDuration(notes) {
  if (!notes || notes.length === 0) return 0;

  return Math.max(...notes.map(n => (n.time || 0) + (n.duration || 0)));
}

/**
 * Quantize notes to musical grid (rhythm-preserving)
 * @param {Array} recordedNotes - Raw notes with onTime, duration, midi, velocity
 * @param {Object} settings - { bpm, quantizeDivision }
 * @returns {Array} Quantized notes with time, duration, midi, velocity
 */
export function quantizeToGrid(recordedNotes, settings = {}) {
  const { bpm = 120, quantizeDivision = 16 } = settings;

  if (!recordedNotes || recordedNotes.length === 0) {
    return [];
  }

  // Calculate grid size
  const beatDuration = 60 / bpm; // seconds per beat
  const gridSize = beatDuration / (quantizeDivision / 4); // grid interval in seconds

  // Convert to milliseconds for precision
  const gridSizeMs = gridSize * 1000;

  return recordedNotes
    .map(note => {
      // Quantize start time to nearest grid
      const onTimeMs = note.onTime;
      const gridPosition = Math.round(onTimeMs / gridSizeMs);
      const quantizedTime = (gridPosition * gridSizeMs) / 1000; // back to seconds

      // Quantize duration to nearest grid (minimum 1 grid)
      const durationMs = note.duration || 100;
      const durationGrids = Math.max(1, Math.round(durationMs / gridSizeMs));
      const quantizedDuration = (durationGrids * gridSizeMs) / 1000; // back to seconds

      return {
        midi: note.midi,
        time: quantizedTime,
        duration: quantizedDuration,
        velocity: note.velocity
      };
    })
    .sort((a, b) => a.time - b.time); // Ensure chronological order
}

/**
 * Space notes equally across a duration (ignores original timing)
 * @param {Array} recordedNotes - Raw notes with midi, velocity
 * @param {number} totalDuration - Target duration in seconds
 * @returns {Array} Equally-spaced notes
 */
export function equalSpaceNotes(recordedNotes, totalDuration = 4.0) {
  if (!recordedNotes || recordedNotes.length === 0) {
    return [];
  }

  const interval = totalDuration / recordedNotes.length;
  const noteDuration = interval * 0.75; // 75% of interval (leaves gap)

  return recordedNotes.map((note, index) => ({
    midi: note.midi,
    time: index * interval,
    duration: noteDuration,
    velocity: note.velocity
  }));
}

/**
 * Normalize velocities to a target range
 * @param {Array} notes - Notes with velocity values
 * @param {Object} options - { min, max, mode }
 * @returns {Array} Notes with normalized velocities
 */
export function normalizeVelocities(notes, options = {}) {
  const { min = 0.5, max = 1.0, mode = 'scale' } = options;

  if (!notes || notes.length === 0) {
    return [];
  }

  if (mode === 'constant') {
    // Set all to same velocity
    const targetVel = (min + max) / 2;
    return notes.map(n => ({ ...n, velocity: targetVel }));
  }

  if (mode === 'scale') {
    // Scale existing range to target range
    const velocities = notes.map(n => n.velocity);
    const minVel = Math.min(...velocities);
    const maxVel = Math.max(...velocities);
    const range = maxVel - minVel;

    if (range === 0) {
      // All same velocity
      return notes.map(n => ({ ...n, velocity: (min + max) / 2 }));
    }

    return notes.map(n => ({
      ...n,
      velocity: min + ((n.velocity - minVel) / range) * (max - min)
    }));
  }

  return notes;
}

/**
 * Merge very short notes into longer sustains
 * @param {Array} notes - Notes to process
 * @param {number} minDuration - Minimum duration in seconds
 * @returns {Array} Processed notes
 */
export function mergeShortNotes(notes, minDuration = 0.05) {
  if (!notes || notes.length === 0) {
    return [];
  }

  return notes.map(note => ({
    ...note,
    duration: Math.max(note.duration, minDuration)
  }));
}

/**
 * Remove overlapping notes (keep first)
 * @param {Array} notes - Notes to process
 * @returns {Array} Non-overlapping notes
 */
export function removeOverlaps(notes) {
  if (!notes || notes.length <= 1) {
    return notes;
  }

  const sorted = [...notes].sort((a, b) => a.time - b.time);
  const result = [];

  for (let i = 0; i < sorted.length; i++) {
    const current = sorted[i];
    const currentEnd = current.time + current.duration;

    // Check if overlaps with previous note
    if (result.length > 0) {
      const previous = result[result.length - 1];
      const previousEnd = previous.time + previous.duration;

      if (current.time < previousEnd) {
        // Truncate previous note to avoid overlap
        previous.duration = current.time - previous.time;
      }
    }

    result.push(current);
  }

  return result;
}

/**
 * Group notes into chords based on time proximity
 * @param {Array} notes - Notes to group
 * @param {number} timeThreshold - Max time difference (seconds) to consider notes simultaneous
 * @returns {Array} Notes with normalized chord timing
 */
export function groupNotesIntoChords(notes, timeThreshold = 0.05) {
  if (!notes || notes.length === 0) {
    return [];
  }

  // Sort by time
  const sorted = [...notes].sort((a, b) => a.time - b.time);

  const chords = [];
  let currentChord = [sorted[0]];

  for (let i = 1; i < sorted.length; i++) {
    const timeDiff = sorted[i].time - currentChord[0].time;

    if (timeDiff < timeThreshold) {
      // Part of same chord
      currentChord.push(sorted[i]);
    } else {
      // New chord - normalize and save previous
      chords.push(normalizeChord(currentChord));
      currentChord = [sorted[i]];
    }
  }

  // Don't forget last chord
  chords.push(normalizeChord(currentChord));

  return chords.flat();
}

/**
 * Normalize chord notes to have same time and duration
 * @param {Array} chordNotes - Notes in the chord
 * @returns {Array} Normalized chord notes
 */
function normalizeChord(chordNotes) {
  if (!chordNotes || chordNotes.length === 0) {
    return [];
  }

  // Use earliest time as chord time
  const chordTime = Math.min(...chordNotes.map(n => n.time));

  // Use longest duration as chord duration
  const chordDuration = Math.max(...chordNotes.map(n => n.duration));

  return chordNotes.map(note => ({
    ...note,
    time: chordTime,
    duration: chordDuration
  }));
}

/**
 * Full processing pipeline for recorded notes
 * @param {Array} recordedNotes - Raw recorded notes
 * @param {Object} settings - Processing settings
 * @returns {Array} Fully processed notes
 */
export function processRecording(recordedNotes, settings = {}) {
  const {
    mode = 'grid', // 'grid' | 'equal'
    bpm = 120,
    quantizeDivision = 16,
    totalDuration = 4.0,
    normalizeVelocity = false,
    minNoteDuration = 0.05,
    chordMode = false
  } = settings;

  if (!recordedNotes || recordedNotes.length === 0) {
    return [];
  }

  let processed;

  // Apply quantization mode
  if (mode === 'equal') {
    processed = equalSpaceNotes(recordedNotes, totalDuration);
  } else {
    processed = quantizeToGrid(recordedNotes, { bpm, quantizeDivision });
  }

  // Merge very short notes
  processed = mergeShortNotes(processed, minNoteDuration);

  // Chord mode: group simultaneous notes
  if (chordMode) {
    processed = groupNotesIntoChords(processed);
    console.log('🎹 Chord mode: Grouped notes into chords');
  } else {
    // Melody mode: remove overlaps
    processed = removeOverlaps(processed);
  }

  // Normalize velocities if requested
  if (normalizeVelocity) {
    processed = normalizeVelocities(processed, { mode: 'scale' });
  }

  return processed;
}

/**
 * Get quantization division options
 * @returns {Array} Division options with labels
 */
export function getQuantizeDivisions() {
  return [
    { value: 4, label: '1/4 (Quarter notes)' },
    { value: 8, label: '1/8 (Eighth notes)' },
    { value: 16, label: '1/16 (Sixteenth notes)' },
    { value: 32, label: '1/32 (Thirty-second notes)' }
  ];
}
