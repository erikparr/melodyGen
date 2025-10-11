import React from 'react';
import { useMelodyStore } from '../store/melodyStore';
import './BottomControlBar.css';

function BottomControlBar() {
  const selectedMelodies = useMelodyStore((state) => state.selectedMelodies);
  const tracks = useMelodyStore((state) => state.tracks);
  const selectAll = useMelodyStore((state) => state.selectAll);
  const clearSelection = useMelodyStore((state) => state.clearSelection);
  const deleteMelodies = useMelodyStore((state) => state.deleteMelodies);
  const moveToNewLayer = useMelodyStore((state) => state.moveToNewLayer);

  // Check if all melodies are selected
  const totalMelodies = tracks.reduce((sum, track) => sum + track.melodies.length, 0);
  const allSelected = totalMelodies > 0 && selectedMelodies.length === totalMelodies;

  const handleToggleSelectAll = () => {
    if (allSelected) {
      clearSelection();
    } else {
      selectAll();
    }
  };

  const handleDelete = () => {
    if (selectedMelodies.length === 0) return;
    if (confirm(`Delete ${selectedMelodies.length} selected melodies?`)) {
      deleteMelodies();
    }
  };

  const handleMoveToNewLayer = () => {
    if (selectedMelodies.length === 0) return;
    moveToNewLayer();
  };

  return (
    <div className="bottom-control-bar">
      <div className="bottom-bar-section">
        <span className="selection-info">
          {selectedMelodies.length > 0 ? (
            <span className="selection-count">{selectedMelodies.length} selected</span>
          ) : (
            <span className="selection-count-empty">No selection</span>
          )}
        </span>
      </div>

      <div className="bottom-bar-section">
        <button
          className="bottom-button secondary"
          onClick={handleToggleSelectAll}
          disabled={totalMelodies === 0}
        >
          {allSelected ? 'Clear Selection' : 'Select All'}
        </button>
        <button
          className="bottom-button action"
          onClick={handleMoveToNewLayer}
          disabled={selectedMelodies.length === 0}
        >
          Move to New Layer
        </button>
        <button
          className="bottom-button danger"
          onClick={handleDelete}
          disabled={selectedMelodies.length === 0}
        >
          Delete Selected
        </button>
      </div>
    </div>
  );
}

export default BottomControlBar;
