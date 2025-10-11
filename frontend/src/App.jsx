import React from 'react';
import ControlBar from './components/ControlBar';
import TrackList from './components/TrackList';
import BottomControlBar from './components/BottomControlBar';
import './App.css';

function App() {
  return (
    <div className="app">
      <ControlBar />
      <TrackList />
      <BottomControlBar />
    </div>
  );
}

export default App;
