import { useState, useCallback } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import { sendMelodyToLayer } from '../utils/oscSender';

/**
 * Hook for simultaneous multi-track playback.
 * Each track loops independently at its own rate.
 */
export function useMultiTrackPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playingTracks, setPlayingTracks] = useState(new Map()); // trackId -> melodyId

  const tracks = useMelodyStore(state => state.tracks);
  const selectedMelodies = useMelodyStore(state => state.selectedMelodies);
  const setPlayingMelody = useMelodyStore(state => state.setPlayingMelody);

  /**
   * Get one melody per track from selections.
   * Uses first selected melody from each track.
   */
  const getTrackPlaylist = useCallback(() => {
    const melodiesByTrack = {};

    // Group selections by track
    selectedMelodies.forEach(sel => {
      if (!melodiesByTrack[sel.trackId]) {
        melodiesByTrack[sel.trackId] = [];
      }
      melodiesByTrack[sel.trackId].push(sel.melodyId);
    });

    // Build playlist: one melody per track
    const playlist = [];
    Object.entries(melodiesByTrack).forEach(([trackId, melodyIds]) => {
      const track = tracks.find(t => t.id === trackId);
      if (!track) return;

      // Use first selected melody from this track
      const melodyId = melodyIds[0];
      const melody = track.melodies.find(m => m.id === melodyId);
      if (!melody) return;

      const trackIndex = tracks.indexOf(track);
      const layer = track.fixedLayer || ((trackIndex) % 3) + 1;
      const targetGroup = track.targetGroup ?? trackIndex;
      const oscType = track.oscType || 'melody';

      playlist.push({
        track,
        melody,
        layer,
        targetGroup,
        oscType,
        trackId,
        melodyId
      });
    });

    return playlist;
  }, [tracks, selectedMelodies]);

  /**
   * Start all tracks simultaneously with looping enabled.
   */
  const startAll = useCallback(async () => {
    const playlist = getTrackPlaylist();

    if (playlist.length === 0) {
      alert('No melodies selected');
      return;
    }

    console.log('🎵 Starting simultaneous playback for', playlist.length, 'tracks');

    try {
      // Send all tracks simultaneously with loop=true
      const sendPromises = playlist.map(async (item) => {
        // Trigger flash animation
        setPlayingMelody(item.trackId, item.melodyId);

        return sendMelodyToLayer(item.melody, item.layer, true, item.targetGroup, item.oscType);
      });

      await Promise.all(sendPromises);

      // Track which melodies are playing
      const playing = new Map();
      playlist.forEach(item => {
        playing.set(item.trackId, item.melodyId);
        console.log(`  ✓ Track ${item.targetGroup} (${item.track.name}): ${item.melody.name}`);
      });

      setPlayingTracks(playing);
      setIsPlaying(true);

    } catch (error) {
      console.error('Failed to start multi-track playback:', error);
      alert('Failed to start playback');
    }
  }, [getTrackPlaylist, setPlayingMelody]);

  /**
   * Stop all tracks gracefully (after current iteration).
   */
  const stopAll = useCallback(async () => {
    console.log('⏹ Stopping all tracks');

    try {
      const response = await fetch('http://localhost:8000/osc/stop-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();

      if (result.success) {
        setPlayingTracks(new Map());
        setIsPlaying(false);
        console.log('✓ All tracks stopped');
      }
    } catch (error) {
      console.error('Failed to stop tracks:', error);
    }
  }, []);

  /**
   * Stop a specific track gracefully (after current iteration).
   */
  const stopTrack = useCallback(async (trackId) => {
    const track = tracks.find(t => t.id === trackId);
    if (!track) return;

    const targetGroup = tracks.indexOf(track);
    console.log(`⏹ Stopping track ${targetGroup}`);

    try {
      const response = await fetch(`http://localhost:8000/osc/stop-track?target_group=${targetGroup}`, {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        const newPlaying = new Map(playingTracks);
        newPlaying.delete(trackId);
        setPlayingTracks(newPlaying);

        if (newPlaying.size === 0) {
          setIsPlaying(false);
        }
      }
    } catch (error) {
      console.error('Failed to stop track:', error);
    }
  }, [tracks, playingTracks]);

  return {
    isPlaying,
    playingTracks,
    startAll,
    stopAll,
    stopTrack,
    trackCount: getTrackPlaylist().length
  };
}

export default useMultiTrackPlayer;
