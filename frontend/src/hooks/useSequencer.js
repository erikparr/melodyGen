import { useState, useEffect, useRef } from 'react';
import { useMelodyStore } from '../store/melodyStore';
import { sendMelodyToLayer } from '../utils/oscSender';

export function useSequencer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const wsRef = useRef(null);
  const playNextRef = useRef(null);

  const tracks = useMelodyStore((state) => state.tracks);
  const selectedMelodies = useMelodyStore((state) => state.selectedMelodies);
  const loop = useMelodyStore((state) => state.loop);

  // Get the ordered list of melodies to play
  const getPlaylist = () => {
    const playlist = [];

    // Group by track and get the most recent selection per track
    const melodiesByTrack = {};
    selectedMelodies.forEach(sel => {
      if (!melodiesByTrack[sel.trackId]) {
        melodiesByTrack[sel.trackId] = [];
      }
      melodiesByTrack[sel.trackId].push(sel.melodyId);
    });

    // For each track, add all selected melodies to playlist
    Object.entries(melodiesByTrack).forEach(([trackId, melodyIds]) => {
      const track = tracks.find(t => t.id === trackId);
      if (!track) return;

      const trackIndex = tracks.indexOf(track);
      const layer = ((trackIndex) % 3) + 1;

      melodyIds.forEach(melodyId => {
        const melody = track.melodies.find(m => m.id === melodyId);
        if (melody) {
          playlist.push({
            melody,
            layer,
            trackId,
            trackName: track.name
          });
        }
      });
    });

    return playlist;
  };

  const playlist = getPlaylist();

  // Define playNext and keep ref updated
  const playNext = () => {
    const { sequenceLoop } = useMelodyStore.getState();

    setCurrentIndex((prev) => {
      const next = prev + 1;

      if (next >= playlist.length) {
        // Reached end of playlist
        if (sequenceLoop) {
          // Loop back to start
          return 0;
        } else {
          // Stop playing
          setIsPlaying(false);
          return 0;
        }
      }
      return next;
    });
  };

  // Update ref whenever playNext changes
  useEffect(() => {
    playNextRef.current = playNext;
  });

  // Connect to WebSocket for completion events
  useEffect(() => {
    if (!isPlaying) return;

    const ws = new WebSocket('ws://localhost:8000/ws/completions');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('🔌 Connected to completion WebSocket');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('✅ Received completion event:', data);

      // Play next melody in sequence using ref to get latest function
      if (playNextRef.current) {
        playNextRef.current();
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('🔌 Disconnected from completion WebSocket');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [isPlaying]);

  const playCurrent = async () => {
    if (playlist.length === 0) {
      setIsPlaying(false);
      return;
    }

    const item = playlist[currentIndex];
    if (!item) {
      setIsPlaying(false);
      return;
    }

    try {
      // Set the playing melody to trigger flash animation
      useMelodyStore.getState().setPlayingMelody(item.trackId, item.melody.id);

      await sendMelodyToLayer(item.melody, item.layer, false); // Always one-shot for sequencer
      console.log(`🎵 Sequencer: Playing ${item.melody.name} on layer ${item.layer} (${currentIndex + 1}/${playlist.length})`);
    } catch (error) {
      console.error('Failed to send melody:', error);
      setIsPlaying(false);
    }
  };

  // When index changes and we're playing, send the next melody
  useEffect(() => {
    if (isPlaying && playlist.length > 0) {
      playCurrent();
    }
  }, [currentIndex, isPlaying]);

  const start = () => {
    if (playlist.length === 0) {
      alert('No melodies selected');
      return;
    }
    setCurrentIndex(0);
    setIsPlaying(true);
  };

  const stop = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
  };

  return {
    isPlaying,
    currentIndex,
    playlist,
    start,
    stop
  };
}
