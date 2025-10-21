import React, { useRef, useState } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import { sendMelodyToLayer } from '../utils/oscSender';
import { useSequencer } from '../hooks/useSequencer';
import { useMultiTrackPlayer } from '../hooks/useMultiTrackPlayer';
import './ControlBar.css';

function ControlBar() {
  const fileInputRef = useRef(null);
  const loadFromJSON = useMelodyStore((state) => state.loadFromJSON);
  const selectedMelodies = useMelodyStore((state) => state.selectedMelodies);
  const loop = useMelodyStore((state) => state.loop);
  const setLoop = useMelodyStore((state) => state.setLoop);
  const sequenceLoop = useMelodyStore((state) => state.sequenceLoop);
  const setSequenceLoop = useMelodyStore((state) => state.setSequenceLoop);
  const setPlayingMelody = useMelodyStore((state) => state.setPlayingMelody);
  const tracks = useMelodyStore((state) => state.tracks);
  const importMode = useMelodyStore((state) => state.importMode);
  const setImportMode = useMelodyStore((state) => state.setImportMode);
  const targetLayer = useMelodyStore((state) => state.targetLayer);
  const setTargetLayer = useMelodyStore((state) => state.setTargetLayer);
  const createNewMelody = useMelodyStore((state) => state.createNewMelody);
  const playbackMode = useMelodyStore((state) => state.playbackMode);
  const setPlaybackMode = useMelodyStore((state) => state.setPlaybackMode);
  const [sending, setSending] = useState(false);

  // Sequencer and multi-track hooks
  const sequencer = useSequencer();
  const multiTrack = useMultiTrackPlayer();

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
          // Trigger flash animation
          setPlayingMelody(trackId, lastMelodyId);

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
        <button className="control-button primary" onClick={createNewMelody}>
          New Melody
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
        {/* Playback Mode Toggle */}
        <div className="mode-toggle">
          <button
            className={playbackMode === 'sequential' ? 'active' : ''}
            onClick={() => setPlaybackMode('sequential')}
            title="Play melodies one after another"
          >
            Sequential
          </button>
          <button
            className={playbackMode === 'simultaneous' ? 'active' : ''}
            onClick={() => setPlaybackMode('simultaneous')}
            title="Play all tracks simultaneously (multi-track looping)"
          >
            Simultaneous
          </button>
        </div>

        {/* Conditional Controls based on playback mode */}
        {playbackMode === 'sequential' ? (
          <>
            <button
              className={`control-button toggle ${loop ? 'active' : ''}`}
              onClick={() => setLoop(!loop)}
              title={loop ? 'Individual Loop: ON' : 'Individual Loop: OFF'}
            >
              Loop: {loop ? 'ON' : 'OFF'}
            </button>
            <button
              className="control-button action"
              onClick={handlePlayAll}
              disabled={selectedMelodies.length === 0 || sending || sequencer.isPlaying}
            >
              {sending ? 'Sending...' : `Play All (${selectedMelodies.length})`}
            </button>
            <button
              className={`control-button toggle ${sequenceLoop ? 'active' : ''}`}
              onClick={() => setSequenceLoop(!sequenceLoop)}
              title={sequenceLoop ? 'Sequence Loop: ON' : 'Sequence Loop: OFF'}
            >
              Seq Loop: {sequenceLoop ? 'ON' : 'OFF'}
            </button>
            <button
              className="control-button sequencer"
              onClick={sequencer.isPlaying ? sequencer.stop : sequencer.start}
              disabled={selectedMelodies.length === 0}
              title={sequencer.isPlaying ? 'Stop sequence' : (sequenceLoop ? 'Play sequence (looping)' : 'Play sequence (one-shot)')}
            >
              {sequencer.isPlaying
                ? `Stop (${sequencer.currentIndex + 1}/${sequencer.playlist.length})`
                : `Sequence (${selectedMelodies.length})`
              }
            </button>
          </>
        ) : (
          <>
            <button
              className="control-button action multi-track-play"
              onClick={multiTrack.startAll}
              disabled={multiTrack.isPlaying || multiTrack.trackCount === 0}
              title="Play all tracks simultaneously with independent looping"
            >
              ▶ Play All Tracks ({multiTrack.trackCount})
            </button>
            <button
              className="control-button stop"
              onClick={multiTrack.stopAll}
              disabled={!multiTrack.isPlaying}
              title="Stop all looping tracks"
            >
              ⏹ Stop All
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default ControlBar;
