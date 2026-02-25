// Tauri API imports
// const { invoke } = window.__TAURI__.core;

// UI Elements
const elements = {
  percentText: document.getElementById('percent-text'),
  progressRing: document.getElementById('progress-ring'),
  usbSpeed: document.getElementById('usb-speed'),
  wifiSpeed: document.getElementById('wifi-speed'),
  chunkGrid: document.getElementById('chunk-grid'),
  console: document.getElementById('console')
};

// Initialize Lucide icons
lucide.createIcons();

// Generate Chunk Grid
function initChunkGrid() {
  elements.chunkGrid.innerHTML = '';
  for (let i = 0; i < 200; i++) {
    const chunk = document.createElement('div');
    chunk.className = 'chunk';
    if (i < 150) chunk.classList.add('completed');
    if (i >= 150 && i < 160) chunk.classList.add('active');
    elements.chunkGrid.appendChild(chunk);
  }
}

// Update UI Function
function updateMetrics(data) {
  elements.usbSpeed.textContent = `${data.usbSpeed.toFixed(1)} Mbps`;
  elements.wifiSpeed.textContent = `${data.wifiSpeed.toFixed(1)} Mbps`;

  const percent = data.progress;
  elements.percentText.textContent = `${percent}%`;

  // Update progress ring (dasharray is 565)
  const offset = 565 - (565 * percent) / 100;
  elements.progressRing.style.strokeDashoffset = offset;
}

// Log Function
function log(message) {
  const time = new Date().toLocaleTimeString([], { hour12: false });
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `<span class="log-time">${time}</span> <span>${message}</span>`;
  elements.console.insertBefore(entry, elements.console.firstChild);
}

let currentTransfer = { active: false, totalBytes: 0, transferredBytes: 0, usbBytes: 0, wifiBytes: 0, lastUsb: 0, lastWifi: 0, speedInterval: null };

function connectTelemetry() {
  const socket = new WebSocket('ws://127.0.0.1:9002');

  socket.onopen = () => {
    log('Telemetry Engine Connected. Binding live metrics...');
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "TRANSFER_STARTED") {
        currentTransfer.active = true;
        currentTransfer.totalBytes = msg.data.size;
        currentTransfer.transferredBytes = 0;
        currentTransfer.usbBytes = 0;
        currentTransfer.wifiBytes = 0;
        log(`[CORE] Transfer initiated: ${msg.data.filename}`);
        if (currentTransfer.speedInterval) clearInterval(currentTransfer.speedInterval);
        currentTransfer.speedInterval = setInterval(calculateSpeeds, 1000);
      }
      if (msg.type === "CHUNK_COMPLETED") {
        currentTransfer.transferredBytes += msg.data.bytes;
        if (msg.data.channel === "usb") currentTransfer.usbBytes += msg.data.bytes;
        else if (msg.data.channel === "wifi") currentTransfer.wifiBytes += msg.data.bytes;

        const percent = Math.min(100, Math.floor((currentTransfer.transferredBytes / currentTransfer.totalBytes) * 100));
        elements.percentText.textContent = `${percent}%`;

        const offset = 565 - (565 * percent) / 100;
        elements.progressRing.style.strokeDashoffset = offset;

        // Visually complete a chunk on grid
        const chunks = document.querySelectorAll('.chunk');
        const cidx = msg.data.chunk_id % 200;
        if (chunks[cidx]) {
          chunks[cidx].classList.add('completed');
        }
      }
      if (msg.type === "TRANSFER_COMPLETED") {
        currentTransfer.active = false;
        clearInterval(currentTransfer.speedInterval);
        log(`[CORE] Transfer completed successfully.`);
        updateMetrics({ usbSpeed: 0, wifiSpeed: 0, progress: 100 });
      }
    } catch (e) { }
  };

  socket.onclose = () => {
    setTimeout(connectTelemetry, 5000);
  };
}

function calculateSpeeds() {
  if (!currentTransfer.active) return;
  const deltaUsb = currentTransfer.usbBytes - currentTransfer.lastUsb;
  const deltaWifi = currentTransfer.wifiBytes - currentTransfer.lastWifi;
  currentTransfer.lastUsb = currentTransfer.usbBytes;
  currentTransfer.lastWifi = currentTransfer.wifiBytes;
  const usbspeed = deltaUsb / (1024 * 1024);
  const wifispeed = deltaWifi / (1024 * 1024);
  elements.usbSpeed.textContent = `${usbspeed.toFixed(1)} Mbps`;
  elements.wifiSpeed.textContent = `${wifispeed.toFixed(1)} Mbps`;
}

connectTelemetry();

// Navigation
const navItems = document.querySelectorAll('.nav-item');
navItems.forEach(item => {
  item.addEventListener('click', () => {
    navItems.forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    const view = item.querySelector('span').textContent.toLowerCase();
    switchView(view);
  });
});

function switchView(view) {
  log(`Switching view to: ${view.toUpperCase()}`);

  const overview = document.getElementById('view-overview');
  const analytics = document.getElementById('view-analytics');

  if (view === 'overview') {
    overview.style.display = 'grid';
    analytics.style.display = 'none';
  } else if (view === 'analytics') {
    overview.style.display = 'none';
    analytics.style.display = 'grid';
  }
}

// System State
async function checkSystem() {
  try {
    // Example of calling Rust command
    // const devices = await window.__TAURI__.core.invoke('get_adb_devices');
    // if (devices.length > 0) log(`ADB: Found ${devices.length} device(s)`);
  } catch (e) {
    console.error(e);
  }
}

checkSystem();
setInterval(checkSystem, 10000);

// Initialize
initChunkGrid();
log('Mission Control initialized. Scanning for remote engine telemetry...');
