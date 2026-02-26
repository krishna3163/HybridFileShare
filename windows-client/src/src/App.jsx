import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import QRCode from 'qrcode.react';

const App = () => {
  const [mode, setMode] = useState('home'); // home, share, receive
  const [deviceId, setDeviceId] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [nearbyDevices, setNearbyDevices] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [qrCode, setQrCode] = useState('');
  const [pin, setPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [progress, setProgress] = useState(0);
  const [transferring, setTransferring] = useState(false);
  const fileInputRef = useRef(null);

  // Initialize device
  useEffect(() => {
    const id = `web-${Math.random().toString(36).substr(2, 9)}`;
    setDeviceId(id);
    setDeviceName(
      `${navigator.platform.includes('Win') ? '🖥️' : navigator.platform.includes('Mac') ? '🍎' : '🐧'} ${navigator.platform}`
    );

    // Start device discovery
    discoverNearbyDevices();
    const interval = setInterval(discoverNearbyDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  // Generate QR code and PIN
  const generateQrAndPin = () => {
    const pin = Math.random().toString().slice(2, 8);
    setPin(pin);

    const qrData = {
      deviceId,
      deviceName,
      pin,
      timestamp: Date.now(),
    };

    setQrCode(JSON.stringify(qrData));
    return pin;
  };

  // Discover nearby devices
  const discoverNearbyDevices = async () => {
    try {
      const response = await fetch('/api/discover-devices');
      const devices = await response.json();
      setNearbyDevices(devices.filter((d) => d.deviceId !== deviceId));
    } catch (error) {
      console.debug('Device discovery:', error);
    }
  };

  // Handle file selection
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFile(files);
    if (files.length > 0) {
      // Auto-start transfer simulation if multiple files or large file
      setTransferring(true);
      let p = 0;
      const interval = setInterval(() => {
        p += 5;
        setProgress(p);
        if (p >= 100) {
          clearInterval(interval);
          setTransferring(false);
          setProgress(0);
          setSelectedFile(null);
        }
      }, 500);
    }
  };

  // Send files
  const sendFiles = async (targetDevice) => {
    if (!selectedFile || selectedFile.length === 0) {
      alert('Please select files first');
      return;
    }
    setTransferring(true);
    // Simulation for demo
    let p = 0;
    const interval = setInterval(() => {
      p += 2;
      setProgress(p);
      if (p >= 100) {
        clearInterval(interval);
        setTransferring(false);
        setProgress(0);
        setSelectedFile(null);
      }
    }, 200);
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <img src="/logo.png" alt="Logo" style={{ width: '30px' }} />
        </div>
        <div className={`nav-item ${mode === 'home' ? 'active' : ''}`} onClick={() => setMode('home')}>
          <span style={{ fontSize: '20px' }}>🏠</span>
          <span style={{ fontSize: '10px' }}>Dashboard</span>
        </div>
        <div className={`nav-item ${mode === 'share' ? 'active' : ''}`} onClick={() => setMode('share')}>
          <span style={{ fontSize: '20px' }}>📤</span>
          <span style={{ fontSize: '10px' }}>Transfer</span>
        </div>
        <div className={`nav-item ${mode === 'receive' ? 'active' : ''}`} onClick={() => setMode('receive')}>
          <span style={{ fontSize: '20px' }}>📥</span>
          <span style={{ fontSize: '10px' }}>History</span>
        </div>
        <div className="nav-item">
          <span style={{ fontSize: '20px' }}>⚙️</span>
          <span style={{ fontSize: '10px' }}>Settings</span>
        </div>
      </aside>

      {/* Main Wrapper */}
      <main className="main-wrapper">
        <header className="top-header">
          <div className="project-brand">
            <span className="project-title">HybridFileShare</span>
            <div className="top-nav">
              <span style={{ color: 'white', borderBottom: '2px solid var(--primary)', paddingBottom: '4px' }}>Dashboard</span>
              <span style={{ color: 'var(--text-dim)' }}>History</span>
              <span style={{ color: 'var(--text-dim)' }}>Settings</span>
            </div>
          </div>
          <div className="header-actions">
            <span style={{ fontSize: '20px', cursor: 'pointer' }}>🔔</span>
            <div className="user-profile">
              <img src="/logo.png" className="avatar" alt="User" />
              <span style={{ fontSize: '14px', fontWeight: 'bold' }}>Asish</span>
              <span style={{ fontSize: '12px' }}>▼</span>
            </div>
          </div>
        </header>

        <div className="content-area">
          {/* Hero Banner */}
          <section className="hero-banner">
            <div style={{ position: 'relative' }}>
              <img src="/logo.png" alt="Big Logo" style={{ width: '100px', marginBottom: '16px', filter: 'drop-shadow(0 0 20px var(--primary))' }} />
            </div>
            <h1 style={{ fontSize: '38px', marginBottom: '8px', fontWeight: '900', letterSpacing: '-1px' }}>HybridFileShare</h1>
            <p style={{ opacity: 0.8, fontSize: '16px', fontWeight: '500' }}>Share with WiFi + USB at same time</p>
          </section>

          {/* Dashboard Grid */}
          <div className="dashboard-grid">
            {/* Left Column: Nearby Devices */}
            <div className="dashboard-panel">
              <div className="panel-header">
                <span className="panel-title">Nearby Devices</span>
                <span style={{ fontSize: '12px', color: 'var(--accent)' }}>Receive Mode 🔘</span>
              </div>
              <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
                {nearbyDevices.length > 0 ? (
                  nearbyDevices.map((device) => (
                    <div key={device.deviceId} className="device-item-new" onClick={() => sendFiles(device)}>
                      <div className="device-avatar">
                        {device.type === 'android' ? '📱' : '🖥️'}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{device.deviceName}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{device.host || 'Strong Connection'}</div>
                      </div>
                      <div className="device-status-dot"></div>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="device-item-new">
                      <div className="device-avatar">📱</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'bold', fontSize: '14px' }}>Ashish's Samsung</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>S24 Ultra · Strong</div>
                      </div>
                      <div className="device-status-dot"></div>
                    </div>
                    <div className="device-item-new">
                      <div className="device-avatar">🖥️</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 'bold', fontSize: '14px' }}>Vikram's PC</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Desktop · OK</div>
                      </div>
                      <div className="device-status-dot" style={{ background: 'var(--warning)' }}></div>
                    </div>
                  </>
                )}
              </div>

              <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                <button style={{ flex: 1, padding: '12px', borderRadius: '12px', border: '1px solid var(--primary)', background: 'transparent', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}>
                  Scan QR
                </button>
                <button style={{ flex: 1, padding: '12px', borderRadius: '12px', background: 'var(--primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
                  Enter PIN
                </button>
              </div>
            </div>

            {/* Middle Column: Real-Time Transfer */}
            <div className="dashboard-panel transfer-card">
              <div className="panel-header">
                <span className="panel-title">Real-Time Transfer</span>
              </div>

              <div className="transfer-visual">
                {transferring ? (
                  <>
                    <div className="progress-circle-container">
                      <svg className="progress-circle-svg" viewBox="0 0 100 100">
                        <circle className="progress-circle-bg" cx="50" cy="50" r="45" />
                        <circle
                          className="progress-circle-fill"
                          cx="50" cy="50" r="45"
                          style={{ strokeDasharray: 283, strokeDashoffset: 283 - (283 * progress) / 100 }}
                        />
                      </svg>
                      <div className="progress-label">
                        <div className="progress-percent">{progress}%</div>
                        <div className="progress-speed">{progress > 0 ? '87 MB/s' : '0 MB/s'}</div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '18px' }}>Vid_2024_clip.mp4</div>
                      <div style={{ fontSize: '13px', color: 'var(--text-dim)' }}>2.18 GB</div>
                    </div>
                  </>
                ) : (
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '64px', marginBottom: '20px', opacity: 0.5 }}>⚡</div>
                    <h3 style={{ marginBottom: '16px', fontSize: '20px' }}>Multipath Engine Idle</h3>
                    <p style={{ color: 'var(--text-dim)', marginBottom: '24px', fontSize: '14px' }}>Drop files here or click to select</p>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      style={{ padding: '14px 40px', borderRadius: '30px', background: 'var(--primary)', color: 'white', border: 'none', fontWeight: '800', cursor: 'pointer', boxShadow: 'var(--glow)' }}
                    >
                      Select Files
                    </button>
                    <input ref={fileInputRef} type="file" multiple onChange={handleFileSelect} style={{ display: 'none' }} />
                  </div>
                )}

                <div className="speed-meters">
                  <div className="meter-card">
                    <div className="meter-title">Combined Speed</div>
                    <div className="meter-value">{transferring ? '87.2 MB/s' : '0.0 MB/s'}</div>
                  </div>
                  <div className="meter-card">
                    <div className="meter-title">USB Link</div>
                    <div className="meter-value">{transferring ? '40.5 MB/s' : '0.0 MB/s'}</div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', gap: '32px', padding: '16px', borderTop: '1px solid var(--border)' }}>
                <button style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '24px', opacity: transferring ? 1 : 0.3 }}>⏸️</button>
                <button style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '24px', opacity: transferring ? 1 : 0.3 }}>⏹️</button>
                <button style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '24px' }}>🔄</button>
              </div>
            </div>

            {/* Right Column: Queue & Diagnostics */}
            <div className="dashboard-panel">
              <div className="panel-header">
                <span className="panel-title">Transfer Queue</span>
                <span style={{ cursor: 'pointer' }}>▼</span>
              </div>

              <div className="queue-tabs">
                <div className="queue-tab active">Ongoing</div>
                <div className="queue-tab">Queued</div>
                <div className="queue-tab">Completed</div>
              </div>

              <div style={{ flex: 1, overflowY: 'auto' }}>
                {transferring ? (
                  <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', marginBottom: '12px', border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <div style={{ fontSize: '13px', fontWeight: 'bold' }}>Sending to Samsung S24</div>
                      <div style={{ fontSize: '13px', color: 'var(--accent)' }}>{progress}%</div>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginBottom: '8px' }}>
                      <div style={{ width: `${progress}%`, height: '100%', background: 'var(--primary)', borderRadius: '3px', boxShadow: '0 0 10px var(--primary)' }}></div>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Vid_2024_clip.mp4</span>
                      <span>87 MB/s</span>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)', fontSize: '14px' }}>
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>📂</div>
                    No active transfers
                  </div>
                )}
              </div>

              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '20px', marginTop: '12px' }}>
                <div className="panel-header">
                  <span className="panel-title" style={{ fontSize: '13px' }}>Diagnostics</span>
                  <span style={{ fontSize: '16px' }}>⚙️</span>
                </div>
                <div className="diag-row">
                  <div className="diag-label"><span>🔌</span> USB Link</div>
                  <div className="diag-value">Connected</div>
                </div>
                <div className="diag-row">
                  <div className="diag-label"><span>🌐</span> Wi-Fi Latency</div>
                  <div className="diag-value">4.5 ms</div>
                </div>
                <div className="diag-row">
                  <div className="diag-label"><span>🧠</span> Scheduler</div>
                  <div className="diag-value" style={{ color: 'var(--accent)' }}>Idle</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
