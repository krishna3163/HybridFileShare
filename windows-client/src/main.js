// HybridFileShare Main Controller
// Unified Discovery & Multitrack Transfer Management

// UI Elements
const elements = {
  percentText: document.querySelector('.percent-val'),
  progressRing: document.getElementById('main-progress-ring'),
  speedText: document.querySelector('.speed-val'),
  deviceList: document.getElementById('discovered-devices'),
  brandTitle: document.querySelector('.brand-title'),
  sidebarNav: document.querySelectorAll('.nav-item'),
  activeTransferUI: document.getElementById('active-transfer-ui'),
  idleStateUI: document.getElementById('idle-state-ui'),
  fileName: document.querySelector('.file-name'),
  fileSize: document.querySelector('.file-size')
};

// Initialize Lucide icons
if (window.lucide) {
  lucide.createIcons();
}

// Global State
let state = {
  discoveredDevices: [],
  isTransferring: false,
  progress: 76,
  speed: 87,
  currentView: 'dashboard'
};

// --- View Switching ---
elements.sidebarNav.forEach(item => {
  item.addEventListener('click', () => {
    elements.sidebarNav.forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    const view = item.getAttribute('data-view');
    state.currentView = view;
    console.log(`View switched to: ${view}`);
    // In a real app, we would swap out panels here
  });
});

// --- Device Discovery ---
async function fetchNearbyDevices() {
  try {
    // Try to fetch from local API server
    const response = await fetch('http://localhost:3000/api/discover-devices');
    const devices = await response.json();
    state.discoveredDevices = devices;
    updateDeviceList();
  } catch (error) {
    console.debug('API Server not yet reachable, using mock devices...');
    // Mock devices if server is down for demo
    if (state.discoveredDevices.length === 0) {
      state.discoveredDevices = [
        { deviceId: 's24-u', deviceName: "Ashish's Samsung", platform: 'android', status: 'online', host: '192.168.1.5' },
        { deviceId: 'win-pc', deviceName: "Vikram's PC", platform: 'win32', status: 'online', host: '192.168.1.10' }
      ];
      updateDeviceList();
    }
  }
}

function updateDeviceList() {
  if (!elements.deviceList) return;

  elements.deviceList.innerHTML = '';
  state.discoveredDevices.forEach(device => {
    const item = document.createElement('div');
    item.className = `device-item ${device.deviceId === 's24-u' ? 'active' : ''}`;

    const iconSrc = '/assets/logo.png'; // Should use specific icons based on platform

    item.innerHTML = `
            <img src="${iconSrc}" class="device-icon" ${device.platform === 'win32' ? 'style="filter: hue-rotate(220deg);"' : ''}>
            <div class="device-info">
                <h4 class="device-name">${device.deviceName}</h4>
                <p class="device-model">${device.platform === 'android' ? 'Android Device' : 'Windows Client'}</p>
            </div>
            <div class="device-status">
                <div class="stat-dots">
                    <span class="dot active"></span>
                    <span class="dot ${device.status === 'online' ? 'active' : ''}"></span>
                </div>
                <span class="stat-text">${device.status === 'online' ? 'Strong' : 'Offline'}</span>
            </div>
        `;

    item.onclick = () => {
      document.querySelectorAll('.device-item').forEach(d => d.classList.remove('active'));
      item.classList.add('active');
      console.log(`Target device selected: ${device.deviceName}`);
    };

    elements.deviceList.appendChild(item);
  });
}

// --- Transfer Management ---
function updateProgress(percent, mbps) {
  state.progress = percent;
  state.speed = mbps;

  if (elements.percentText) elements.percentText.textContent = `${percent}%`;
  if (elements.speedText) elements.speedText.textContent = `${mbps} MB/s`;

  if (elements.progressRing) {
    // circumference of r=45 is ~283
    const offset = 283 - (283 * percent) / 100;
    elements.progressRing.style.strokeDashoffset = offset;
  }
}

// --- Multichannel Telemetry ---
function connectTelemetry() {
  // Connect to the engine's WebSocket for live progress
  const ws = new WebSocket('ws://localhost:9002');

  ws.onopen = () => {
    console.log('✅ Multitrack Engine Connected');
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === 'TRANSFER_PROGRESS') {
        updateProgress(msg.progress, msg.speed);
        // Update specific channel speeds if available
        if (msg.usbSpeed) {
          const usbSpeedEl = document.getElementById('usb-speed');
          if (usbSpeedEl) usbSpeedEl.textContent = `${msg.usbSpeed} MB/s`;
        }
      }
    } catch (e) {
      console.error('Telemetry parse error', e);
    }
  };

  ws.onclose = () => {
    setTimeout(connectTelemetry, 3000);
  };
}

// --- Initialization ---
function init() {
  console.log('🚀 HybridFileShare Multitrack Interface Initializing...');

  // Start discovery loops
  fetchNearbyDevices();
  setInterval(fetchNearbyDevices, 5000);

  // Connect telemetry
  connectTelemetry();

  // Simulated live progress for teaser
  let p = 76;
  setInterval(() => {
    if (p < 100) {
      p += 0.1;
      updateProgress(Math.floor(p), 87 + Math.floor(Math.random() * 5));
    } else {
      p = 0;
    }
  }, 400);

  // Initial icon refresh
  if (window.lucide) lucide.createIcons();
}

document.addEventListener('DOMContentLoaded', init);
