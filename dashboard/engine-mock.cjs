const { WebSocketServer } = require('ws');

const wss = new WebSocketServer({ port: 8080 });

console.log('HybridLink Engine Mock started on ws://localhost:8080');

let transferActive = false;
let progress = 0;
let usbSpeed = 0;
let wifiSpeed = 0;
let chunks = Array(100).fill(0); // 0: empty, 1: downloading, 2: completed
let status = 'idle';

const sendState = (ws) => {
    const data = {
        type: 'metrics',
        payload: {
            progress: Math.floor(progress),
            usbSpeed,
            wifiSpeed,
            chunks,
            status,
            remainingTime: transferActive ? Math.ceil((100 - progress) / ((usbSpeed + wifiSpeed + 0.1) / 10)) : 0,
            health: 'stable',
            activeChannels: transferActive ? ['USB', 'WiFi'] : []
        }
    };
    ws.send(JSON.stringify(data));
};

wss.on('connection', (ws) => {
    console.log('Dashboard connected');

    ws.send(JSON.stringify({
        type: 'pairing',
        payload: {
            pin: '741-963',
            qr_text: 'hybridlink-pairing-token-xyz'
        }
    }));

    const interval = setInterval(() => {
        if (transferActive) {
            usbSpeed = Math.random() * 50 + 20;
            wifiSpeed = Math.random() * 30 + 10;
            progress += (usbSpeed + wifiSpeed) / 500;

            // Randomly update chunks
            for (let i = 0; i < 5; i++) {
                const idx = Math.floor(Math.random() * 100);
                if (chunks[idx] === 0) chunks[idx] = 1;
                else if (chunks[idx] === 1 && Math.random() > 0.7) chunks[idx] = 2;
            }

            if (progress >= 100) {
                progress = 100;
                transferActive = false;
                status = 'completed';
                chunks = chunks.map(() => 2);
                ws.send(JSON.stringify({ type: 'log', payload: { message: 'Transfer completed successfully', level: 'info' } }));
            }
        } else {
            usbSpeed = 0;
            wifiSpeed = 0;
        }
        sendState(ws);
    }, 500);

    ws.on('message', (message) => {
        const action = JSON.parse(message);
        console.log('Received action:', action);

        switch (action.type) {
            case 'START':
                transferActive = true;
                progress = 0;
                status = 'active';
                chunks = Array(100).fill(0);
                ws.send(JSON.stringify({ type: 'log', payload: { message: 'Transfer started...', level: 'info' } }));
                break;
            case 'PAUSE':
                transferActive = false;
                status = 'paused';
                ws.send(JSON.stringify({ type: 'log', payload: { message: 'Transfer paused', level: 'warn' } }));
                break;
            case 'RESUME':
                transferActive = true;
                status = 'active';
                ws.send(JSON.stringify({ type: 'log', payload: { message: 'Transfer resumed', level: 'info' } }));
                break;
            case 'CANCEL':
                transferActive = false;
                progress = 0;
                status = 'idle';
                chunks = Array(100).fill(0);
                ws.send(JSON.stringify({ type: 'log', payload: { message: 'Transfer cancelled', level: 'error' } }));
                break;
        }
    });

    ws.on('close', () => clearInterval(interval));
});
