import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import QRCode from 'qrcode.react';
import JSZip from 'jszip';

const App = () => {
  const [mode, setMode] = useState('home'); // home, share, receive
  const [deviceId, setDeviceId] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [nearbyDevices, setNearbyDevices] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [qrCode, setQrCode] = useState('');
  const [pin, setPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [shareLink, setShareLink] = useState('');
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

  // Generate QR code link
  const generateShareLink = () => {
    const baseUrl = window.location.origin;
    const shareData = {
      deviceId,
      deviceName,
      pin: Math.random().toString().slice(2, 8),
    };
    const link = `${baseUrl}?share=${Buffer.from(JSON.stringify(shareData)).toString('base64')}`;
    setShareLink(link);
    return link;
  };

  // Handle file selection
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFile(files);
  };

  // Send files
  const sendFiles = async (targetDevice) => {
    if (!selectedFile || selectedFile.length === 0) {
      alert('Please select files');
      return;
    }

    setTransferring(true);
    try {
      // Create FormData
      const formData = new FormData();
      selectedFile.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('fromDeviceId', deviceId);
      formData.append('fromDeviceName', deviceName);
      formData.append('toDeviceId', targetDevice.deviceId);

      // Upload to relay server
      const response = await fetch('/api/transfer', {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });

      if (response.ok) {
        alert('✅ Files sent successfully!');
        setSelectedFile(null);
        setProgress(0);
      }
    } catch (error) {
      console.error('Transfer error:', error);
      alert('❌ Transfer failed');
    } finally {
      setTransferring(false);
    }
  };

  // Home Screen
  if (mode === 'home') {
    return (
      <div className="app">
        <header className="header">
          <div className="header-content">
            <h1>📱 HybridLink Share</h1>
            <p>Fast file sharing across devices</p>
            <span className="device-badge">{deviceName}</span>
          </div>
        </header>

        <div className="container">
          {/* Quick Stats */}
          <div className="stats">
            <div className="stat-card">
              <div className="stat-number">{nearbyDevices.length}</div>
              <div className="stat-label">Nearby Devices</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">0</div>
              <div className="stat-label">Pending Transfers</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">100%</div>
              <div className="stat-label">Connection Status</div>
            </div>
          </div>

          {/* Main Actions */}
          <div className="action-grid">
            <button
              className="action-btn share-btn"
              onClick={() => {
                setMode('share');
                generateQrAndPin();
              }}
            >
              <div className="action-icon">📤</div>
              <div className="action-title">Share Files</div>
              <div className="action-desc">Send to nearby devices</div>
            </button>

            <button
              className="action-btn receive-btn"
              onClick={() => {
                setMode('receive');
              }}
            >
              <div className="action-icon">📥</div>
              <div className="action-title">Receive Files</div>
              <div className="action-desc">Get files from others</div>
            </button>

            <button className="action-btn qr-btn" onClick={generateShareLink}>
              <div className="action-icon">🔗</div>
              <div className="action-title">QR Link</div>
              <div className="action-desc">Share via QR code</div>
            </button>

            <button className="action-btn web-btn" onClick={() => window.open('/web', '_blank')}>
              <div className="action-icon">🌐</div>
              <div className="action-title">Web Interface</div>
              <div className="action-desc">More options & history</div>
            </button>
          </div>

          {/* Nearby Devices */}
          <div className="section">
            <h2>🔍 Nearby Devices</h2>
            {nearbyDevices.length > 0 ? (
              <div className="device-list">
                {nearbyDevices.map((device) => (
                  <div key={device.deviceId} className="device-item">
                    <div className="device-info">
                      <div className="device-name">{device.deviceName}</div>
                      <div className="device-distance">
                        {device.distance ? `${device.distance}m away` : 'Connected'}
                      </div>
                    </div>
                    <button className="quick-send" onClick={() => sendFiles(device)}>
                      Send
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No nearby devices found</p>
                <p className="hint">Make sure other devices are close and connected</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Share Screen
  if (mode === 'share') {
    return (
      <div className="app">
        <header className="header-back" onClick={() => setMode('home')}>
          <span>← Back</span>
          <h1>Share Files</h1>
        </header>

        <div className="container">
          {/* QR Code Section */}
          <div className="qr-section">
            <h2>Scan to Receive</h2>
            <div className="qr-container">
              {qrCode && (
                <QRCode
                  value={qrCode}
                  size={250}
                  level="H"
                  includeMargin={true}
                  renderAs="canvas"
                />
              )}
            </div>

            {/* PIN */}
            <div className="pin-section">
              <button className="pin-toggle" onClick={() => setShowPin(!showPin)}>
                {showPin ? '🔒' : '🔓'} PIN Code
              </button>
              {showPin && (
                <div className="pin-display">
                  <div className="pin-code">{pin}</div>
                  <p>Share this PIN for manual entry</p>
                </div>
              )}
            </div>

            {/* Or select from nearby */}
            <div className="divider">OR</div>

            <h3>Select Recipient Device</h3>
            {nearbyDevices.length > 0 ? (
              <>
                <div className="file-input-section">
                  <button
                    className="file-btn"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    + Select Files
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />

                  {selectedFile && selectedFile.length > 0 && (
                    <div className="selected-files">
                      {selectedFile.map((f) => (
                        <div key={f.name} className="file-item">
                          <span>📄 {f.name}</span>
                          <span>{(f.size / 1024 / 1024).toFixed(2)}MB</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="device-grid">
                  {nearbyDevices.map((device) => (
                    <button
                      key={device.deviceId}
                      className="device-select"
                      onClick={() => sendFiles(device)}
                      disabled={!selectedFile || transferring}
                    >
                      <div className="device-emoji">
                        {device.type === 'android' ? '📱' : device.type === 'windows' ? '🖥️' : '🌐'}
                      </div>
                      <div className="device-name">{device.deviceName}</div>
                      <div className="device-status">
                        {transferring ? '⏳ Sending...' : '✓ Ready'}
                      </div>
                    </button>
                  ))}
                </div>

                {transferring && (
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                    <div className="progress-text">{progress}%</div>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">
                <p>No nearby devices found</p>
                <p className="hint">Other devices will appear here when they come in range</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Receive Screen
  if (mode === 'receive') {
    return (
      <div className="app">
        <header className="header-back" onClick={() => setMode('home')}>
          <span>← Back</span>
          <h1>Receive Files</h1>
        </header>

        <div className="container">
          <div className="receive-section">
            <div className="receive-icon">📥</div>
            <h2>Ready to Receive</h2>
            <p>Your device is discoverable by nearby devices</p>

            <div className="info-card">
              <h3>Device Information</h3>
              <div className="info-row">
                <span>Device ID:</span>
                <span className="mono">{deviceId}</span>
              </div>
              <div className="info-row">
                <span>Device Name:</span>
                <span>{deviceName}</span>
              </div>
              <div className="info-row">
                <span>PIN:</span>
                <span className="mono">{pin || 'Generated when sharing'}</span>
              </div>
            </div>

            <div className="hint-card">
              <h4>💡 Tips:</h4>
              <ul>
                <li>Keep this window open to receive files</li>
                <li>Make sure your device is connected to the same WiFi</li>
                <li>Files will appear in your Downloads folder</li>
              </ul>
            </div>

            <button className="back-btn" onClick={() => setMode('home')}>
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }
};

export default App;
