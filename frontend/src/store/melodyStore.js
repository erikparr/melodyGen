import { create } from 'zustand';

export const useMelodyStore = create((set, get) => ({
  // Data
  tracks: [],
  selectedMelodies: [],
  activeMelody: null,  // { trackId, melodyId } for the most recently selected/clicked melody
  playingMelody: null,  // { trackId, melodyId } for the currently playing melody
  loop: false,  // Global loop setting for individual playback, default OFF
  sequenceLoop: true,  // Loop the sequence playback, default ON
  importMode: 'single-track',  // 'multi-track' | 'single-track'
  targetLayer: 1,  // For single-track mode: 1, 2, or 3

  // Actions
  setTracks: (tracks) => set({ tracks }),

  setLoop: (loop) => set({ loop }),

  setSequenceLoop: (sequenceLoop) => set({ sequenceLoop }),

  setPlayingMelody: (trackId, melodyId) => {
    set({ playingMelody: trackId && melodyId ? { trackId, melodyId } : null });

    // Auto-clear after 100ms
    if (trackId && melodyId) {
      setTimeout(() => {
        set({ playingMelody: null });
      }, 100);
    }
  },

  setImportMode: (mode) => set({ importMode: mode }),

  setTargetLayer: (layer) => set({ targetLayer: layer }),

  selectMelody: (trackId, melodyId) => {
    const { selectedMelodies } = get();
    const exists = selectedMelodies.some(
      (sel) => sel.trackId === trackId && sel.melodyId === melodyId
    );

    if (!exists) {
      set({
        selectedMelodies: [...selectedMelodies, { trackId, melodyId }]
      });
    }
  },

  deselectMelody: (trackId, melodyId) => {
    set({
      selectedMelodies: get().selectedMelodies.filter(
        (sel) => !(sel.trackId === trackId && sel.melodyId === melodyId)
      )
    });
  },

  toggleMelody: (trackId, melodyId) => {
    const { selectedMelodies } = get();
    const exists = selectedMelodies.some(
      (sel) => sel.trackId === trackId && sel.melodyId === melodyId
    );

    if (exists) {
      get().deselectMelody(trackId, melodyId);
    } else {
      get().selectMelody(trackId, melodyId);
    }

    // Set as active melody
    set({ activeMelody: { trackId, melodyId } });
  },

  clearSelection: () => set({ selectedMelodies: [] }),

  selectAll: () => {
    const { tracks } = get();
    const allSelections = [];
    tracks.forEach(track => {
      track.melodies.forEach(melody => {
        allSelections.push({ trackId: track.id, melodyId: melody.id });
      });
    });
    set({ selectedMelodies: allSelections });
  },

  deleteMelodies: () => {
    const { tracks, selectedMelodies, activeMelody } = get();
    const newTracks = tracks.map(track => ({
      ...track,
      melodies: track.melodies.filter(melody =>
        !selectedMelodies.some(sel => sel.trackId === track.id && sel.melodyId === melody.id)
      )
    })).filter(track => track.melodies.length > 0);

    // Clear active melody if it was deleted
    const activeMelodyDeleted = activeMelody && selectedMelodies.some(
      sel => sel.trackId === activeMelody.trackId && sel.melodyId === activeMelody.melodyId
    );

    set({
      tracks: newTracks,
      selectedMelodies: [],
      activeMelody: activeMelodyDeleted ? null : activeMelody
    });
  },

  moveToNewLayer: () => {
    const { tracks, selectedMelodies, targetLayer } = get();

    if (selectedMelodies.length === 0) return;

    // Collect selected melodies
    const melodies = [];
    selectedMelodies.forEach(sel => {
      const track = tracks.find(t => t.id === sel.trackId);
      if (track) {
        const melody = track.melodies.find(m => m.id === sel.melodyId);
        if (melody) {
          melodies.push(melody);
        }
      }
    });

    // Create new track with selected melodies
    const newTrackId = `layer-${targetLayer}-${Date.now()}`;
    const newTrack = {
      id: newTrackId,
      name: `Layer ${targetLayer} (Moved)`,
      melodies: melodies,
      fixedLayer: targetLayer
    };

    // Add new track and select its melodies
    const newSelection = melodies.map(m => ({ trackId: newTrackId, melodyId: m.id }));
    set({
      tracks: [...tracks, newTrack],
      selectedMelodies: newSelection
    });
  },

  createNewMelody: () => {
    const { tracks, targetLayer } = get();
    const timestamp = Date.now();

    // Create new melody object
    const newMelody = {
      id: `new_melody_${timestamp}`,
      name: 'New Melody',
      notes: [],
      metadata: {
        totalDuration: 4.0,
        noteCount: 0,
        name: 'New Melody',
        key: 'C',
        scale: 'major',
        durationType: 'absolute',
        loop: false
      }
    };

    let updatedTracks;
    let trackId;

    if (tracks.length === 0) {
      // No tracks exist - create one
      trackId = `track_${timestamp}`;
      const newTrack = {
        id: trackId,
        name: 'Track 1',
        melodies: [newMelody]
      };
      updatedTracks = [newTrack];
    } else {
      // Add to first track
      trackId = tracks[0].id;
      updatedTracks = tracks.map((track, index) => {
        if (index === 0) {
          return {
            ...track,
            melodies: [...track.melodies, newMelody]
          };
        }
        return track;
      });
    }

    // Set as active and selected
    set({
      tracks: updatedTracks,
      activeMelody: { trackId, melodyId: newMelody.id },
      selectedMelodies: [{ trackId, melodyId: newMelody.id }]
    });
  },

  updateMelodyMetadata: (trackId, melodyId, updates) => {
    const { tracks } = get();

    const updatedTracks = tracks.map(track => {
      if (track.id === trackId) {
        return {
          ...track,
          melodies: track.melodies.map(melody => {
            if (melody.id === melodyId) {
              return {
                ...melody,
                metadata: {
                  ...melody.metadata,
                  ...updates
                }
              };
            }
            return melody;
          })
        };
      }
      return track;
    });

    set({ tracks: updatedTracks });
  },

  updateMelodyNotes: (trackId, melodyId, notes) => {
    const { tracks } = get();

    const updatedTracks = tracks.map(track => {
      if (track.id === trackId) {
        return {
          ...track,
          melodies: track.melodies.map(melody => {
            if (melody.id === melodyId) {
              // Calculate total duration from notes
              const totalDuration = notes.length > 0
                ? Math.max(...notes.map(n => (n.time || 0) + (n.duration || 0)))
                : (melody.metadata?.totalDuration || 0);

              return {
                ...melody,
                notes: notes,
                metadata: {
                  ...melody.metadata,
                  noteCount: notes.length,
                  totalDuration: totalDuration
                }
              };
            }
            return melody;
          })
        };
      }
      return track;
    });

    set({ tracks: updatedTracks });
  },

  // Load data from JSON
  loadFromJSON: (jsonData) => {
    const { importMode, targetLayer } = get();
    const allMelodies = [];
    const tracks = [];
    const selectedMelodies = [];

    if (jsonData.melodies) {
      Object.entries(jsonData.melodies).forEach(([melodyName, melodyData]) => {
        const melodies = [];

        // Check if this is variations format (has original/variations)
        if (melodyData.original || melodyData.variations) {
          // Add original
          if (melodyData.original?.layer1) {
            melodies.push({
              id: `${melodyName}_original`,
              name: 'Original',
              notes: convertJSONNotesToInternal(melodyData.original.layer1),
              metadata: melodyData.original.layer1.metadata
            });
          }

          // Add variations
          if (melodyData.variations) {
            Object.entries(melodyData.variations).forEach(([varId, varData]) => {
              melodies.push({
                id: `${melodyName}_${varId}`,
                name: varData.method || varId,
                notes: convertJSONNotesToInternal(varData.layer1),
                metadata: varData.layer1.metadata
              });
            });
          }
        } else if (melodyData.layers?.layer1) {
          // This is input format - just has layers
          melodies.push({
            id: `${melodyName}_original`,
            name: 'Original',
            notes: convertJSONNotesToInternal(melodyData.layers.layer1),
            metadata: melodyData.layers.layer1.metadata
          });
        }

        if (importMode === 'single-track') {
          // Collect all melodies for single track
          allMelodies.push(...melodies);
        } else {
          // Multi-track mode: each melody gets its own track
          if (melodies.length > 0) {
            const trackId = melodyName;
            tracks.push({
              id: trackId,
              name: melodyName,
              melodies
            });
            // Select all melodies in this track
            melodies.forEach(melody => {
              selectedMelodies.push({ trackId, melodyId: melody.id });
            });
          }
        }
      });
    }

    if (importMode === 'single-track' && allMelodies.length > 0) {
      // Create one track with all melodies
      const trackId = 'merged-track';
      const newTrack = {
        id: trackId,
        name: `All Melodies (Layer ${targetLayer})`,
        melodies: allMelodies,
        fixedLayer: targetLayer
      };
      // Select all melodies in single track
      allMelodies.forEach(melody => {
        selectedMelodies.push({ trackId, melodyId: melody.id });
      });
      set({
        tracks: [newTrack],
        selectedMelodies
      });
    } else {
      // Multi-track mode: limit to 5 tracks max
      set({
        tracks: tracks.slice(0, 5),
        selectedMelodies: selectedMelodies.slice(0, 5 * 20) // Reasonable limit
      });
    }
  }
}));

/**
 * Convert JSON layer format to internal format
 * Input: { notes: [{midi, vel, dur}], timing: [...], metadata }
 * Output: [{midi, time, duration, velocity}]
 */
function convertJSONNotesToInternal(layer) {
  const { notes, timing, metadata } = layer;
  const totalDuration = metadata.totalDuration;

  const internalNotes = [];
  let currentTime = 0;

  notes.forEach((note, i) => {
    // Calculate time from timing array
    if (i < timing.length) {
      currentTime += timing[i] * totalDuration;
    }

    // Convert duration
    let duration = note.dur;
    if (metadata.durationType === 'fractional' && i < notes.length - 1) {
      const timeToNext = timing[i + 1] * totalDuration;
      duration = note.dur * timeToNext;
    }

    internalNotes.push({
      midi: note.midi,
      time: currentTime,
      duration: duration,
      velocity: note.vel
    });
  });

  return internalNotes;
}
