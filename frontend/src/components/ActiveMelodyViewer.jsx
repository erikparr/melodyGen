import React, { useEffect, useRef } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import { drawMelodyCard } from '../utils/midiRenderer';
import MIDIInputPanel from './MIDIInputPanel';
import './ActiveMelodyViewer.css';

// Available scales for dropdown
const SCALES = [
  'major', 'minor', 'harmonic minor', 'melodic minor',
  'dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian',
  'phrygian dominant', 'pentatonic major', 'pentatonic minor',
  'blues', 'whole tone', 'chromatic'
];

// Available keys
const KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

function ActiveMelodyViewer() {
  const canvasRef = useRef(null);
  const activeMelody = useMelodyStore((state) => state.activeMelody);
  const tracks = useMelodyStore((state) => state.tracks);
  const updateMelodyMetadata = useMelodyStore((state) => state.updateMelodyMetadata);
  const updateMelodyNotes = useMelodyStore((state) => state.updateMelodyNotes);

  // Get the active melody data
  const getMelodyData = () => {
    if (!activeMelody) return null;

    const track = tracks.find(t => t.id === activeMelody.trackId);
    if (!track) return null;

    const melody = track.melodies.find(m => m.id === activeMelody.melodyId);
    if (!melody) return null;

    return {
      melody,
      track,
      layer: track.fixedLayer || (tracks.indexOf(track) % 3) + 1
    };
  };

  const melodyData = getMelodyData();

  // Render canvas when melody changes
  useEffect(() => {
    if (!melodyData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const { melody } = melodyData;

    // Only draw if there are notes
    if (melody.notes.length > 0) {
      drawMelodyCard(canvas, melody.notes, {
        width: canvas.offsetWidth * 2, // 2x for retina
        height: canvas.offsetHeight * 2,
        backgroundColor: '#0a0a0a',
        gridColor: '#222',
        showGrid: true
      });
    } else {
      // Clear canvas for empty melodies
      const ctx = canvas.getContext('2d');
      canvas.width = canvas.offsetWidth * 2;
      canvas.height = canvas.offsetHeight * 2;
      ctx.fillStyle = '#0a0a0a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
  }, [melodyData]);

  const handleMetadataChange = (field, value) => {
    if (!melodyData) return;

    const { track, melody } = melodyData;
    updateMelodyMetadata(track.id, melody.id, { [field]: value });
  };

  const handleMIDIRecording = (notes) => {
    if (!melodyData) return;

    const { track, melody } = melodyData;
    console.log('📝 MIDI recording complete, updating melody with', notes.length, 'notes');
    updateMelodyNotes(track.id, melody.id, notes);
  };

  if (!melodyData) {
    return (
      <div className="active-melody-viewer empty">
        <div className="empty-message">
          <span>No melody selected</span>
          <span className="empty-hint">Click a melody card to preview</span>
        </div>
      </div>
    );
  }

  const { melody, track, layer } = melodyData;
  const noteCount = melody.notes.length;
  const metadata = melody.metadata || {};
  const duration = metadata.totalDuration || 0;
  const durationType = metadata.durationType || 'absolute';
  const key = metadata.key || 'C';
  const scale = metadata.scale || 'major';

  return (
    <div className="active-melody-viewer">
      <div className="viewer-header">
        <div className="melody-info">
          <span className="melody-name">{melody.name}</span>
          <span className="melody-meta">
            {track.name} • Layer {layer} • {noteCount} notes
          </span>
        </div>
      </div>

      <div className="viewer-canvas-container">
        {noteCount === 0 ? (
          <MIDIInputPanel
            onRecordingComplete={handleMIDIRecording}
            initialDuration={duration}
          />
        ) : (
          <canvas
            ref={canvasRef}
            className="viewer-canvas"
          />
        )}
      </div>

      <div className="metadata-editor">
        <div className="metadata-row">
          <label className="metadata-label">
            Duration (s):
            <input
              type="number"
              className="metadata-input"
              value={duration}
              onChange={(e) => handleMetadataChange('totalDuration', parseFloat(e.target.value) || 0)}
              step="0.25"
              min="0.25"
              max="32"
            />
          </label>

          <label className="metadata-label">
            Duration Type:
            <select
              className="metadata-select"
              value={durationType}
              onChange={(e) => handleMetadataChange('durationType', e.target.value)}
            >
              <option value="absolute">Absolute</option>
              <option value="fractional">Fractional</option>
            </select>
          </label>
        </div>

        <div className="metadata-row">
          <label className="metadata-label">
            Key:
            <select
              className="metadata-select"
              value={key}
              onChange={(e) => handleMetadataChange('key', e.target.value)}
            >
              {KEYS.map(k => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </label>

          <label className="metadata-label">
            Scale:
            <select
              className="metadata-select"
              value={scale}
              onChange={(e) => handleMetadataChange('scale', e.target.value)}
            >
              {SCALES.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </div>
  );
}

export default ActiveMelodyViewer;
