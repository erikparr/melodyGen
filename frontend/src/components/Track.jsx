import MelodyCard from './MelodyCard';
import './Track.css';

export default function Track({ trackId, trackName, melodies, selectedMelodies, onMelodyClick }) {
  return (
    <div className="track">
      <div className="track-header">
        <div className="track-name">{trackName}</div>
        <div className="track-info">{melodies.length} variations</div>
      </div>
      <div className="track-content">
        {melodies.map((melody) => (
          <MelodyCard
            key={melody.id}
            melody={melody}
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
