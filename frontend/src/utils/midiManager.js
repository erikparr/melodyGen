/**
 * MIDI Manager - Handles Web MIDI API access and device management
 */

class MIDIManager {
  constructor() {
    this.midiAccess = null;
    this.activeInput = null;
    this.noteOnCallbacks = [];
    this.noteOffCallbacks = [];
    this.deviceChangeCallbacks = [];
  }

  /**
   * Request MIDI access from the browser
   * @returns {Promise<boolean>} Success status
   */
  async requestAccess() {
    if (!navigator.requestMIDIAccess) {
      console.warn('Web MIDI API not supported in this browser');
      return false;
    }

    try {
      this.midiAccess = await navigator.requestMIDIAccess();

      // Listen for device connect/disconnect
      this.midiAccess.onstatechange = (e) => {
        console.log('MIDI device state changed:', e.port.name, e.port.state);
        this.deviceChangeCallbacks.forEach(cb => cb(this.getDevices()));
      };

      console.log('✅ MIDI access granted');
      return true;
    } catch (error) {
      console.error('Failed to get MIDI access:', error);
      return false;
    }
  }

  /**
   * Get list of available MIDI input devices
   * @returns {Array<{id: string, name: string}>}
   */
  getDevices() {
    if (!this.midiAccess) {
      return [];
    }

    const devices = [];
    const inputs = this.midiAccess.inputs.values();

    for (let input of inputs) {
      devices.push({
        id: input.id,
        name: input.name || 'Unknown Device',
        manufacturer: input.manufacturer || '',
        state: input.state
      });
    }

    return devices;
  }

  /**
   * Connect to a MIDI input device
   * @param {string} deviceId - Device ID to connect to
   * @returns {boolean} Success status
   */
  connect(deviceId) {
    if (!this.midiAccess) {
      console.error('MIDI access not initialized');
      return false;
    }

    // Disconnect previous device
    this.disconnect();

    const input = this.midiAccess.inputs.get(deviceId);
    if (!input) {
      console.error('MIDI device not found:', deviceId);
      return false;
    }

    this.activeInput = input;
    this.activeInput.onmidimessage = this._handleMIDIMessage.bind(this);

    console.log('🎹 Connected to MIDI device:', input.name);
    return true;
  }

  /**
   * Disconnect from current MIDI device
   */
  disconnect() {
    if (this.activeInput) {
      this.activeInput.onmidimessage = null;
      console.log('🔌 Disconnected from MIDI device');
      this.activeInput = null;
    }
  }

  /**
   * Handle incoming MIDI message
   * @private
   */
  _handleMIDIMessage(event) {
    const [status, note, velocity] = event.data;
    const channel = status & 0x0F;
    const command = status & 0xF0;

    // Note On (0x90-0x9F)
    if (command === 0x90 && velocity > 0) {
      const normalizedVelocity = velocity / 127;
      this.noteOnCallbacks.forEach(cb => cb(note, normalizedVelocity, channel));
    }

    // Note Off (0x80-0x8F) or Note On with velocity 0
    else if (command === 0x80 || (command === 0x90 && velocity === 0)) {
      this.noteOffCallbacks.forEach(cb => cb(note, channel));
    }
  }

  /**
   * Register callback for note on events
   * @param {Function} callback - (note, velocity, channel) => void
   */
  onNoteOn(callback) {
    this.noteOnCallbacks.push(callback);
  }

  /**
   * Register callback for note off events
   * @param {Function} callback - (note, channel) => void
   */
  onNoteOff(callback) {
    this.noteOffCallbacks.push(callback);
  }

  /**
   * Register callback for device list changes
   * @param {Function} callback - (devices) => void
   */
  onDeviceChange(callback) {
    this.deviceChangeCallbacks.push(callback);
  }

  /**
   * Remove all event listeners
   */
  clearCallbacks() {
    this.noteOnCallbacks = [];
    this.noteOffCallbacks = [];
    this.deviceChangeCallbacks = [];
  }

  /**
   * Check if Web MIDI API is supported
   * @returns {boolean}
   */
  static isSupported() {
    return typeof navigator !== 'undefined' && !!navigator.requestMIDIAccess;
  }

  /**
   * Convert MIDI note number to note name
   * @param {number} midiNote - MIDI note number (0-127)
   * @returns {string} Note name (e.g., "C4")
   */
  static midiToNoteName(midiNote) {
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const octave = Math.floor(midiNote / 12) - 1;
    const noteName = noteNames[midiNote % 12];
    return `${noteName}${octave}`;
  }
}

// Export singleton instance
export const midiManager = new MIDIManager();
export default midiManager;
