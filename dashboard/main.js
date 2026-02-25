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
    wifiGraph: document.getElementById('wifi-graph'),
    usbBadge: document.getElementById('usb-badge'),
    wifiBadge: document.getElementById('wifi-badge'),
    queueCount: document.getElementById('queue-count')
};

// Initialize Chunks
const chunks = [];
elements.chunkMap.innerHTML = ''; // Clear placeholders
for (let i = 0; i < CHUNK_COUNT; i++) {
    const chunk = document.createElement('div');
    chunk.className = 'chunk';
    elements.chunkMap.appendChild(chunk);
    chunks.push(chunk);
}

// Speed Graph History
let usbHistory = Array(20).fill(0);
let wifiHistory = Array(20).fill(0);

function updateGraph(element, history, value) {
    history.push(value);
    if (history.length > 20) history.shift();

    const step = 100 / (history.length - 1);
    const points = history.map((val, i) => {
        const x = i * step;
        const y = 20 - (Math.min(val, 100) / 100 * 20);
        return `${x.toFixed(1)} ${y.toFixed(1)}`;
    }).join(' L');

    element.setAttribute('d', `M${points}`);
}

function connect() {
    ws = new WebSocket('ws://localhost:8080');

    ws.onopen = () => {
        elements.statusDot.classList.add('online');
        elements.statusText.textContent = 'ONLINE';
        log('SYSTEM', 'Secure connection established with HybridLink Engine', 'info');
        clearInterval(reconnectInterval);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics') {
                updateUI(data.payload);
            } else if (data.type === 'log') {
                log('ENGINE', data.payload.message, data.payload.level);
            }
        } catch (e) {
            console.error('Failed to parse WS message', e);
        }
    };

    ws.onclose = () => {
        elements.statusDot.classList.remove('online');
        elements.statusText.textContent = 'OFFLINE';
        log('SYSTEM', 'Link interrupted. Attempting automatic recovery...', 'error');
        reconnectInterval = setInterval(connect, 3000);

        // Reset speeds
        elements.usbSpeed.textContent = '0.0';
        elements.wifiSpeed.textContent = '0.0';
        elements.usbBadge.classList.remove('online');
        elements.wifiBadge.classList.remove('online');
    };
}

function updateUI(payload) {
    // Smooth progress update
    elements.progressValue.textContent = `${payload.progress}%`;
    elements.progressFill.style.width = `${payload.progress}%`;

    // Speed updates
    elements.usbSpeed.textContent = payload.usbSpeed.toFixed(1);
    elements.wifiSpeed.textContent = payload.wifiSpeed.toFixed(1);

    // Badges
    if (payload.usbSpeed > 0) elements.usbBadge.classList.add('online');
    else elements.usbBadge.classList.remove('online');

    if (payload.wifiSpeed > 0) elements.wifiBadge.classList.add('online');
    else elements.wifiBadge.classList.remove('online');

    // Graphs
    updateGraph(elements.usbGraph, usbHistory, payload.usbSpeed);
    updateGraph(elements.wifiGraph, wifiHistory, payload.wifiSpeed);

    // Time
    if (payload.remainingTime > 0) {
        const mins = Math.floor(payload.remainingTime / 60);
        const secs = payload.remainingTime % 60;
        elements.remainingTime.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    } else {
        elements.remainingTime.textContent = '--:--';
    }

    // Update chunks
    payload.chunks.forEach((state, i) => {
        if (chunks[i]) {
            const className = 'chunk' + (state === 1 ? ' active' : state === 2 ? ' done' : '');
            if (chunks[i].className !== className) {
                chunks[i].className = className;
            }
        }
    });

    // Health
    elements.healthStatus.textContent = payload.health.toUpperCase();
    elements.healthStatus.style.color = payload.health === 'stable' ? 'var(--accent-success)' : 'var(--accent-warning)';

    elements.activeChannels.textContent = payload.activeChannels.join(', ') || 'NONE';

    // Button visibility
    if (payload.status === 'paused') {
        elements.pauseBtn.style.display = 'none';
        elements.resumeBtn.style.display = 'flex';
    } else {
        elements.pauseBtn.style.display = 'flex';
        elements.resumeBtn.style.display = 'none';
    }
}

function log(source, message, level = 'info') {
    const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const entry = document.createElement('div');
    entry.className = `log-entry log-${level}`;

    entry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-source">[${source}]</span>
        <span class="log-message">${message}</span>
    `;

    elements.console.insertBefore(entry, elements.console.firstChild);

    // Prune logs if too many
    if (elements.console.children.length > 50) {
        elements.console.removeChild(elements.console.lastChild);
    }
}

// Event Listeners
const sendCommand = (cmd, payload = {}) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: cmd, ...payload }));
    }
};

elements.startBtn.onclick = () => sendCommand('START');
elements.pauseBtn.onclick = () => sendCommand('PAUSE');
elements.resumeBtn.onclick = () => sendCommand('RESUME');
elements.cancelBtn.onclick = () => sendCommand('CANCEL');

// Browser Receiver Logic
const urlParams = new URLSearchParams(window.location.search);
const sessionToken = urlParams.get('s');
const deviceId = urlParams.get('d');

if (sessionToken && deviceId) {
    showReceiverUI();
}

function showReceiverUI() {
    const overlay = document.getElementById('receiver-overlay');
    overlay.style.display = 'flex';

    log('BROWSER', `Joining app-less session: ${sessionToken.substring(0, 8)}...`, 'info');

    // Simulate pairing request
    setTimeout(() => {
        document.getElementById('pin-entry').style.display = 'block';
        log('SECURITY', 'Manual PIN verification required for browser node', 'warn');
    }, 1500);

    // PIN Box Auto-focus/tabbing
    const pinBoxes = document.querySelectorAll('.pin-box');
    pinBoxes.forEach((box, idx) => {
        box.onkeyup = (e) => {
            if (e.target.value.length === 1 && idx < pinBoxes.length - 1) {
                pinBoxes[idx + 1].focus();
            }

            // Check if all filled
            const pin = Array.from(pinBoxes).map(b => b.value).join('');
            if (pin.length === 6) {
                verifyPairing(pin);
            }
        }
    });
}

function verifyPairing(pin) {
    log('SECURITY', 'Verifying session token and PIN...', 'info');

    // Simulate verification
    setTimeout(() => {
        document.getElementById('pairing-panel').style.display = 'none';
        document.getElementById('transfer-panel').style.display = 'block';
        document.getElementById('accept-btn').style.display = 'flex';

        document.getElementById('incoming-filename').textContent = 'Project_Source_v2.zip';
        document.getElementById('incoming-size').textContent = '248.5 MB';

        log('AUTH', 'Pairing successful. Session established over WiFi-Relay', 'success');
    }, 1000);
}

document.getElementById('accept-btn').onclick = () => {
    document.getElementById('accept-btn').style.display = 'none';
    log('TRANSFER', 'Receiving chunks via browser stream...', 'info');
    simulateReception();
};

document.getElementById('close-receiver-btn').onclick = () => {
    window.location.search = '';
};

function simulateReception() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 5;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            log('TRANSFER', 'File received successfully via Browser Mode', 'info');
        }

        document.getElementById('receiver-progress-fill').style.width = `${progress}%`;
        document.getElementById('receiver-percent').textContent = `${Math.floor(progress)}%`;
        document.getElementById('receiver-speed').textContent = `${(Math.random() * 10 + 5).toFixed(1)} MB/s`;
    }, 500);
}

// Start connection
connect();

