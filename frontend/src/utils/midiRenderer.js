/**
 * MIDI Piano Roll Renderer
 * Draws melody notes on canvas with piano roll visualization
 */

export function drawMelodyCard(canvas, notes, options = {}) {
  if (!canvas || !notes || notes.length === 0) return;

  const {
    width = canvas.width,
    height = canvas.height,
    minPitch = null,
    maxPitch = null,
    backgroundColor = '#1a1a1a',
    gridColor = '#333',
    showGrid = true
  } = options;

  const ctx = canvas.getContext('2d');

  // Set canvas dimensions
  canvas.width = width;
  canvas.height = height;

  // Clear canvas
  ctx.fillStyle = backgroundColor;
  ctx.fillRect(0, 0, width, height);

  // Calculate pitch range
  const pitches = notes.map(n => n.midi);
  const min = minPitch !== null ? minPitch : Math.min(...pitches) - 2;
  const max = maxPitch !== null ? maxPitch : Math.max(...pitches) + 2;
  const pitchRange = max - min;

  // Calculate time range
  const times = notes.map(n => n.time);
  const durations = notes.map((n, i) => n.duration || (notes[i+1] ? notes[i+1].time - n.time : 0.25));
  const totalDuration = Math.max(...notes.map((n, i) => n.time + durations[i]));

  // Draw grid (optional)
  if (showGrid) {
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;

    // Horizontal lines (octaves)
    for (let pitch = Math.floor(min / 12) * 12; pitch <= max; pitch += 12) {
      const y = pitchToY(pitch, min, max, height);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Vertical lines (beats - assuming 4/4 time)
    const secondsPerBeat = 0.5; // 120 BPM
    for (let time = 0; time <= totalDuration; time += secondsPerBeat) {
      const x = (time / totalDuration) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
  }

  // Group notes by time to detect chords (notes at same time)
  const noteGroups = groupNotesByTime(notes, durations, 0.001);

  // Draw notes
  noteGroups.forEach(group => {
    const isChord = group.notes.length > 1;

    group.notes.forEach((note, i) => {
      const duration = group.duration;
      const x = (group.time / totalDuration) * width;
      const y = pitchToY(note.midi, min, max, height);
      const w = Math.max(2, (duration / totalDuration) * width);
      const h = Math.max(4, height / pitchRange * 0.8);

      // Color by velocity (with chord accent)
      const color = isChord
        ? velocityToColor(note.velocity || note.vel || 0.7, true)
        : velocityToColor(note.velocity || note.vel || 0.7, false);

      // Draw note rectangle
      ctx.fillStyle = color;
      ctx.fillRect(x, y - h/2, w, h);

      // Add border (stronger for chords)
      if (isChord) {
        ctx.strokeStyle = 'rgba(100, 200, 255, 0.6)'; // Blue accent for chords
        ctx.lineWidth = 2;
      } else {
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.lineWidth = 1;
      }
      ctx.strokeRect(x, y - h/2, w, h);
    });

    // Draw chord connector line (vertical line through all notes)
    if (isChord) {
      const x = (group.time / totalDuration) * width;
      const topNote = Math.max(...group.notes.map(n => n.midi));
      const bottomNote = Math.min(...group.notes.map(n => n.midi));
      const yTop = pitchToY(topNote, min, max, height);
      const yBottom = pitchToY(bottomNote, min, max, height);

      ctx.strokeStyle = 'rgba(100, 200, 255, 0.3)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x - 2, yTop);
      ctx.lineTo(x - 2, yBottom);
      ctx.stroke();
    }
  });
}

/**
 * Group notes that occur at the same time (chords)
 */
function groupNotesByTime(notes, durations, threshold = 0.001) {
  const groups = [];
  const processed = new Set();

  notes.forEach((note, i) => {
    if (processed.has(i)) return;

    const group = {
      time: note.time,
      duration: durations[i],
      notes: [note]
    };

    // Find all notes at the same time
    for (let j = i + 1; j < notes.length; j++) {
      if (processed.has(j)) continue;
      if (Math.abs(notes[j].time - note.time) < threshold) {
        group.notes.push(notes[j]);
        processed.add(j);
      }
    }

    processed.add(i);
    groups.push(group);
  });

  return groups;
}

/**
 * Convert MIDI pitch to Y coordinate
 */
function pitchToY(pitch, minPitch, maxPitch, height) {
  const normalized = (pitch - minPitch) / (maxPitch - minPitch);
  return height - (normalized * height); // Flip Y axis (higher pitch = top)
}

/**
 * Convert velocity (0-1) to color
 * High velocity = bright red
 * Medium velocity = orange/pink
 * Low velocity = purple/blue
 * Chords get a cyan/blue tint
 */
function velocityToColor(velocity, isChord = false) {
  // Normalize velocity to 0-1 if it's in 0-127 range
  const v = velocity > 1 ? velocity / 127 : velocity;

  if (isChord) {
    // Chord notes: cyan/blue gradient based on velocity
    if (v >= 0.8) {
      return `rgba(100, 200, 255, ${0.8 + v * 0.2})`;
    } else if (v >= 0.5) {
      return `rgba(120, 180, 255, ${0.7 + v * 0.3})`;
    } else {
      return `rgba(140, 160, 255, ${0.6 + v * 0.4})`;
    }
  }

  // Regular melody notes
  if (v >= 0.8) {
    // High velocity: bright red
    return `rgba(255, 100, 100, ${0.7 + v * 0.3})`;
  } else if (v >= 0.5) {
    // Medium velocity: orange/coral
    return `rgba(255, 150, 100, ${0.6 + v * 0.4})`;
  } else {
    // Low velocity: purple/blue
    return `rgba(150, 100, 255, ${0.5 + v * 0.5})`;
  }
}

/**
 * Get note info at position (for tooltips/hover)
 */
export function getNoteAtPosition(notes, x, y, totalDuration, minPitch, maxPitch, width, height) {
  const time = (x / width) * totalDuration;

  for (let i = 0; i < notes.length; i++) {
    const note = notes[i];
    const duration = note.duration || (notes[i+1] ? notes[i+1].time - note.time : 0.25);

    if (time >= note.time && time <= note.time + duration) {
      const noteY = pitchToY(note.midi, minPitch, maxPitch, height);
      const h = height / (maxPitch - minPitch) * 0.8;

      if (y >= noteY - h/2 && y <= noteY + h/2) {
        return {
          ...note,
          index: i
        };
      }
    }
  }

  return null;
}
