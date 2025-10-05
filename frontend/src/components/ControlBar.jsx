import React, { useRef } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import './ControlBar.css';

function ControlBar() {
  const fileInputRef = useRef(null);
  const loadFromJSON = useMelodyStore((state) => state.loadFromJSON);
  const selectedMelodies = useMelodyStore((state) => state.selectedMelodies);
  const clearSelection = useMelodyStore((state) => state.clearSelection);

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

  const handleClearSelection = () => {
    clearSelection();
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
      </div>

      <div className="control-bar-section">
        <div className="selection-info">
          {selectedMelodies.length > 0 ? (
            <>
              <span className="selection-count">
                {selectedMelodies.length} selected
              </span>
              <button
                className="control-button secondary"
                onClick={handleClearSelection}
              >
                Clear Selection
              </button>
            </>
          ) : (
            <span className="selection-count-empty">No selection</span>
          )}
        </div>
      </div>

      <div className="control-bar-section">
        <button
          className="control-button action"
          disabled={selectedMelodies.length === 0}
        >
          Send to Playback ({selectedMelodies.length})
        </button>
      </div>
    </div>
  );
}

export default ControlBar;
