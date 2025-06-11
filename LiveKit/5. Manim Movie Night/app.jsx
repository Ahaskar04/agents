// app.jsx
/**
 * LiveKit Movie Night - React Version
 * 
 * This app allows users to:
 * 1. Create movie rooms for different animations
 * 2. Join rooms to watch Manim animations
 * 3. Hear synchronized narration from the Movie Night Agent
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  
  // Form state
  const [userName, setUserName] = useState('Student');
  const [selectedAnimation, setSelectedAnimation] = useState('projectile');
  
  /**
   * Create a new movie room
   * This tells the server to prepare a room for the selected animation
   */
  const createRoom = async () => {
    try {
      setStatus('Creating room...');
      
      const response = await fetch(`${SERVER_URL}/createMovieRoom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ animation: selectedAnimation })
      });
      
      const data = await response.json();
      if (data.success) {
        setCurrentRoomName(data.room);
        setStatus(`Room created: ${data.room}`);
      } else {
        throw new Error(data.message || 'Failed to create room');
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`);
      console.error('Create room error:', error);
    }
  };
  
  /**
   * Join the movie room
   * This connects to LiveKit and subscribes to tracks from the Movie Night Agent
   */
  const joinRoom = async () => {
    try {
      setStatus('Connecting to room...');
      
      // Generate unique identity for this user
      const identity = `user-${Date.now()}`;
      
      // Get access token from server
      const tokenResponse = await fetch(
        `${SERVER_URL}/getToken?identity=${identity}&name=${userName}&room=${currentRoomName}`
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
      setStatus(`Connected to ${currentRoomName}`);
      
    } catch (error) {
      setStatus(`Error: ${error.message}`);
      console.error('Join error:', error);
    }
  };
  
  /**
   * Set up all event handlers for the room
   * This is where we handle incoming video/audio from the agent
   */
  const setupRoomEventHandlers = (room) => {
    /**
     * Handle track subscribed events
     * This fires when we receive video or audio from the Movie Night Agent
     */
    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log(`Track subscribed: ${track.kind} from ${participant.identity}`);
      
      // Handle video tracks (the Manim animation)
      if (track.kind === Track.Kind.Video) {
        setVideoTrack(track);
        setStatus(`Receiving video from ${participant.identity}`);
      }
      
      // Handle audio tracks (the narration)
      if (track.kind === Track.Kind.Audio) {
        // Audio tracks play automatically when attached
        // But we'll track them for volume control if needed
        setAudioTracks(prev => [...prev, track]);
        console.log(`Audio narration started from ${participant.identity}`);
      }
    });
    
    /**
     * Handle track unsubscribed
     * This fires when a track stops (e.g., video ends)
     */
    room.on(RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
      console.log(`Track unsubscribed: ${track.kind} from ${participant.identity}`);
      
      if (track.kind === Track.Kind.Video) {
        setVideoTrack(null);
        setStatus('Video ended');
      }
      
      if (track.kind === Track.Kind.Audio) {
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
      setStatus(`Disconnected: ${reason || 'unknown reason'}`);
      setConnected(false);
      setVideoTrack(null);
      setAudioTracks([]);
      handleLeaveRoom();
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
    setParticipants(allParticipants);
  };
  
  /**
   * Leave the room and clean up
   */
  const leaveRoom = async () => {
    if (room) {
      await room.disconnect();
      handleLeaveRoom();
    }
  };
  
  /**
   * Clean up after leaving room
   */
  const handleLeaveRoom = () => {
    setRoom(null);
    setConnected(false);
    setVideoTrack(null);
    setAudioTracks([]);
    setParticipants([]);
    setCurrentRoomName('');
    setStatus('Disconnected');
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
          <li>Click "Join Room" to enter and watch</li>
          <li>The Movie Night Agent will stream the video with narration!</li>
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
            <option value="pendulum">Pendulum (Coming Soon)</option>
            <option value="waves">Wave Motion (Coming Soon)</option>
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
      
      {/* Video Display Component */}
      <VideoDisplay videoTrack={videoTrack} />
      
      {/* Participants List */}
      <div className="participants">
        <h3>Participants</h3>
        <div className="participants-list">
          {participants.length > 0 ? (
            participants.map(p => (
              <span key={p.identity} className="participant">
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

/**
 * Video Display Component
 * Handles rendering the video track from the Movie Night Agent
 */
function VideoDisplay({ videoTrack }) {
  const videoRef = React.useRef(null);
  
  useEffect(() => {
    if (videoTrack && videoRef.current) {
      // Attach the video track to the video element
      videoTrack.attach(videoRef.current);
      
      // Cleanup function to detach when component unmounts or track changes
      return () => {
        videoTrack.detach();
      };
    }
  }, [videoTrack]);
  
  return (
    <div className="video-container">
      {videoTrack ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{ width: '100%', maxWidth: '800px' }}
        />
      ) : (
        <div className="video-placeholder">
          <p>Video will appear here when you join a room</p>
        </div>
      )}
    </div>
  );
}

export default MovieNightApp;