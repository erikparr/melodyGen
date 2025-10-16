import React from 'react';
import ControlBar from './components/ControlBar';
import TrackList from './components/TrackList';
import ActiveMelodyViewer from './components/ActiveMelodyViewer';
import BottomControlBar from './components/BottomControlBar';
import './App.css';

function App() {
  return (
    <div className="app">
      <ControlBar />
      <TrackList />
      <ActiveMelodyViewer />
      <BottomControlBar />
    </div>
  );
}

export default App;
