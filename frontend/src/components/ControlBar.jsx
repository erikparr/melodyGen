import React, { useRef, useState } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import { sendMelodyToLayer } from '../utils/oscSender';
import { useSequencer } from '../hooks/useSequencer';
import './ControlBar.css';

function ControlBar() {
  const fileInputRef = useRef(null);
  const loadFromJSON = useMelodyStore((state) => state.loadFromJSON);
  const selectedMelodies = useMelodyStore((state) => state.selectedMelodies);
  const loop = useMelodyStore((state) => state.loop);
  const setLoop = useMelodyStore((state) => state.setLoop);
  const tracks = useMelodyStore((state) => state.tracks);
  const importMode = useMelodyStore((state) => state.importMode);
  const setImportMode = useMelodyStore((state) => state.setImportMode);
  const targetLayer = useMelodyStore((state) => state.targetLayer);
  const setTargetLayer = useMelodyStore((state) => state.setTargetLayer);
  const [sending, setSending] = useState(false);

  // Sequencer hook
  const sequencer = useSequencer();

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonData = JSON.parse(e.target.result);
        loadFromJSON(jsonData);
      } catch (error) {
        console.error('Error parsing JSON:', error);
        alert('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const handleLoadClick = () => {
    fileInputRef.current?.click();
  };

  const handlePlayAll = async () => {
    if (selectedMelodies.length === 0 || sending) return;

    setSending(true);
    try {
      // Group selected melodies by track
      const melodiesByTrack = {};
      selectedMelodies.forEach(sel => {
        if (!melodiesByTrack[sel.trackId]) {
          melodiesByTrack[sel.trackId] = [];
        }
        melodiesByTrack[sel.trackId].push(sel.melodyId);
      });

      // Send the most recently selected melody from each track
      const promises = [];
      Object.entries(melodiesByTrack).forEach(([trackId, melodyIds]) => {
        const track = tracks.find(t => t.id === trackId);
        if (!track) return;

        const trackIndex = tracks.indexOf(track);
        const layer = ((trackIndex) % 3) + 1;

        // Get the most recently selected melody for this track
        const lastMelodyId = melodyIds[melodyIds.length - 1];
        const melody = track.melodies.find(m => m.id === lastMelodyId);

        if (melody) {
          promises.push(
            sendMelodyToLayer(melody, layer, loop)
              .then(() => console.log(`Sent ${melody.name} to layer ${layer} (loop: ${loop})`))
          );
        }
      });

      await Promise.all(promises);
    } catch (error) {
      console.error('Failed to send melodies:', error);
      alert(`Failed to send melodies: ${error.message}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="control-bar">
      <div className="control-bar-section">
        <button className="control-button primary" onClick={handleLoadClick}>
          Load Variations
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />
        <div className="import-mode-selector">
          <label className="import-mode-label">
            <input
              type="radio"
              name="importMode"
              value="multi-track"
              checked={importMode === 'multi-track'}
              onChange={(e) => setImportMode(e.target.value)}
            />
            <span>Multi-Track</span>
          </label>
          <label className="import-mode-label">
            <input
              type="radio"
              name="importMode"
              value="single-track"
              checked={importMode === 'single-track'}
              onChange={(e) => setImportMode(e.target.value)}
            />
            <span>Single Track →</span>
          </label>
          {importMode === 'single-track' && (
            <select
              className="layer-select"
              value={targetLayer}
              onChange={(e) => setTargetLayer(Number(e.target.value))}
            >
              <option value={1}>Layer 1</option>
              <option value={2}>Layer 2</option>
              <option value={3}>Layer 3</option>
            </select>
          )}
        </div>
      </div>

      <div className="control-bar-section">
        <button
          className="control-button loop-toggle"
          onClick={() => setLoop(!loop)}
          title={loop ? 'Loop: ON' : 'Loop: OFF'}
        >
          {loop ? '🔁' : '➡️'}
        </button>
        <button
          className="control-button action"
          onClick={handlePlayAll}
          disabled={selectedMelodies.length === 0 || sending || sequencer.isPlaying}
        >
          {sending ? '⏳ Sending...' : `▶ Play All (${selectedMelodies.length})`}
        </button>
        <button
          className="control-button sequencer"
          onClick={sequencer.isPlaying ? sequencer.stop : sequencer.start}
          disabled={selectedMelodies.length === 0}
          title={sequencer.isPlaying ? 'Stop sequence' : 'Play sequence (one-shot mode)'}
        >
          {sequencer.isPlaying
            ? `⏹ Stop (${sequencer.currentIndex + 1}/${sequencer.playlist.length})`
            : `⏭ Sequence (${selectedMelodies.length})`
          }
        </button>
      </div>
    </div>
  );
}

export default ControlBar;
