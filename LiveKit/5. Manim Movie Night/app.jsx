// app.jsx
/**
 * LiveKit Movie Night - React Version with Play Button Control
 * 
 * This app allows users to:
 * 1. Create movie rooms for different animations
 * 2. Join rooms to watch Manim animations
 * 3. Control when the video + narration starts with a Play button
 * 4. Hear synchronized narration from the Movie Night Agent
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Room,
  RoomEvent,
  Track,
  RemoteTrack,
  RemoteParticipant,
  LocalParticipant,
  VideoPresets,
  createLocalTracks,
} from 'livekit-client';

// Configuration
const SERVER_URL = "http://localhost:5000";
const LIVEKIT_URL = "wss://solvd-x191iqhu.livekit.cloud"; // Update with your URL

// Main App Component
function MovieNightApp() {
  // State management
  const [room, setRoom] = useState(null);
  const [connected, setConnected] = useState(false);
  const [currentRoomName, setCurrentRoomName] = useState('');
  const [participants, setParticipants] = useState([]);
  const [status, setStatus] = useState('Ready to create a room');
  const [videoTrack, setVideoTrack] = useState(null);
  const [audioTracks, setAudioTracks] = useState([]);
  
  // ← CHANGED: NEW state for gating play
  const [isReadyToPlay, setIsReadyToPlay] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Form state
  const [userName, setUserName] = useState('Student');
  const [selectedAnimation, setSelectedAnimation] = useState('projectile');
  
  // Video ref for manual attachment
  const videoRef = useRef(null);
  
  // Helper function for status updates
  const updateStatus = useCallback((msg, isError = false) => {
    setStatus(msg);
    if (isError) {
      console.error(msg);
    } else {
      console.log(msg);
    }
  }, []);

  /**
   * Create a new movie room
   * This tells the server to prepare a room for the selected animation
   */
  const createRoom = async () => {
    try {
      updateStatus('Creating room...');
      
      const response = await fetch(`${SERVER_URL}/createMovieRoom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ animation: selectedAnimation })
      });
      
      const data = await response.json();
      if (data.success) {
        setCurrentRoomName(data.room);
        updateStatus(`Room created: ${data.room}`);
      } else {
        throw new Error(data.message || 'Failed to create room');
      }
    } catch (error) {
      updateStatus(`Error: ${error.message}`, true);
    }
  };
  
  /**
   * Join the movie room
   * This connects to LiveKit and subscribes to tracks from the Movie Night Agent
   */
  const joinRoom = async () => {
    try {
      updateStatus('Connecting to room...');
      
      // Generate unique identity for this user
      const identity = `user-${Date.now()}`;
      
      // Get access token from server
      const tokenResponse = await fetch(
        `${SERVER_URL}/getToken?identity=${identity}&name=${encodeURIComponent(userName)}&room=${currentRoomName}`
      );
      const token = await tokenResponse.text();
      
      // Create new LiveKit Room instance
      const newRoom = new Room({
        // Audio settings for better quality
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: true,
        },
        // Video settings
        videoCaptureDefaults: {
          resolution: VideoPresets.h720.resolution,
        },
        // Enable adaptive streaming for better performance
        adaptiveStream: true,
        // Automatically manage video quality based on bandwidth
        dynacast: true,
      });
      
      // Set up event handlers before connecting
      setupRoomEventHandlers(newRoom);
      
      // Connect to the LiveKit room
      await newRoom.connect(LIVEKIT_URL, token);
      
      // For movie night, participants don't need camera/mic
      // They're just watching the agent's stream
      await newRoom.localParticipant.setCameraEnabled(false);
      await newRoom.localParticipant.setMicrophoneEnabled(false);
      
      setRoom(newRoom);
      setConnected(true);
      updateStatus(`Connected to ${currentRoomName}`);
      
    } catch (error) {
      updateStatus(`Error: ${error.message}`, true);
    }
  };
  
  /**
   * Set up all event handlers for the room
   * ← CHANGED: Collect tracks but don't attach them immediately
   */
  const setupRoomEventHandlers = (room) => {
    /**
     * Handle track subscribed events
     * This fires when we receive video or audio from the Movie Night Agent
     */
    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log(`Track subscribed: ${track.kind} from ${participant.identity}`);
      
      // Handle video tracks (the Manim animation) - collect but don't attach
      if (track.kind === Track.Kind.Video) {
        setVideoTrack(track);
        updateStatus(`Video ready from ${participant.identity}`);
      }
      
      // Handle audio tracks (the narration) - collect but don't attach
      if (track.kind === Track.Kind.Audio) {
        setAudioTracks(prev => [...prev, track]);
        updateStatus(`Audio ready from ${participant.identity}`);
      }
      
      // ← CHANGED: Once we have tracks, show the Play button
      setIsReadyToPlay(true);
    });
    
    /**
     * Handle track unsubscribed
     * This fires when a track stops (e.g., video ends)
     */
    room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      console.log(`Track unsubscribed: ${track.kind} from ${participant.identity}`);
      
      if (track.kind === Track.Kind.Video) {
        setVideoTrack(null);
        updateStatus('Video ended');
      }
      
      // Clean up audio when it ends
      if (track.kind === Track.Kind.Audio) {
        track.detach().forEach((el) => el.remove());
        setAudioTracks(prev => prev.filter(t => t !== track));
      }
    });
    
    /**
     * Handle participant events
     * Track who's in the room (including the agent)
     */
    room.on(RoomEvent.ParticipantConnected, (participant) => {
      console.log(`${participant.identity} joined`);
      updateParticipants(room);
    });
    
    room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      console.log(`${participant.identity} left`);
      updateParticipants(room);
    });
    
    /**
     * Handle disconnection
     */
    room.on(RoomEvent.Disconnected, (reason) => {
      updateStatus(`Disconnected: ${reason || 'unknown reason'}`);
      cleanupRoom();
    });
    
    // Initial participants update
    updateParticipants(room);
  };
  
  /**
   * Update the list of participants in the room
   */
  const updateParticipants = (room) => {
    const allParticipants = [
      room.localParticipant,
      ...Array.from(room.participants.values())
    ];
    setParticipants(allParticipants.filter(Boolean));
  };
  
  /**
   * ← CHANGED: Handle Play button click - attach tracks when user is ready
   */
  const handlePlay = () => {
    // Attach video track to video element
    if (videoTrack && videoRef.current) {
      videoTrack.attach(videoRef.current);
    }
    
    // Attach audio tracks (hidden audio elements)
    audioTracks.forEach(track => {
      const el = track.attach();
      el.autoplay = true;
      el.controls = false;
      el.style.display = 'none';
      document.body.appendChild(el);
    });
    
    setIsPlaying(true);
    updateStatus('Playing animation 🎬');
  };
  
  /**
   * Leave the room and clean up
   */
  const leaveRoom = async () => {
    if (room) {
      await room.disconnect();
      cleanupRoom();
    }
  };
  
  /**
   * Clean up after leaving room
   * ← CHANGED: Reset play state as well
   */
  const cleanupRoom = () => {
    setRoom(null);
    setConnected(false);
    setVideoTrack(null);
    setAudioTracks([]);
    setParticipants([]);
    setCurrentRoomName('');
    setStatus('Disconnected');
    setIsReadyToPlay(false);
    setIsPlaying(false);
  };
  
  // Render the UI
  return (
    <div className="movie-night-app">
      <h1>🎬 Manim Movie Night</h1>
      
      <div className="instructions">
        <strong>How it works:</strong>
        <ol>
          <li>Choose your name and select an animation</li>
          <li>Click "Create Room" to set up a movie room</li>
          <li>Click "Join Room" to enter and wait for content</li>
          <li>Click "Play" when ready to start the animation with narration!</li>
        </ol>
      </div>
      
      <div className="controls">
        <h2>Room Controls</h2>
        
        <div className="control-group">
          <label htmlFor="nameInput">Your Name:</label>
          <input
            id="nameInput"
            type="text"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            disabled={connected}
          />
        </div>
        
        <div className="control-group">
          <label htmlFor="animationSelect">Animation:</label>
          <select
            id="animationSelect"
            value={selectedAnimation}
            onChange={(e) => setSelectedAnimation(e.target.value)}
            disabled={connected || currentRoomName}
          >
            <option value="projectile">Projectile Motion</option>
            <option value="pendulum">Pendulum</option>
            <option value="waves">Wave Motion</option>
          </select>
        </div>
        
        <div className="control-group">
          <button
            onClick={createRoom}
            disabled={connected || currentRoomName}
          >
            Create Room
          </button>
          <button
            onClick={joinRoom}
            disabled={connected || !currentRoomName}
          >
            Join Room
          </button>
          <button
            onClick={leaveRoom}
            disabled={!connected}
          >
            Leave Room
          </button>
        </div>
      </div>
      
      <div className="status">
        Status: {status}
      </div>
      
      {/* ← CHANGED: Show Play button only when ready and not yet playing */}
      {connected && isReadyToPlay && !isPlaying && (
        <div className="play-control">
          <button 
            onClick={handlePlay}
            className="play-button"
            style={{
              fontSize: '1.2rem',
              padding: '12px 24px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              margin: '20px 0'
            }}
          >
            ▶️ Play Animation & Narration
          </button>
        </div>
      )}
      
      {/* ← CHANGED: Video Display with conditional rendering */}
      <div className="video-container">
        {isPlaying ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            style={{ width: '100%', maxWidth: '800px' }}
          />
        ) : (
          <div className="video-placeholder" style={{
            width: '100%',
            maxWidth: '800px',
            height: '400px',
            backgroundColor: '#f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px dashed #ccc',
            borderRadius: '8px'
          }}>
            <p>Video will appear here when you click Play</p>
          </div>
        )}
      </div>
      
      {/* Participants List */}
      <div className="participants">
        <h3>Participants</h3>
        <div className="participants-list">
          {participants.length > 0 ? (
            participants.map(p => (
              <span key={p.identity} className="participant" style={{
                display: 'inline-block',
                margin: '4px 8px',
                padding: '4px 8px',
                backgroundColor: '#e7e7e7',
                borderRadius: '4px'
              }}>
                {p.name || p.identity}
                {(p.identity === 'agent' || p.name === 'Movie Night Agent') && ' 🤖'}
              </span>
            ))
          ) : (
            <span className="participant">No one in room yet</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MovieNightApp;