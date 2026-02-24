let ws;
let reconnectInterval;
const CHUNK_COUNT = 100;

// UI Elements
const elements = {
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    progressValue: document.getElementById('global-progress-value'),
    progressFill: document.getElementById('global-progress-fill'),
    usbSpeed: document.getElementById('usb-speed'),
    wifiSpeed: document.getElementById('wifi-speed'),
    remainingTime: document.getElementById('remaining-time'),
    chunkMap: document.getElementById('chunk-map'),
    console: document.getElementById('console'),
    startBtn: document.getElementById('start-btn'),
    pauseBtn: document.getElementById('pause-btn'),
    resumeBtn: document.getElementById('resume-btn'),
    cancelBtn: document.getElementById('cancel-btn'),
    healthStatus: document.getElementById('health-status'),
    activeChannels: document.getElementById('active-channels'),
    usbGraph: document.getElementById('usb-graph'),
    wifiGraph: document.getElementById('wifi-graph')
};

// Initialize Chunks
const chunks = [];
for (let i = 0; i < CHUNK_COUNT; i++) {
    const chunk = document.createElement('div');
    chunk.className = 'chunk';
    elements.chunkMap.appendChild(chunk);
    chunks.push(chunk);
}

// Speed Graph History
let usbHistory = Array(10).fill(0);
let wifiHistory = Array(10).fill(0);

function updateGraph(element, history, value) {
    history.push(value);
    history.slice(-10);
    const points = history.map((val, i) => `${i * 10} ${20 - (val / 100 * 20)}`).join(' L');
    element.setAttribute('d', `M${points}`);
}

function connect() {
    ws = new WebSocket('ws://localhost:8080');

    ws.onopen = () => {
        elements.statusDot.classList.add('online');
        elements.statusText.textContent = 'ONLINE';
        log('System', 'Connected to HybridLink Engine', 'info');
        clearInterval(reconnectInterval);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'metrics') {
            updateUI(data.payload);
        } else if (data.type === 'log') {
            log('Engine', data.payload.message, data.payload.level);
        }
    };

    ws.onclose = () => {
        elements.statusDot.classList.remove('online');
        elements.statusText.textContent = 'OFFLINE';
        log('System', 'Connection lost. Reconnecting...', 'error');
        reconnectInterval = setInterval(connect, 3000);
    };
}

function updateUI(payload) {
    elements.progressValue.textContent = `${payload.progress}%`;
    elements.progressFill.style.width = `${payload.progress}%`;

    elements.usbSpeed.textContent = payload.usbSpeed.toFixed(1);
    elements.wifiSpeed.textContent = payload.wifiSpeed.toFixed(1);

    updateGraph(elements.usbGraph, usbHistory, payload.usbSpeed);
    updateGraph(elements.wifiGraph, wifiHistory, payload.wifiSpeed);

    if (payload.remainingTime > 0) {
        const mins = Math.floor(payload.remainingTime / 60);
        const secs = payload.remainingTime % 60;
        elements.remainingTime.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    } else {
        elements.remainingTime.textContent = '--:--';
    }

    // Update chunks
    payload.chunks.forEach((state, i) => {
        chunks[i].className = 'chunk' + (state === 1 ? ' active' : state === 2 ? ' done' : '');
    });

    elements.healthStatus.textContent = payload.health.toUpperCase();
    elements.activeChannels.textContent = payload.activeChannels.join(', ') || 'NONE';

    // Button visibility
    if (payload.status === 'paused') {
        elements.pauseBtn.style.display = 'none';
        elements.resumeBtn.style.display = 'block';
    } else {
        elements.pauseBtn.style.display = 'block';
        elements.resumeBtn.style.display = 'none';
    }
}

function log(source, message, level = 'info') {
    const time = new Date().toLocaleTimeString([], { hour12: false });
    const entry = document.createElement('div');
    entry.className = `log-entry`;
    entry.innerHTML = `<span class="log-time">[${time}]</span> <span class="log-${level}">[${source}]</span> ${message}`;
    elements.console.insertBefore(entry, elements.console.firstChild);
}

// Event Listeners
elements.startBtn.onclick = () => ws.send(JSON.stringify({ type: 'START' }));
elements.pauseBtn.onclick = () => ws.send(JSON.stringify({ type: 'PAUSE' }));
elements.resumeBtn.onclick = () => ws.send(JSON.stringify({ type: 'RESUME' }));
elements.cancelBtn.onclick = () => ws.send(JSON.stringify({ type: 'CANCEL' }));

// Start connection
connect();
