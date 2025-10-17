import { useState, useEffect } from 'react';
import midiManager from '../utils/midiManager';
import { useMIDIRecorder } from '../hooks/useMIDIRecorder';
import { getQuantizeDivisions } from '../utils/quantizer';
import './MIDIInputPanel.css';

function MIDIInputPanel({ onRecordingComplete, initialDuration = 4.0 }) {
  const [midiSupported, setMidiSupported] = useState(false);
  const [midiAccess, setMidiAccess] = useState(false);
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState('');
  const [deviceConnected, setDeviceConnected] = useState(false);

  const recorder = useMIDIRecorder({
    mode: 'melody',
    onRecordingComplete: onRecordingComplete
  });

  // Check MIDI support on mount
  useEffect(() => {
    const supported = midiManager.constructor.isSupported();
    setMidiSupported(supported);

    if (supported) {
      requestMIDIAccess();
    }
  }, []);

  // Request MIDI access
  const requestMIDIAccess = async () => {
    const success = await midiManager.requestAccess();
    setMidiAccess(success);

    if (success) {
      refreshDevices();

      // Listen for device changes
      midiManager.onDeviceChange((updatedDevices) => {
        setDevices(updatedDevices);
      });
    }
  };

  // Refresh device list
  const refreshDevices = () => {
    const deviceList = midiManager.getDevices();
    setDevices(deviceList);

    // Auto-select first device if available
    if (deviceList.length > 0 && !selectedDevice) {
      setSelectedDevice(deviceList[0].id);
    }
  };

  // Handle device selection
  const handleDeviceChange = (deviceId) => {
    setSelectedDevice(deviceId);

    if (deviceId) {
      const success = midiManager.connect(deviceId);
      setDeviceConnected(success);
    } else {
      midiManager.disconnect();
      setDeviceConnected(false);
    }
  };

  // Handle start/stop recording
  const toggleRecording = () => {
    if (recorder.isRecording) {
      recorder.stopRecording();
    } else {
      if (!deviceConnected) {
        alert('Please select and connect a MIDI device first');
        return;
      }
      recorder.startRecording();
    }
  };

  // Not supported
  if (!midiSupported) {
    return (
      <div className="midi-input-panel">
        <div className="midi-error">
          <div className="error-icon">⚠️</div>
          <div className="error-text">
            <strong>Web MIDI not supported</strong>
            <p>Please use Chrome, Edge, or Opera browser</p>
          </div>
        </div>
      </div>
    );
  }

  // Access not granted
  if (!midiAccess) {
    return (
      <div className="midi-input-panel">
        <div className="midi-error">
          <div className="error-icon">🎹</div>
          <div className="error-text">
            <strong>MIDI Access Required</strong>
            <p>Failed to get MIDI access. Please check browser permissions.</p>
            <button className="retry-button" onClick={requestMIDIAccess}>
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Recording view
  if (recorder.isRecording) {
    return (
      <div className="midi-input-panel recording">
        <div className="recording-header">
          <span className="recording-indicator">⚫</span>
          <span className="recording-label">RECORDING...</span>
        </div>

        <div className="recording-info">
          {recorder.lastNote && (
            <div className="last-note">
              Last: <strong>{recorder.lastNote.name}</strong> ({recorder.lastNote.midi})
              vel:{recorder.lastNote.velocity.toFixed(2)}
            </div>
          )}
          <div className="note-count">
            Count: <strong>{recorder.noteCount}</strong> notes
          </div>
          <div className="elapsed-time">
            Time: <strong>{recorder.elapsedTime.toFixed(1)}s</strong>
          </div>
        </div>

        <button
          className="record-button stop"
          onClick={toggleRecording}
        >
          ⏹ Stop Recording
        </button>
      </div>
    );
  }

  // Setup view
  return (
    <div className="midi-input-panel">
      <div className="panel-header">
        <span className="panel-icon">🎹</span>
        <span className="panel-title">MIDI Input</span>
      </div>

      <div className="device-section">
        <label className="device-label">
          MIDI Device:
          <select
            className="device-select"
            value={selectedDevice}
            onChange={(e) => handleDeviceChange(e.target.value)}
          >
            <option value="">Select device...</option>
            {devices.map(device => (
              <option key={device.id} value={device.id}>
                {device.name}
              </option>
            ))}
          </select>
        </label>
        <button className="refresh-button" onClick={refreshDevices}>
          ↻ Refresh
        </button>
      </div>

      {devices.length === 0 && (
        <div className="no-devices">
          No MIDI devices found. Connect a MIDI keyboard or controller.
        </div>
      )}

      {deviceConnected && (
        <>
          <div className="settings-section">
            <label className="setting-label">
              Quantize:
              <select
                className="setting-select"
                value={recorder.settings.quantizeDivision}
                onChange={(e) => recorder.updateSettings({
                  quantizeDivision: parseInt(e.target.value)
                })}
              >
                {getQuantizeDivisions().map(div => (
                  <option key={div.value} value={div.value}>
                    {div.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="setting-label">
              BPM:
              <input
                type="number"
                className="setting-input"
                value={recorder.settings.bpm}
                onChange={(e) => recorder.updateSettings({
                  bpm: parseInt(e.target.value) || 120
                })}
                min="40"
                max="240"
                step="1"
              />
            </label>

            <label className="setting-label mode-toggle">
              <input
                type="radio"
                checked={recorder.settings.quantizeMode === 'grid'}
                onChange={() => recorder.updateSettings({ quantizeMode: 'grid' })}
              />
              <span>Preserve rhythm</span>
            </label>

            <label className="setting-label mode-toggle">
              <input
                type="radio"
                checked={recorder.settings.quantizeMode === 'equal'}
                onChange={() => recorder.updateSettings({ quantizeMode: 'equal' })}
              />
              <span>Equal spacing</span>
            </label>
          </div>

          <div className="chord-mode-section">
            <label className="chord-mode-toggle">
              <input
                type="checkbox"
                checked={recorder.settings.chordMode}
                onChange={(e) => recorder.updateSettings({ chordMode: e.target.checked })}
              />
              <span className="checkbox-label">
                <strong>Chord Mode</strong>
                <small>Record simultaneous notes as a single chord</small>
              </span>
            </label>
          </div>

          <button
            className="record-button start"
            onClick={toggleRecording}
          >
            ● Start Recording
          </button>

          <div className="status-text">
            {deviceConnected ? '✅ Device connected - Ready to record' : '⚠️ Connect a device to start'}
          </div>
        </>
      )}
    </div>
  );
}

export default MIDIInputPanel;
