import { useRef, useEffect, useState } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import { drawMelodyCard, getNoteAtPosition } from '../utils/midiRenderer';
import './MelodyCard.css';

export default function MelodyCard({ melody, selected, onClick, trackId, melodyId }) {
  const canvasRef = useRef(null);
  const [hoveredNote, setHoveredNote] = useState(null);
  const playingMelody = useMelodyStore((state) => state.playingMelody);

  // Check if this melody is currently playing
  const isPlaying = playingMelody &&
    playingMelody.trackId === trackId &&
    playingMelody.melodyId === melodyId;

  const width = 200;
  const height = 100;

  // Draw melody on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !melody?.notes) return;

    drawMelodyCard(canvas, melody.notes, {
      width,
      height,
      backgroundColor: selected ? '#2a2a3a' : '#1a1a1a',
      gridColor: '#333',
      showGrid: true
    });
  }, [melody, selected]);

  // Handle mouse hover for tooltips
  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    if (!canvas || !melody?.notes) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const pitches = melody.notes.map(n => n.midi);
    const minPitch = Math.min(...pitches) - 2;
    const maxPitch = Math.max(...pitches) + 2;

    const times = melody.notes.map(n => n.time);
    const durations = melody.notes.map((n, i) =>
      n.duration || (melody.notes[i+1] ? melody.notes[i+1].time - n.time : 0.25)
    );
    const totalDuration = Math.max(...melody.notes.map((n, i) => n.time + durations[i]));

    const note = getNoteAtPosition(
      melody.notes,
      x,
      y,
      totalDuration,
      minPitch,
      maxPitch,
      width,
      height
    );

    setHoveredNote(note);
  };

  const handleMouseLeave = () => {
    setHoveredNote(null);
  };

  // Note name from MIDI number
  const getMidiNoteName = (midi) => {
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const octave = Math.floor(midi / 12) - 1;
    const noteName = noteNames[midi % 12];
    return `${noteName}${octave}`;
  };

  return (
    <div className={`melody-card ${selected ? 'selected' : ''} ${isPlaying ? 'playing' : ''}`} onClick={onClick}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      />
      <div className="melody-card-label">
        {melody?.name || 'Untitled'}
      </div>

      {/* Tooltip for hovered note */}
      {hoveredNote && (
        <div className="note-tooltip">
          {getMidiNoteName(hoveredNote.midi)} •
          vel: {(hoveredNote.velocity || hoveredNote.vel || 0.7).toFixed(2)}
        </div>
      )}

      {/* Metadata badge */}
      {melody?.metadata && (
        <div className="melody-card-meta">
          {melody.metadata.key} {melody.metadata.scale}
        </div>
      )}
    </div>
  );
}
