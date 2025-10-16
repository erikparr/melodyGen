import { useState } from 'react';
import MelodyCard from './MelodyCard';
import { useMelodyStore } from '../store/melodyStore';
import { sendMelodyToLayer } from '../utils/oscSender';
import './Track.css';

export default function Track({ trackId, trackName, melodies, selectedMelodies, onMelodyClick, trackIndex, loop, fixedLayer }) {
  const [sending, setSending] = useState(false);
  const setPlayingMelody = useMelodyStore((state) => state.setPlayingMelody);

  // Get the most recently selected melody for this track
  const getSelectedMelody = () => {
    const trackSelections = selectedMelodies.filter(sel => sel.trackId === trackId);
    if (trackSelections.length === 0) return null;

    const lastSelection = trackSelections[trackSelections.length - 1];
    return melodies.find(m => m.id === lastSelection.melodyId);
  };

  // Use fixedLayer if provided, otherwise auto-assign based on track index
  const layer = fixedLayer || ((trackIndex) % 3) + 1;

  const handlePlay = async () => {
    const selectedMelody = getSelectedMelody();
    if (!selectedMelody || sending) return;

    setSending(true);
    try {
      // Trigger flash animation
      setPlayingMelody(trackId, selectedMelody.id);

      await sendMelodyToLayer(selectedMelody, layer, loop);
      console.log(`Sent ${selectedMelody.name} to layer ${layer} (loop: ${loop})`);
    } catch (error) {
      console.error('Failed to send melody:', error);
      alert(`Failed to send melody: ${error.message}`);
    } finally {
      setSending(false);
    }
  };

  const selectedMelody = getSelectedMelody();
  const hasSelection = selectedMelody !== null;

  return (
    <div className="track">
      <div className="track-header">
        <div className="track-name">{trackName}</div>
        <div className="track-controls">
          <span className="track-layer">Layer {layer}</span>
          <button
            className="track-play-button"
            onClick={handlePlay}
            disabled={!hasSelection || sending}
            title={hasSelection ? `Send to Layer ${layer}` : 'Select a melody first'}
          >
            {sending ? '⏳' : '▶'}
          </button>
        </div>
      </div>
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
