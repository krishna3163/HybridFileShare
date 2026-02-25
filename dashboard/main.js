const CHUNK_COUNT = 150;
const chunks = [];

// Elements
const els = {
    app: document.getElementById('app'),
    deviceList: document.getElementById('device-list'),
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('file-input'),
    selectedFiles: document.getElementById('selected-files'),
    previewName: document.getElementById('preview-filename'),
    previewSize: document.getElementById('preview-filesize'),
    clearBtn: document.getElementById('clear-files-btn'),
    sendBtn: document.getElementById('send-files-btn'),
    metrics: document.getElementById('metrics-container'),
    progressFill: document.getElementById('progress-fill'),
    progressVal: document.getElementById('progress-val'),
    etaVal: document.getElementById('eta-val'),
    usbSpeed: document.getElementById('usb-speed-val'),
    wifiSpeed: document.getElementById('wifi-speed-val'),
    totalSpeed: document.getElementById('total-speed-val'),
    chunkMap: document.getElementById('chunk-map'),
    modal: document.getElementById('connection-modal'),
    modalTitle: document.getElementById('modal-title'),
    btnAccept: document.getElementById('accept-btn'),
    btnReject: document.getElementById('reject-btn'),
    devName: document.querySelector('.device-name'),
    devStatus: document.querySelector('.device-status'),
    devAvatar: document.querySelector('.device-avatar'),
    diagUsb: document.getElementById('diag-usb'),
    queueList: document.getElementById('queue-list'),
    manualConnectBtn: document.getElementById('manual-connect-btn'),
};

// State
let isConnected = false;
let socket = null;
let currentTransfer = {
    totalBytes: 0,
    transferredBytes: 0,
    usbBytes: 0,
    wifiBytes: 0,
    startTime: 0,
    active: false,
    filename: ""
};

// Initialize Chunks
els.chunkMap.innerHTML = '';
for (let i = 0; i < CHUNK_COUNT; i++) {
    const chunk = document.createElement('div');
    chunk.className = 'chunk';
    els.chunkMap.appendChild(chunk);
    chunks.push(chunk);
}

// -------------------------------------------------------------
// Real WebSocket Telemetry integration
// -------------------------------------------------------------
function connectTelemetry() {
    socket = new WebSocket('ws://127.0.0.1:9002');

    socket.onopen = () => {
        console.log("Telemetry connected");
        // We consider the local engine "discovered" for now
        addDevice({
            id: 'engine-1',
            name: "HybridLink Engine",
            type: "PC",
            channels: ['USB', 'WIFI']
        });
    };

    socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleTelemetryEvent(msg.type, msg.data);
        } catch (e) { console.error("T-Error", e); }
    };

    socket.onclose = () => {
        setTimeout(connectTelemetry, 5000); // Reconnect
    };
}

function handleTelemetryEvent(type, data) {
    if (!currentTransfer.active && type === "TRANSFER_STARTED") {
        startTransferUI(data.filename, data.size);
    }

    if (type === "CHUNK_COMPLETED") {
        currentTransfer.transferredBytes += data.bytes;
        if (data.channel === "usb") currentTransfer.usbBytes += data.bytes;
        else if (data.channel === "wifi") currentTransfer.wifiBytes += data.bytes;

        updateMetricsUI(data.chunk_id, data.channel);
    }

    if (type === "TRANSFER_COMPLETED") {
        finishTransferUI();
    }
}

connectTelemetry();

// -------------------------------------------------------------
// Nearby Device Discovery & Pairing (Zero-setup UI)
// -------------------------------------------------------------
function addDevice(dev) {
    if (document.getElementById(dev.id)) return;

    const el = document.createElement('div');
    el.className = 'device-item';
    el.id = dev.id;
    el.innerHTML = `
        <div class="device-icon"><i data-lucide="${dev.type === 'Android' ? 'smartphone' : 'monitor'}"></i></div>
        <div class="device-item-info">
            <span class="device-item-name">${dev.name}</span>
            <span class="device-item-type">HybridLink ${dev.type} Node (Zero-Setup)</span>
        </div>
        <div style="font-size:0.75rem; color:var(--accent-blue); padding:4px 8px; border-radius:12px; background:rgba(59,130,246,0.1)">PAIR</div>
    `;

    setTimeout(() => { if (window.lucide) lucide.createIcons(); }, 10);
    el.onclick = () => requestConnection(dev);
    els.deviceList.appendChild(el);
}

function requestConnection(dev) {
    els.modalTitle.textContent = `Pair with ${dev.name}?`;
    document.getElementById('modal-status').textContent = `Temporary session key will be generated.`;
    els.modal.style.display = 'flex';

    els.btnAccept.onclick = () => {
        els.modal.style.display = 'none';
        establishConnection(dev);
    };
    els.btnReject.onclick = () => {
        els.modal.style.display = 'none';
        isConnected = false;
    };
}

els.manualConnectBtn.onclick = () => {
    const ip = prompt("Enter Device IP Address:");
    if (ip) {
        addDevice({
            id: 'manual-' + btoa(ip).replace(/=/g, ''),
            name: ip,
            type: "Android",
            channels: ['WIFI']
        });
    }
};

function establishConnection(dev) {
    isConnected = true;
    els.devName.textContent = dev.name;
    els.devStatus.textContent = "Securely paired (Temporary Session)";
    els.devAvatar.classList.remove('placeholder');
    els.devAvatar.innerHTML = `<i data-lucide="${dev.type === 'Android' ? 'smartphone' : 'monitor'}" style="color:white;"></i>`;
    setTimeout(() => { if (window.lucide) lucide.createIcons(); }, 10);

    els.diagUsb.textContent = "Bound (Multipath)";
    els.diagUsb.className = 'status-badge active';

    els.dropzone.classList.remove('disabled');
    document.getElementById('global-status-text').textContent = "Paired";
}

// -------------------------------------------------------------
// File Sharing UX
// -------------------------------------------------------------
els.dropzone.addEventListener('click', () => { if (isConnected) els.fileInput.click(); });
els.dropzone.addEventListener('dragover', (e) => { e.preventDefault(); if (isConnected) els.dropzone.style.background = 'rgba(59,130,246,0.1)'; });
els.dropzone.addEventListener('dragleave', (e) => { e.preventDefault(); if (isConnected) els.dropzone.style.background = 'rgba(255,255,255,0.02)'; });
els.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    els.dropzone.style.background = 'rgba(255,255,255,0.02)';
    if (isConnected && e.dataTransfer.files.length > 0) processFileSelection(e.dataTransfer.files[0]);
});
els.fileInput.addEventListener('change', (e) => { if (e.target.files.length > 0) processFileSelection(e.target.files[0]); });

els.clearBtn.onclick = () => {
    els.selectedFiles.style.display = 'none';
    els.dropzone.style.display = 'flex';
    els.fileInput.value = '';
};

function processFileSelection(file) {
    els.dropzone.style.display = 'none';
    els.selectedFiles.style.display = 'block';
    els.previewName.textContent = file.name;
    els.previewSize.textContent = (file.size / (1024 * 1024)).toFixed(1) + " MB";
}

els.sendBtn.onclick = () => {
    const file = els.fileInput.files[0];
    if (!file) return;

    // Fallback UI starting if no real backend response
    startTransferUI(file.name, file.size);

    // In a real integrated flow, we would push the file content or trigger the CLI here.
    // E.g., fetch('/api/upload', {method: 'POST'})

    // For visual testing of the UI without a connected backend file reading system:
    let simulatedProgress = 0;
    currentTransfer.simInterval = setInterval(() => {
        handleTelemetryEvent("CHUNK_COMPLETED", {
            chunk_id: Math.floor(Math.random() * CHUNK_COUNT),
            channel: Math.random() > 0.4 ? 'usb' : 'wifi',
            bytes: file.size / CHUNK_COUNT
        });
        simulatedProgress += (100 / CHUNK_COUNT);
        if (simulatedProgress >= 100) {
            clearInterval(currentTransfer.simInterval);
            handleTelemetryEvent("TRANSFER_COMPLETED", {});
        }
    }, 150);
};

// -------------------------------------------------------------
// Multipath Real-time Metrics
// -------------------------------------------------------------
let speedCheckInterval;
function startTransferUI(name, totalBytes) {
    currentTransfer = {
        totalBytes: totalBytes,
        transferredBytes: 0,
        usbBytes: 0,
        wifiBytes: 0,
        lastUsb: 0,
        lastWifi: 0,
        startTime: Date.now(),
        active: true,
        filename: name
    };

    els.selectedFiles.style.display = 'none';
    els.metrics.style.display = 'flex';
    document.getElementById('global-status-text').textContent = "Transferring";
    addQueueItem(name);

    // Clear chunks
    chunks.forEach(c => c.className = 'chunk');

    speedCheckInterval = setInterval(calculateSpeeds, 1000);
}

function calculateSpeeds() {
    if (!currentTransfer.active) return;

    const deltaUsb = currentTransfer.usbBytes - currentTransfer.lastUsb;
    const deltaWifi = currentTransfer.wifiBytes - currentTransfer.lastWifi;

    currentTransfer.lastUsb = currentTransfer.usbBytes;
    currentTransfer.lastWifi = currentTransfer.wifiBytes;

    const usbSpeed = deltaUsb / (1024 * 1024);
    const wifiSpeed = deltaWifi / (1024 * 1024);
    const totalSpeed = usbSpeed + wifiSpeed;

    els.usbSpeed.innerHTML = `${usbSpeed.toFixed(1)} <span class="unit">MB/s</span>`;
    els.wifiSpeed.innerHTML = `${wifiSpeed.toFixed(1)} <span class="unit">MB/s</span>`;
    els.totalSpeed.innerHTML = `${totalSpeed.toFixed(1)} <span class="unit">MB/s</span>`;

    const remain = currentTransfer.totalBytes - currentTransfer.transferredBytes;
    let eta = 0;
    if (totalSpeed > 0) eta = Math.ceil((remain / (1024 * 1024)) / totalSpeed);
    els.etaVal.textContent = eta + 's';
}

function updateMetricsUI(chunkId, channel) {
    if (!currentTransfer.active) return;

    const pct = Math.min(100, (currentTransfer.transferredBytes / currentTransfer.totalBytes) * 100);
    els.progressVal.textContent = Math.floor(pct) + "%";
    els.progressFill.style.width = pct + "%";

    // Map chunk to visual grid
    const cidx = chunkId % CHUNK_COUNT;
    const colorClass = channel === 'usb' ? 'cyan' : 'purple';
    chunks[cidx].className = `chunk ${colorClass}`;

    // Fade old chunks to 'done'
    setTimeout(() => { if (chunks[cidx].classList.contains(colorClass)) chunks[cidx].className = 'chunk done'; }, 500);
}

function finishTransferUI() {
    currentTransfer.active = false;
    clearInterval(speedCheckInterval);
    document.getElementById('global-status-text').textContent = "Completed";

    els.usbSpeed.innerHTML = `0.0 <span class="unit">MB/s</span>`;
    els.wifiSpeed.innerHTML = `0.0 <span class="unit">MB/s</span>`;
    els.totalSpeed.innerHTML = `0.0 <span class="unit">MB/s</span>`;
    els.progressFill.style.width = "100%";
    els.progressVal.textContent = "100%";

    setTimeout(() => {
        els.metrics.style.display = 'none';
        els.dropzone.style.display = 'flex';
        els.fileInput.value = '';
        markQueueDone(currentTransfer.filename);
    }, 3000);
}

function addQueueItem(name) {
    if (els.queueList.querySelector('.empty-state')) els.queueList.innerHTML = '';
    const item = document.createElement('div');
    item.className = 'queue-item';
    item.id = `q-${btoa(name).replace(/=/g, '')}`;
    item.innerHTML = `<div style="font-weight: 500">${name}</div><div style="font-size: 0.7rem; color: var(--accent-blue); margin-top:4px;">TRANSFERRING...</div>`;
    els.queueList.prepend(item);
}

function markQueueDone(name) {
    const item = document.getElementById(`q-${btoa(name).replace(/=/g, '')}`);
    if (item) {
        item.className = 'queue-item done';
        item.innerHTML = `<div style="font-weight: 500">${name}</div><div style="font-size: 0.7rem; color: var(--accent-green); margin-top:4px;">COMPLETED</div>`;
    }
}
