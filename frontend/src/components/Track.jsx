import { useState } from 'react';
import MelodyCard from './MelodyCard';
import { useMelodyStore } from '../store/melodyStore';
import { useMultiTrackPlayer } from '../hooks/useMultiTrackPlayer';
import { sendMelodyToLayer } from '../utils/oscSender';
import './Track.css';

export default function Track({ track, trackId, trackName, melodies, selectedMelodies, onMelodyClick, trackIndex, loop, fixedLayer }) {
  const [sending, setSending] = useState(false);
  const setPlayingMelody = useMelodyStore((state) => state.setPlayingMelody);
  const setTrackTargetGroup = useMelodyStore((state) => state.setTrackTargetGroup);
  const playbackMode = useMelodyStore((state) => state.playbackMode);
  const multiTrack = useMultiTrackPlayer();

  // Get the most recently selected melody for this track
  const getSelectedMelody = () => {
    const trackSelections = selectedMelodies.filter(sel => sel.trackId === trackId);
    if (trackSelections.length === 0) return null;

    const lastSelection = trackSelections[trackSelections.length - 1];
    return melodies.find(m => m.id === lastSelection.melodyId);
  };

  // Use fixedLayer if provided, otherwise auto-assign based on track index
  const layer = fixedLayer || ((trackIndex) % 3) + 1;
  // Use track.targetGroup if available, fallback to trackIndex
  const targetGroup = track?.targetGroup ?? trackIndex;
  // Get oscType from track, fallback to 'melody'
  const oscType = track?.oscType || 'melody';

  const handlePlay = async () => {
    const selectedMelody = getSelectedMelody();
    if (!selectedMelody || sending) return;

    setSending(true);
    try {
      // Trigger flash animation
      setPlayingMelody(trackId, selectedMelody.id);

      await sendMelodyToLayer(selectedMelody, layer, loop, targetGroup, oscType);
      console.log(`Sent ${selectedMelody.name} to ${oscType} targetGroup ${targetGroup} (layer ${layer}, loop: ${loop})`);
    } catch (error) {
      console.error('Failed to send melody:', error);
      alert(`Failed to send melody: ${error.message}`);
    } finally {
      setSending(false);
    }
  };

  const selectedMelody = getSelectedMelody();
  const hasSelection = selectedMelody !== null;

  // Check if this track is currently playing in simultaneous mode
  const isTrackPlaying = multiTrack.playingTracks.has(trackId);

  // Get first selected melody (armed for simultaneous mode)
  const trackSelections = selectedMelodies.filter(sel => sel.trackId === trackId);
  const armedMelodyId = trackSelections.length > 0 ? trackSelections[0].melodyId : null;
  const armedMelody = armedMelodyId ? melodies.find(m => m.id === armedMelodyId) : null;

  return (
    <div className={`track ${isTrackPlaying ? 'track-playing' : ''}`}>
      <div className="track-header">
        <div className="track-name">{trackName}</div>
        <div className="track-controls">
          <span className={`track-osc-type ${oscType}`}>{oscType.toUpperCase()}</span>
          <span className="track-target-label">Target:</span>
          <select
            className="track-target-select"
            value={targetGroup}
            onChange={(e) => setTrackTargetGroup(trackId, Number(e.target.value))}
            title="SuperCollider target group for this track"
          >
            {[0, 1, 2, 3, 4, 5, 6, 7].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
          <span className="track-layer">Layer {layer}</span>
          {isTrackPlaying && (
            <span className="track-playing-indicator">🔴 PLAYING</span>
          )}
          <button
            className="track-play-button"
            onClick={handlePlay}
            disabled={!hasSelection || sending}
            title={hasSelection ? `Send to Layer ${layer}` : 'Select a melody first'}
          >
            {sending ? '⏳' : '▶'}
          </button>
          {isTrackPlaying && (
            <button
              className="track-stop-button"
              onClick={() => multiTrack.stopTrack(trackId)}
              title="Stop this track"
            >
              ⏹
            </button>
          )}
        </div>
      </div>
      {playbackMode === 'simultaneous' && armedMelody && !isTrackPlaying && (
        <div className="armed-indicator">
          Armed: {armedMelody.name}
        </div>
      )}
      <div className="track-content">
        {melodies.map((melody) => (
          <MelodyCard
            key={melody.id}
            melody={melody}
            trackId={trackId}
            melodyId={melody.id}
            selected={selectedMelodies.some(
              (sel) => sel.trackId === trackId && sel.melodyId === melody.id
            )}
            onClick={(e) => onMelodyClick(trackId, melody.id, e)}
          />
        ))}
      </div>
    </div>
  );
}
