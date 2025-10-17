import { useState, useEffect, useRef, useCallback } from 'react';
import midiManager from '../utils/midiManager';
import { processRecording } from '../utils/quantizer';

/**
 * Hook for recording MIDI input
 * @param {Object} options - Recording options
 * @returns {Object} Recording state and controls
 */
export function useMIDIRecorder(options = {}) {
  const {
    mode = 'melody', // 'melody' | 'chord'
    onRecordingComplete = null
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [recordedNotes, setRecordedNotes] = useState([]);
  const [lastNote, setLastNote] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  const isRecordingRef = useRef(false); // Add ref to track recording state
  const recordingStartTime = useRef(null);
  const activeNotes = useRef(new Map());
  const timerInterval = useRef(null);

  // Recording settings
  const [settings, setSettings] = useState({
    quantizeMode: 'grid', // 'grid' | 'equal'
    bpm: 120,
    quantizeDivision: 16,
    minNoteDuration: 0.05,
    chordMode: false
  });

  /**
   * Handle note on event from MIDI
   */
  const handleNoteOn = useCallback((midiNote, velocity, channel) => {
    console.log('🎹 MIDI Note ON received:', midiNote, 'recording:', isRecordingRef.current);

    if (!isRecordingRef.current) return;

    const timestamp = performance.now();

    // Melody mode: only one note at a time (no overlaps)
    if (!settings.chordMode && mode === 'melody') {
      // If a note is already active, ignore this one
      if (activeNotes.current.size > 0) {
        console.log('Melody mode: ignoring overlapping note', midiNote);
        return;
      }
    }

    // Store note start time and velocity
    activeNotes.current.set(midiNote, {
      onTime: timestamp - recordingStartTime.current,
      velocity: velocity
    });

    // Update UI with last played note
    setLastNote({
      midi: midiNote,
      name: midiManager.constructor.midiToNoteName(midiNote),
      velocity: velocity
    });

    console.log(`✅ Note ON: ${midiManager.constructor.midiToNoteName(midiNote)} (${midiNote}) vel:${velocity.toFixed(2)}`);
  }, [mode, settings.chordMode]);

  /**
   * Handle note off event from MIDI
   */
  const handleNoteOff = useCallback((midiNote, channel) => {
    if (!isRecordingRef.current) return;

    if (!activeNotes.current.has(midiNote)) {
      console.warn('Note OFF without ON:', midiNote);
      return;
    }

    const timestamp = performance.now();
    const noteData = activeNotes.current.get(midiNote);
    const offTime = timestamp - recordingStartTime.current;
    const duration = offTime - noteData.onTime;

    // Store completed note
    const completedNote = {
      midi: midiNote,
      velocity: noteData.velocity,
      onTime: noteData.onTime,
      offTime: offTime,
      duration: duration
    };

    setRecordedNotes(prev => [...prev, completedNote]);
    activeNotes.current.delete(midiNote);

    console.log(`Note OFF: ${midiManager.constructor.midiToNoteName(midiNote)} duration:${duration.toFixed(0)}ms`);

    // Chord mode: auto-stop when all notes are released
    if (settings.chordMode && activeNotes.current.size === 0 && recordedNotes.length > 0) {
      console.log('🎵 Chord mode: All notes released, auto-stopping...');
      // Delay slightly to ensure state updates
      setTimeout(() => {
        if (isRecordingRef.current) {
          stopRecording();
        }
      }, 50);
    }
  }, [settings.chordMode, recordedNotes.length]);

  /**
   * Start recording
   */
  const startRecording = useCallback(() => {
    console.log('🔴 Starting MIDI recording...');

    recordingStartTime.current = performance.now();
    activeNotes.current.clear();
    setRecordedNotes([]);
    setLastNote(null);
    setElapsedTime(0);
    setIsRecording(true);
    isRecordingRef.current = true; // Update ref

    // Start timer
    timerInterval.current = setInterval(() => {
      setElapsedTime(prev => prev + 0.1);
    }, 100);

    // Register MIDI callbacks
    midiManager.onNoteOn(handleNoteOn);
    midiManager.onNoteOff(handleNoteOff);
  }, [handleNoteOn, handleNoteOff]);

  /**
   * Stop recording and process notes
   */
  const stopRecording = useCallback(() => {
    console.log('⏹ Stopping MIDI recording...');

    setIsRecording(false);
    isRecordingRef.current = false; // Update ref

    // Stop timer
    if (timerInterval.current) {
      clearInterval(timerInterval.current);
      timerInterval.current = null;
    }

    // Force close any active notes with default duration
    if (activeNotes.current.size > 0) {
      const timestamp = performance.now();
      const forcedNotes = [];

      activeNotes.current.forEach((noteData, midiNote) => {
        const offTime = timestamp - recordingStartTime.current;
        const duration = Math.max(offTime - noteData.onTime, 200); // Min 200ms

        forcedNotes.push({
          midi: midiNote,
          velocity: noteData.velocity,
          onTime: noteData.onTime,
          offTime: offTime,
          duration: duration
        });
      });

      setRecordedNotes(prev => [...prev, ...forcedNotes]);
      activeNotes.current.clear();

      console.log(`Forced close ${forcedNotes.length} active notes`);
    }

    // Clear MIDI callbacks
    midiManager.clearCallbacks();
  }, []);

  /**
   * Process recorded notes when recording stops
   */
  useEffect(() => {
    if (!isRecording && recordedNotes.length > 0) {
      // Process notes
      const processed = processRecording(recordedNotes, {
        mode: settings.quantizeMode,
        bpm: settings.bpm,
        quantizeDivision: settings.quantizeDivision,
        minNoteDuration: settings.minNoteDuration,
        normalizeVelocity: false,
        chordMode: settings.chordMode
      });

      console.log(`✅ Recording complete: ${recordedNotes.length} notes recorded, ${processed.length} after processing`);

      // Call completion callback with notes and settings
      if (onRecordingComplete && processed.length > 0) {
        onRecordingComplete(processed, { chordMode: settings.chordMode });
      }

      // Clear recorded notes after processing
      setRecordedNotes([]);
    }
  }, [isRecording, recordedNotes, settings, onRecordingComplete]);

  /**
   * Clear recording buffer
   */
  const clearRecording = useCallback(() => {
    setRecordedNotes([]);
    setLastNote(null);
    setElapsedTime(0);
    activeNotes.current.clear();
  }, []);

  /**
   * Update recording settings
   */
  const updateSettings = useCallback((newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
      midiManager.clearCallbacks();
    };
  }, []);

  return {
    // State
    isRecording,
    recordedNotes,
    noteCount: recordedNotes.length,
    lastNote,
    elapsedTime,
    settings,

    // Controls
    startRecording,
    stopRecording,
    clearRecording,
    updateSettings
  };
}

export default useMIDIRecorder;
