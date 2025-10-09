import React from 'react';
import Track from './Track';
import { useMelodyStore } from '../store/melodyStore';
import './TrackList.css';

function TrackList() {
  const tracks = useMelodyStore((state) => state.tracks);
  const selectedMelodies = useMelodyStore((state) => state.selectedMelodies);
  const toggleMelody = useMelodyStore((state) => state.toggleMelody);
  const loop = useMelodyStore((state) => state.loop);

  if (!tracks || tracks.length === 0) {
    return (
      <div className="track-list-empty">
        <p>No melodies loaded. Upload a variations JSON file to begin.</p>
      </div>
    );
  }

  return (
    <div className="track-list">
      {tracks.map((track, index) => (
        <Track
          key={track.id}
          trackId={track.id}
          trackName={track.name}
          trackIndex={index}
          melodies={track.melodies || []}
          selectedMelodies={selectedMelodies}
          onMelodyClick={toggleMelody}
          loop={loop}
          fixedLayer={track.fixedLayer}
        />
      ))}
    </div>
  );
}

export default TrackList;
