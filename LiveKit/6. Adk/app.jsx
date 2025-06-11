// app.jsx  ─ React + LiveKit client logic
// The whole file runs only after DOM is ready
window.addEventListener('DOMContentLoaded', () => {
  /* ---------- imports from globals ---------- */
  const { useState, useRef } = React;
  const { Room, RoomEvent } = LivekitClient;   // thanks to the alias

  /* ---------- configuration ---------- */
  const SERVER_URL = 'http://localhost:5000';
  const LIVEKIT_URL = 'wss://solvd-x191iqhu.livekit.cloud';

  /* ---------- helper: file → base64 ---------- */
  const toBase64 = (file) =>
    new Promise((res, rej) => {
      const rd = new FileReader();
      rd.onload = () => res(rd.result);
      rd.onerror = rej;
      rd.readAsDataURL(file);
    });

  /* ---------- main React component ---------- */
  function PhysicsAnalysisApp() {
    const [room, setRoom]               = useState(null);
    const [connected, setConnected]     = useState(false);
    const [roomName, setRoomName]       = useState('');
    const [status, setStatus]           = useState('Ready');
    const [statusType, setStatusType]   = useState('info');   // info | success | error
    const [participants, setParts]      = useState([]);
    const [file, setFile]               = useState(null);
    const [preview, setPreview]         = useState(null);
    const [analysis, setAnalysis]       = useState('');
    const [incoming, setIncoming]       = useState([]);
    const [busy, setBusy]               = useState(false);
    const [name, setName]               = useState('Student');

    const fileInput = useRef(null);

    /* ---------- LiveKit helpers ---------- */
    const refreshParts = (rm) => {
      setParts([rm.localParticipant, ...Array.from(rm.participants.values())]);
    };

    const wireEvents = (rm) => {
      rm.registerByteStreamHandler('image-analysis', async (reader, pInfo) => {
        const chunks = [];
        for await (const c of reader) chunks.push(c);
        const merged = new Uint8Array(chunks.reduce((s,c) => s+c.length,0));
        let off = 0; chunks.forEach(c => { merged.set(c,off); off+=c.length; });
        const txt = new TextDecoder().decode(merged);
        setIncoming(prev => [...prev, {
          who: pInfo.name || pInfo.identity,
          when: new Date().toLocaleTimeString(),
          txt
        }]);
        setStatus(`Analysis received from ${pInfo.name||pInfo.identity}`); setStatusType('success');
      });

      rm.on(RoomEvent.ParticipantConnected,  () => refreshParts(rm));
      rm.on(RoomEvent.ParticipantDisconnected,() => refreshParts(rm));
      rm.on(RoomEvent.Disconnected, (reason) => {
        setStatus(`Disconnected: ${reason||'unknown'}`); setStatusType('error');
        disconnect();
      });
      refreshParts(rm);
    };

    /* ---------- actions ---------- */
    const createRoom = async () => {
      try {
        setStatus('Creating room…'); setStatusType('info');
        const r = await fetch(`${SERVER_URL}/createRoom`,{method:'POST',headers:{'Content-Type':'application/json'}});
        const j = await r.json();
        if (!j.success) throw new Error(j.message);
        setRoomName(j.room); setStatus(`Room created: ${j.room}`); setStatusType('success');
      } catch (e) { setStatus(`Error: ${e.message}`); setStatusType('error'); }
    };

    const joinRoom = async () => {
      try {
        setStatus('Connecting…'); setStatusType('info');
        const id = `user-${Date.now()}`;
        const t = await (await fetch(`${SERVER_URL}/getToken?identity=${id}&name=${name}&room=${roomName}`)).text();
        const rm = new Room({adaptiveStream:true,dynacast:true});
        wireEvents(rm);
        await rm.connect(LIVEKIT_URL, t);
        await rm.localParticipant.setCameraEnabled(false);
        await rm.localParticipant.setMicrophoneEnabled(false);
        setRoom(rm); setConnected(true);
        setStatus(`Joined ${roomName}`); setStatusType('success');
      } catch(e){ setStatus(`Error: ${e.message}`); setStatusType('error'); }
    };

    const disconnect = async () => {
      if (room) await room.disconnect();
      setRoom(null); setConnected(false); setParts([]); setRoomName('');
    };

    const pickFile = (e) => {
      const f = e.target.files[0];
      if (!f) return;
      setFile(f); setPreview(URL.createObjectURL(f));
      setStatus(`Selected: ${f.name}`); setStatusType('info');
    };

    const analyse = async () => {
      if (!file || !connected) return;
      try {
        setBusy(true); setStatus('Analysing…'); setStatusType('info');
        const b64 = await toBase64(file);
        const res = await fetch(`${SERVER_URL}/analyze-image`,{
          method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({image:b64.split(',')[1],mime_type:file.type,room:roomName})
        }).then(r=>r.json());
        if(!res.success) throw new Error(res.error);
        setAnalysis(res.description);
        if (room){
          const w = await room.localParticipant.streamBytes('image-analysis');
          await w.write(new TextEncoder().encode(res.description)); await w.close();
        }
        setStatus('Analysis complete & shared'); setStatusType('success');
      } catch(e){ setStatus(`Error: ${e.message}`); setStatusType('error'); }
      finally{ setBusy(false); }
    };

    /* ---------- UI ---------- */
    return (
      <div className="physics-analysis-app">
        {/* status banner */}
        <div className={`status ${statusType}`}>{busy && '⏳ '} {status}</div>

        {/* controls */}
        <div className="controls">
          <h2>Room Controls</h2>
          <input value={name} onChange={e=>setName(e.target.value)} disabled={connected} placeholder="Your name"/>
          <div className="button-group" style={{marginTop:15}}>
            <button className="btn-primary" onClick={createRoom} disabled={connected||roomName}>Create</button>
            <button className="btn-primary" onClick={joinRoom}   disabled={connected||!roomName}>Join</button>
            <button className="btn-danger"  onClick={disconnect} disabled={!connected}>Leave</button>
          </div>
        </div>

        {/* upload */}
        <div className="controls">
          <h2>Image Upload</h2>
          <input ref={fileInput} style={{display:'none'}} type="file"
                 accept="image/*" onChange={pickFile}/>
          <div className="upload-area" onClick={()=>fileInput.current.click()}>
            {file ? `📄 ${file.name}` : '📁 Click to choose an image'}
          </div>
          {preview && <img className="image-preview" src={preview} alt="preview"/>}
          <button className="btn-primary" style={{width:'100%'}} disabled={!file||!connected||busy} onClick={analyse}>
            {busy ? 'Analysing…' : 'Analyse & Share'}
          </button>
        </div>

        {/* results */}
        {analysis && (
          <div className="analysis-result">
            <h3>Your Analysis</h3><p>{analysis}</p>
          </div>
        )}
        {incoming.length>0 && (
          <div className="analysis-result">
            <h3>Shared Analyses</h3>
            {incoming.map((m,i)=>(
              <p key={i}><strong>{m.who}</strong> [{m.when}]: {m.txt}</p>
            ))}
          </div>
        )}

        {/* participants */}
        <div className="participants">
          <h3>Participants ({participants.length})</h3>
          <div className="participants-list">
            {participants.map(p=>(
              <span key={p.identity} className="participant">
                {p.name||p.identity}{p.identity===room?.localParticipant.identity && ' (you)'}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  /* ---------- mount ---------- */
  ReactDOM.render(<PhysicsAnalysisApp/>, document.getElementById('app'));
});
