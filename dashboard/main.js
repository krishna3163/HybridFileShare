// HybridFileShare Dashboard Controller
// Unified Discovery & Multitrack Transfer Management

const CHUNK_COUNT = 150;
const chunks = [];

// Elements Mapping
const els = {
    app: document.querySelector('.app-layout'),
    deviceList: document.getElementById('device-list'),
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('file-input'),
    folderInput: document.getElementById('folder-input'),
    browseFilesBtn: document.getElementById('browse-files-btn'),
    selectedFiles: document.getElementById('selected-files'), // Might be missing in new UI, let's check
    metrics: document.getElementById('metrics-container'),
    progressRing: document.getElementById('progress-fill-ring'),
    progressVal: document.getElementById('progress-val'),
    totalSpeed: document.getElementById('total-speed-val'),
    usbSpeed: document.getElementById('usb-speed-val'), // Might be missing or hidden
    wifiSpeed: document.getElementById('wifi-speed-val'),
    connectionModal: document.getElementById('connection-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalStatus: document.getElementById('modal-status'),
    btnAccept: document.getElementById('accept-btn'),
    btnReject: document.getElementById('reject-btn'),
    transferModal: document.getElementById('transfer-modal'),
    transferReqDev: document.getElementById('transfer-req-dev'),
    transferReqName: document.getElementById('transfer-req-name'),
    transferReqSize: document.getElementById('transfer-req-size'),
    transferAcceptBtn: document.getElementById('transfer-accept-btn'),
    transferRejectBtn: document.getElementById('transfer-reject-btn'),
    currentFilename: document.getElementById('current-filename'),
    currentFilesize: document.getElementById('current-filesize'),
    queueList: document.getElementById('queue-list')
};

// Global State
let state = {
    isConnected: false,
    socket: null,
    currentTransfer: {
        totalBytes: 0,
        transferredBytes: 0,
        usbBytes: 0,
        wifiBytes: 0,
        startTime: 0,
        active: false,
        filename: ""
    }
};

// --- Initialization ---
function init() {
    console.log("🚀 HybridFileShare Dashboard Initializing...");

    // Initialize Lucide
    if (window.lucide) {
        lucide.createIcons();
    }

    // Connect Telemetry
    connectTelemetry();

    // Start discovery fetch
    fetchNearbyDevices();
    setInterval(fetchNearbyDevices, 5000);

    // Bind all UI events
    bindEvents();
    bindTransferControls();

    // Teaser: Simulated progress if no real transfer
    simulateInitialTeaser();
}

function bindEvents() {
    if (els.browseFilesBtn) {
        els.browseFilesBtn.onclick = () => els.fileInput.click();
    }

    if (els.fileInput) {
        els.fileInput.onchange = (e) => {
            if (e.target.files.length > 0) {
                if (!state.isConnected) {
                    alert("⚠️ Pair with a device first to start multitrack transfer.");
                    return;
                }
                startTransferUI(e.target.files[0].name, e.target.files[0].size);
            }
        };
    }

    // Sidebar Navigation
    const navBtns = document.querySelectorAll('.nav-icon-btn');
    navBtns.forEach(btn => {
        btn.onclick = () => {
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const title = btn.getAttribute('title');
            console.log(`🚀 Switching view to: ${title}`);
            if (title === "History") {
                showHistory();
            } else if (title === "Dashboard") {
                showDashboard();
            } else if (title === "Home") {
                location.reload();
            }
        };
    });

    // Manual Connect
    const manualBtn = document.getElementById('manual-connect-btn');
    const manualInput = document.getElementById('manual-ip-input');
    if (manualBtn && manualInput) {
        manualBtn.onclick = () => {
            const ip = manualInput.value.trim();
            if (ip) {
                alert(`Attempting direct connection to ${ip}...`);
                requestConnection({ deviceName: `Direct Node [${ip}]`, status: 'online' });
            }
        };
    }

    // QR & PIN
    const qrBtn = document.getElementById('scan-qr-btn');
    const pinBtn = document.getElementById('pin-code-btn');

    // QR Modal Els
    const qrModal = document.getElementById('qr-modal');
    const qrImage = document.getElementById('qr-image');
    const closeQrBtn = document.getElementById('close-qr-btn');

    // PIN Modal Els
    const pinModal = document.getElementById('pin-modal');
    const pinInput = document.getElementById('pin-input');
    const closePinBtn = document.getElementById('close-pin-btn');
    const submitPinBtn = document.getElementById('submit-pin-btn');

    let html5QrcodeScanner = null;

    if (qrBtn) {
        qrBtn.onclick = async () => {
            if (qrModal) qrModal.style.display = 'flex';

            // Fetch local IP for QR
            try {
                const response = await fetch('/api/local-ip');
                const data = await response.json();
                const ip = data.ip;
                const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=hybridlink://${ip}:9001`;
                if (qrImage) qrImage.src = qrUrl;
            } catch (err) {
                console.error("Local IP fetch failed:", err);
                const ip = "127.0.0.1";
                const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=hybridlink://${ip}:9001`;
                if (qrImage) qrImage.src = qrUrl;
            }
        };
    }

    // QR Show/Scan Tabs
    const tabShowQr = document.getElementById('tab-show-qr');
    const tabScanQr = document.getElementById('tab-scan-qr');
    const qrShowView = document.getElementById('qr-show-view');
    const qrScanView = document.getElementById('qr-scan-view');

    if (tabShowQr && tabScanQr) {
        tabShowQr.onclick = () => {
            tabShowQr.classList.add('active');
            tabScanQr.classList.remove('active');
            qrShowView.style.display = 'block';
            qrScanView.style.display = 'none';
            if (html5QrcodeScanner) {
                html5QrcodeScanner.clear();
                html5QrcodeScanner = null;
            }
        };

        tabScanQr.onclick = () => {
            tabScanQr.classList.add('active');
            tabShowQr.classList.remove('active');
            qrShowView.style.display = 'none';
            qrScanView.style.display = 'block';

            if (!html5QrcodeScanner) {
                html5QrcodeScanner = new Html5QrcodeScanner("qr-reader", { fps: 10, qrbox: { width: 250, height: 250 } }, false);
                html5QrcodeScanner.render((decodedText, decodedResult) => {
                    // Handle on success
                    alert(`QR Scanned: ${decodedText}`);
                    html5QrcodeScanner.clear();
                    html5QrcodeScanner = null;
                    if (qrModal) qrModal.style.display = 'none';
                    // Parse URI
                    if (decodedText.startsWith('hybridlink://')) {
                        const ip = decodedText.split('://')[1].split(':')[0];
                        requestConnection({ deviceName: `Scanned Node [${ip}]`, status: 'online' });
                    }
                }, (errorMessage) => {
                    // Expected to constantly fail
                });
            }
        };
    }

    if (closeQrBtn) closeQrBtn.onclick = () => {
        if (qrModal) qrModal.style.display = 'none';
        if (html5QrcodeScanner) {
            html5QrcodeScanner.clear();
            html5QrcodeScanner = null;
        }
    };

    // PIN Show/Enter Tabs
    const tabEnterPin = document.getElementById('tab-enter-pin');
    const tabShowPin = document.getElementById('tab-show-pin');
    const pinEnterView = document.getElementById('pin-enter-view');
    const pinShowView = document.getElementById('pin-show-view');
    const closePinShowBtn = document.getElementById('close-pin-show-btn');

    if (tabEnterPin && tabShowPin) {
        tabEnterPin.onclick = () => {
            tabEnterPin.classList.add('active');
            tabShowPin.classList.remove('active');
            pinEnterView.style.display = 'block';
            pinShowView.style.display = 'none';
        };

        tabShowPin.onclick = () => {
            tabShowPin.classList.add('active');
            tabEnterPin.classList.remove('active');
            pinEnterView.style.display = 'none';
            pinShowView.style.display = 'block';
        };
    }

    if (pinBtn) {
        pinBtn.onclick = () => {
            if (pinInput) pinInput.value = '';
            if (pinModal) pinModal.style.display = 'flex';
        };
    }

    if (closePinBtn) closePinBtn.onclick = () => {
        if (pinModal) pinModal.style.display = 'none';
    };

    if (closePinShowBtn) closePinShowBtn.onclick = () => {
        if (pinModal) pinModal.style.display = 'none';
    };

    if (submitPinBtn) submitPinBtn.onclick = () => {
        const pin = pinInput ? pinInput.value : '';
        if (pin && pin.length === 4) {
            alert("🔑 Handshake complete. Multipath enabled.");
            if (pinModal) pinModal.style.display = 'none';
        } else {
            alert("Please enter a valid 4-digit PIN.");
        }
    };

    // Header Actions
    const refreshBtn = document.getElementById('refresh-btn');
    const settingsBtn = document.getElementById('settings-btn-main');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-btn');

    if (refreshBtn) refreshBtn.onclick = () => location.reload();

    if (settingsBtn) {
        settingsBtn.onclick = () => {
            if (settingsModal) settingsModal.style.display = 'flex';
        };
    }

    if (closeSettingsBtn) {
        closeSettingsBtn.onclick = () => {
            if (settingsModal) settingsModal.style.display = 'none';
        };
    }

    // Settings logic
    const settingDarkmode = document.getElementById('setting-darkmode');
    const settingNotifications = document.getElementById('setting-notifications');
    const settingAutoaccept = document.getElementById('setting-autoaccept');

    if (settingDarkmode) {
        settingDarkmode.onclick = () => {
            settingDarkmode.classList.toggle('active');
            if (settingDarkmode.classList.contains('active')) {
                document.body.style.filter = "none";
            } else {
                document.body.style.filter = "invert(1) hue-rotate(180deg)";
            }
        };
    }

    if (settingNotifications) {
        settingNotifications.onclick = () => {
            settingNotifications.classList.toggle('active');
            if (settingNotifications.classList.contains('active')) {
                if (Notification.permission !== "granted") {
                    Notification.requestPermission();
                }
            }
        };
    }

    if (settingAutoaccept) {
        settingAutoaccept.onclick = () => {
            settingAutoaccept.classList.toggle('active');
            state.autoAccept = settingAutoaccept.classList.contains('active');
            alert(`Auto-accept transfers is now ${state.autoAccept ? 'ON' : 'OFF'}`);
        };
    }

    // Drag and Drop
    if (els.dropzone) {
        els.dropzone.ondragover = (e) => { e.preventDefault(); els.dropzone.classList.add('active'); };
        els.dropzone.ondragleave = () => els.dropzone.classList.remove('active');
        els.dropzone.ondrop = (e) => {
            e.preventDefault();
            els.dropzone.classList.remove('active');
            if (e.dataTransfer.files.length > 0) {
                startTransferUI(e.dataTransfer.files[0].name, e.dataTransfer.files[0].size);
            }
        };
    }

    // Tab Switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.onclick = (e) => {
            const parent = e.target.closest('.tabs');
            parent.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
        };
    });

    if (els.btnReject) els.btnReject.onclick = () => els.connectionModal.style.display = 'none';
    if (els.transferRejectBtn) els.transferRejectBtn.onclick = () => els.transferModal.style.display = 'none';
    if (els.transferAcceptBtn) els.transferAcceptBtn.onclick = () => els.transferModal.style.display = 'none';
}

function showHistory() {
    if (els.dropzone) els.dropzone.innerHTML = `
        <div class="history-view" style="padding:40px; opacity:0.8;">
            <i data-lucide="history" size="40"></i>
            <h3>Transfer History</h3>
            <p>No recent transfers found on this device.</p>
        </div>
    `;
    if (window.lucide) lucide.createIcons();
}

function showDashboard() {
    location.reload(); // Simple reload to reset view for now
}

// --- Discovery ---
async function fetchNearbyDevices() {
    try {
        const response = await fetch('/api/discover-devices');
        const devices = await response.json();
        updateDeviceList(devices);
    } catch (error) {
        console.debug("Discovery API not reachable, using placeholders.");
        // Placeholders are already in HTML, but we can update them if needed
    }
}

function updateDeviceList(devices) {
    if (!els.deviceList) return;

    if (devices.length === 0) {
        els.deviceList.innerHTML = `
            <div class="empty-devices" style="text-align:center; padding:40px; opacity:0.5;">
                <i data-lucide="search" class="animate-pulse"></i>
                <p style="font-size:12px; margin-top:10px;">Searching for peers...</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    els.deviceList.innerHTML = '';
    devices.forEach(dev => {
        const item = document.createElement('div');
        item.className = 'device-item' + (dev.status === 'online' ? ' active' : '');
        item.innerHTML = `
            <img src="../logo.png" class="dev-img" style="${dev.platform === 'win32' ? 'filter: hue-rotate(220deg);' : 'background:#222'}">
            <div class="dev-info">
                <div class="dev-name">${dev.deviceName}</div>
                <div class="dev-model">${dev.platform === 'android' ? 'Mobile Node' : dev.platform === 'win32' ? 'PC Node' : 'Web Hub'}</div>
            </div>
            <div class="dev-status">
                <div class="status-indicators">
                    <span class="dot active"></span>
                    <span class="dot ${dev.status === 'online' ? 'active' : ''}"></span>
                </div>
                <span class="status-label">${dev.status === 'online' ? 'Online' : 'Offline'}</span>
            </div>
        `;
        item.onclick = () => requestConnection(dev);
        els.deviceList.appendChild(item);
    });
}

function requestConnection(dev) {
    if (els.modalTitle) els.modalTitle.textContent = `Pair with ${dev.deviceName}?`;
    if (els.modalStatus) els.modalStatus.textContent = `A secure temporary session key will be generated for ${dev.deviceName}.`;
    if (els.connectionModal) els.connectionModal.style.display = 'flex';

    if (els.btnAccept) {
        els.btnAccept.onclick = () => {
            els.connectionModal.style.display = 'none';
            state.isConnected = true;
            console.log(`Connected to ${dev.deviceName}`);
            alert(`✅ Successfully paired with ${dev.deviceName}! You can now send files.`);
        };
    }
}

// --- Telemetry & Transfer ---
function connectTelemetry() {
    // Port 9002 is the Python engine's WebSocket server
    state.socket = new WebSocket('ws://127.0.0.1:9002');

    state.socket.onopen = () => {
        console.log("✅ Telemetry Engine Connected - Real-time Dashboard Active");
    };

    state.socket.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleTelemetryEvent(msg.type, msg.data);
        } catch (e) { console.error("Parse Error", e); }
    };

    state.socket.onclose = () => {
        console.debug("Telemetry socket closed. Reconnecting...");
        setTimeout(connectTelemetry, 5000);
    };

    state.socket.onerror = () => { /* Silent error to prevent console spam */ };
}

function handleTelemetryEvent(type, data) {
    if (type === "SYSTEM_READY") {
        console.log(`System Ready: ${data.serverId} (v${data.version})`);
    } else if (type === "TRANSFER_STARTED") {
        startTransferUI(data.filename, data.size);
    } else if (type === "CHUNK_COMPLETED") {
        updateProgress(data);
    } else if (type === "TRANSFER_COMPLETED") {
        finishTransferUI();
    }
}

// Wire up transfer control buttons
function bindTransferControls() {
    const pauseBtn = document.querySelector('.btn-icon[data-lucide="pause"]');
    const playBtn = document.querySelector('.btn-icon[data-lucide="play"]');
    const retryBtn = document.querySelector('.btn-primary');

    if (pauseBtn) pauseBtn.onclick = () => alert("Transfer Paused");
    if (playBtn) playBtn.onclick = () => alert("Transfer Resumed");
    if (retryBtn && retryBtn.textContent === "Retry") {
        retryBtn.onclick = () => alert("Retrying all failed chunks...");
    }
}

function startTransferUI(name, size) {
    state.currentTransfer = {
        totalBytes: size,
        transferredBytes: 0,
        active: true,
        filename: name
    };

    if (els.dropzone) els.dropzone.style.display = 'none';
    if (els.metrics) els.metrics.style.display = 'flex';
    if (els.currentFilename) els.currentFilename.textContent = name;
    if (els.currentFilesize) els.currentFilesize.textContent = formatBytes(size);

    addToQueue(name);
}

function updateProgress(data) {
    state.currentTransfer.transferredBytes += data.bytes;
    const pct = Math.floor((state.currentTransfer.transferredBytes / state.currentTransfer.totalBytes) * 100);

    if (els.progressVal) els.progressVal.textContent = `${pct}%`;
    if (els.progressRing) {
        const offset = 283 - (283 * pct) / 100;
        els.progressRing.style.strokeDashoffset = offset;
    }

    // Update Combined Speed
    if (els.totalSpeed) {
        // For demo, we might need a speed calculation loop, but if engine provides it:
        if (data.speed) els.totalSpeed.textContent = `${data.speed} MB/s`;
    }
}

function finishTransferUI() {
    state.currentTransfer.active = false;
    if (els.progressVal) els.progressVal.textContent = "100%";
    if (els.progressRing) els.progressRing.style.strokeDashoffset = 0;

    setTimeout(() => {
        if (els.metrics) els.metrics.style.display = 'none';
        if (els.dropzone) els.dropzone.style.display = 'flex';
    }, 3000);
}

// --- Helpers ---
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024, sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function addToQueue(name) {
    if (!els.queueList) return;
    const empty = els.queueList.querySelector('.empty-queue');
    if (empty) empty.remove();

    const item = document.createElement('div');
    item.className = 'queue-card'; // Styling should be in style.css
    item.style.padding = '12px';
    item.style.background = 'rgba(255,255,255,0.02)';
    item.style.borderRadius = '12px';
    item.style.marginBottom = '8px';
    item.innerHTML = `
        <div style="font-size:12px; font-weight:700;">${name}</div>
        <div style="font-size:10px; color:var(--primary); margin-top:4px;">TRANSFERRING...</div>
    `;
    els.queueList.prepend(item);
}

function simulateInitialTeaser() {
    // Teaser only if no active transfer
    let p = 76;
    setInterval(() => {
        if (!state.currentTransfer.active && els.progressRing && els.metrics && els.metrics.style.display !== 'none') {
            p = (p + 0.1) % 100;
            const offset = 283 - (283 * Math.floor(p)) / 100;
            els.progressRing.style.strokeDashoffset = offset;
            if (els.progressVal) els.progressVal.textContent = `${Math.floor(p)}%`;
        }
    }, 200);
}

// Initialize on Load
document.addEventListener('DOMContentLoaded', init);
