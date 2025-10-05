import React from 'react';
import ControlBar from './components/ControlBar';
import TrackList from './components/TrackList';
import './App.css';

function App() {
  return (
    <div className="app">
      <ControlBar />
      <TrackList />
    </div>
  );
}

export default App;
