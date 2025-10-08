import { create } from 'zustand';

export const useMelodyStore = create((set, get) => ({
  // Data
  tracks: [],
  selectedMelodies: [],
  loop: false,  // Global loop setting, default OFF

  // Actions
  setTracks: (tracks) => set({ tracks }),

  setLoop: (loop) => set({ loop }),

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
  },

  clearSelection: () => set({ selectedMelodies: [] }),

  // Load data from JSON
  loadFromJSON: (jsonData) => {
    const tracks = [];

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

        if (melodies.length > 0) {
          tracks.push({
            id: melodyName,
            name: melodyName,
            melodies
          });
        }
      });
    }

    // Limit to 5 tracks max
    set({ tracks: tracks.slice(0, 5) });
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
