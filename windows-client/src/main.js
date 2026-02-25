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

// Main Loop (Mocked for Demo)
let mockProgress = 75;
setInterval(() => {
  if (mockProgress < 100) {
    mockProgress += Math.random() * 0.5;
    if (mockProgress > 100) mockProgress = 100;

    updateMetrics({
      usbSpeed: 450 + Math.random() * 50,
      wifiSpeed: 300 + Math.random() * 30,
      progress: Math.floor(mockProgress)
    });

    // Randomly update chunks
    const chunks = document.querySelectorAll('.chunk');
    const targetIndex = Math.floor(150 + (mockProgress - 75) * 2);
    if (chunks[targetIndex]) {
      chunks[targetIndex].classList.add('active');
      if (targetIndex > 0) chunks[targetIndex - 1].classList.add('completed');
    }
  }
}, 1000);

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
log('Mission Control initialized. Scanning for ADB devices...');
setTimeout(() => log('Pixel 7 Pro detected via USB. Synchronizing...'), 2000);
