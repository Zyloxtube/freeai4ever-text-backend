# ============================================================
# COMPLETE API FOR RENDER.COM WITH WEB INTERFACE
# File: main.py
# ============================================================

from flask import Flask, request, jsonify, Response, stream_with_context, render_template_string
from flask_cors import CORS
import requests
import json
import uuid
import time
import os

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, 
     origins='*', 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], 
     allow_headers=['*'],
     supports_credentials=True,
     expose_headers=['*'])

# Store chat sessions
chat_sessions = {}

# Your API key
API_KEY = "ua_j7N_FLn1MXA0WJF_4B8XVKSvs1geQfR0"

# HTML Interface
HTML_INTERFACE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            max-width: 1100px;
            width: 100%;
            background: #1a1a2e;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.7);
            border: 1px solid #2a2a4a;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .header h1 {
            font-size: 26px;
            font-weight: 700;
            background: linear-gradient(135deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header .status {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }

        .status.online {
            background: #00b894;
            color: #fff;
        }

        .status.offline {
            background: #e74c3c;
            color: #fff;
        }

        .status.checking {
            background: #fdcb6e;
            color: #2d3436;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .card {
            background: #16213e;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid #2a2a4a;
            transition: border-color 0.3s;
        }

        .card:hover {
            border-color: #e94560;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: #e94560;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .badge {
            font-size: 11px;
            padding: 2px 10px;
            border-radius: 12px;
            font-weight: 500;
        }

        .badge.success {
            background: #00b894;
            color: #fff;
        }

        .badge.error {
            background: #e74c3c;
            color: #fff;
        }

        .badge.waiting {
            background: #636e72;
            color: #fff;
        }

        .badge.loading {
            background: #fdcb6e;
            color: #2d3436;
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 12px;
            flex-wrap: wrap;
        }

        .input-group label {
            min-width: 80px;
            font-size: 13px;
            color: #b0b0b0;
            display: flex;
            align-items: center;
        }

        .input-group input, .input-group select {
            flex: 1;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid #2a2a4a;
            background: #0f0f1a;
            color: #e0e0e0;
            font-size: 14px;
            transition: border-color 0.3s;
            min-width: 150px;
        }

        .input-group input:focus, .input-group select:focus {
            outline: none;
            border-color: #e94560;
        }

        .btn {
            padding: 10px 22px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #e94560;
            color: #fff;
        }

        .btn-primary:hover {
            background: #c73e54;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3);
        }

        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: #2a2a4a;
            color: #b0b0b0;
        }

        .btn-secondary:hover {
            background: #3a3a5a;
        }

        .btn-danger {
            background: #e74c3c;
            color: #fff;
        }

        .btn-danger:hover {
            background: #c0392b;
        }

        .btn-success {
            background: #00b894;
            color: #fff;
        }

        .btn-success:hover {
            background: #00a381;
        }

        .btn-warning {
            background: #fdcb6e;
            color: #2d3436;
        }

        .btn-warning:hover {
            background: #fdcb6e;
        }

        .btn-sm {
            padding: 6px 14px;
            font-size: 12px;
        }

        .flex-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }

        .response-box {
            background: #0f0f1a;
            border-radius: 10px;
            padding: 14px;
            margin-top: 12px;
            max-height: 180px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #2a2a4a;
            color: #b0b0b0;
        }

        .response-box .success {
            color: #00b894;
        }

        .response-box .error {
            color: #e74c3c;
        }

        .response-box .info {
            color: #74b9ff;
        }

        .quick-models {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 8px;
        }

        .quick-models button {
            padding: 4px 12px;
            background: #0f0f1a;
            border: 1px solid #2a2a4a;
            border-radius: 6px;
            color: #888;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .quick-models button:hover {
            border-color: #e94560;
            color: #e0e0e0;
        }

        .quick-models button.active {
            border-color: #e94560;
            color: #e94560;
        }

        .chat-messages {
            max-height: 350px;
            overflow-y: auto;
            margin-top: 12px;
            background: #0f0f1a;
            border-radius: 10px;
            padding: 12px;
            border: 1px solid #2a2a4a;
        }

        .chat-messages .msg {
            padding: 10px 14px;
            margin: 6px 0;
            border-radius: 10px;
            font-size: 14px;
            max-width: 85%;
            word-wrap: break-word;
        }

        .chat-messages .msg.user {
            background: #e94560;
            color: #fff;
            margin-left: auto;
            text-align: right;
        }

        .chat-messages .msg.ai {
            background: #2a2a4a;
            color: #e0e0e0;
            margin-right: auto;
            text-align: left;
        }

        .chat-messages .msg.error {
            background: #e74c3c;
            color: #fff;
            text-align: center;
            max-width: 100%;
        }

        .chat-messages .msg.info {
            background: #2d3436;
            color: #74b9ff;
            text-align: center;
            max-width: 100%;
        }

        .typing-indicator {
            display: none;
            color: #888;
            font-style: italic;
            padding: 10px;
            font-size: 13px;
        }

        .logs-box {
            max-height: 200px;
            overflow-y: auto;
            background: #0f0f1a;
            border-radius: 10px;
            padding: 12px;
            border: 1px solid #2a2a4a;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }

        .log-entry {
            padding: 3px 0;
            border-bottom: 1px solid #1a1a2e;
        }

        .log-entry .time {
            color: #555;
            margin-right: 10px;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        .mt-10 {
            margin-top: 10px;
        }

        .mb-10 {
            margin-bottom: 10px;
        }

        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }

            .container {
                padding: 15px;
            }

            .header {
                flex-direction: column;
                align-items: flex-start;
            }

            .input-group {
                flex-direction: column;
            }

            .input-group label {
                min-width: auto;
            }

            .input-group input, .input-group select {
                width: 100%;
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Chat Interface</h1>
            <div>
                <span class="status checking" id="apiStatus">Checking API...</span>
            </div>
        </div>

        <div class="grid-2">
            <!-- Settings -->
            <div class="card">
                <div class="card-title">⚙️ Settings</div>
                <div class="input-group">
                    <label>API URL</label>
                    <input type="text" id="apiBase" value="https://freeai4ever-text-backend.onrender.com">
                </div>
                <div class="input-group">
                    <label>Model</label>
                    <input type="text" id="modelName" value="gateway-gpt-5-5">
                </div>
                <div class="quick-models">
                    <span style="color:#555;font-size:11px;">Quick:</span>
                    <button onclick="setModel('gateway-gpt-5')">GPT-5</button>
                    <button onclick="setModel('gateway-gpt-5-5')" class="active">GPT-5.5</button>
                    <button onclick="setModel('gateway-gpt-4')">GPT-4</button>
                    <button onclick="setModel('gateway-claude-3')">Claude 3</button>
                    <button onclick="setModel('gateway-gemini-pro')">Gemini</button>
                    <button onclick="setModel('custom')">Custom</button>
                </div>
            </div>

            <!-- Status -->
            <div class="card">
                <div class="card-title">📊 Status</div>
                <div id="statusDisplay">
                    <div style="color:#888;font-size:13px;">No active chat</div>
                    <div style="color:#555;font-size:12px;margin-top:5px;">Chat ID: <span id="chatIdDisplay">None</span></div>
                    <div style="color:#555;font-size:12px;">Messages: <span id="msgCount">0</span></div>
                </div>
                <div class="flex-row mt-10">
                    <button class="btn btn-primary btn-sm" onclick="testHealth()">🔄 Health Check</button>
                    <button class="btn btn-danger btn-sm" onclick="clearAll()">🗑️ Clear All</button>
                </div>
            </div>
        </div>

        <!-- Step 1: Generate Chat -->
        <div class="card full-width mt-10">
            <div class="card-title">
                📝 Generate Chat
                <span class="badge waiting" id="genchatBadge">Not tested</span>
            </div>
            <div class="flex-row">
                <button class="btn btn-primary" onclick="generateChat()">🚀 Create Chat Session</button>
                <button class="btn btn-secondary" onclick="clearLogs()">Clear Logs</button>
            </div>
            <div id="genchatResult" class="response-box">Click "Create Chat Session" to start</div>
        </div>

        <!-- Step 2: Send Message -->
        <div class="card full-width">
            <div class="card-title">
                💬 Send Message
                <span class="badge waiting" id="chatBadge">Not tested</span>
            </div>
            <div class="input-group">
                <label>Message</label>
                <input type="text" id="testMessage" value="Hello! Who are you?" placeholder="Type your message">
            </div>
            <div class="flex-row">
                <button class="btn btn-primary" onclick="sendTestMessage()">📤 Send Test Message</button>
                <button class="btn btn-danger" onclick="clearChat()">Clear Chat</button>
            </div>
            <div id="chatResult" class="response-box">Send a message to test</div>
        </div>

        <!-- Live Chat -->
        <div class="card full-width">
            <div class="card-title">💬 Live Chat</div>
            <div id="liveChat" class="chat-messages">
                <div class="msg info">Start a chat session to begin</div>
            </div>
            <div id="typingIndicator" class="typing-indicator">AI is typing...</div>
            <div class="input-group" style="margin-top:10px;">
                <input type="text" id="liveMessage" placeholder="Type your message..." style="flex:1;padding:10px 14px;border-radius:10px;border:1px solid #2a2a4a;background:#0f0f1a;color:#e0e0e0;font-size:14px;" onkeypress="if(event.key==='Enter') sendLiveMessage()">
                <button class="btn btn-primary" onclick="sendLiveMessage()">Send</button>
            </div>
        </div>

        <!-- Logs -->
        <div class="card full-width">
            <div class="card-title">📋 Logs</div>
            <div id="logs" class="logs-box">Ready...</div>
        </div>
    </div>

    <script>
        let chatId = null;
        let isProcessing = false;

        function setModel(model) {
            if (model === 'custom') {
                document.getElementById('modelName').value = '';
                document.getElementById('modelName').focus();
                document.querySelectorAll('.quick-models button').forEach(b => b.classList.remove('active'));
                return;
            }
            document.getElementById('modelName').value = model;
            document.querySelectorAll('.quick-models button').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            addLog('info', 'Model set to: ' + model);
        }

        function addLog(type, message) {
            const logs = document.getElementById('logs');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const timestamp = new Date().toLocaleTimeString();
            const emoji = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
            entry.innerHTML = '<span class="time">[' + timestamp + ']</span>' + emoji + ' ' + message;
            logs.appendChild(entry);
            logs.scrollTop = logs.scrollHeight;
        }

        function clearLogs() {
            document.getElementById('logs').innerHTML = 'Ready...';
            addLog('info', 'Logs cleared');
        }

        function updateBadge(id, status, text) {
            const el = document.getElementById(id);
            el.className = 'badge ' + status;
            el.textContent = text;
        }

        function updateStatus(text, type) {
            const el = document.getElementById('apiStatus');
            el.className = 'status ' + type;
            el.textContent = text;
        }

        async function testHealth() {
            const apiBase = document.getElementById('apiBase').value.trim();
            addLog('info', 'Checking health at ' + apiBase + '/health');

            try {
                const response = await fetch(apiBase + '/health');
                const data = await response.json();

                if (response.ok) {
                    updateStatus('Online', 'online');
                    addLog('success', 'API is online: ' + JSON.stringify(data));
                } else {
                    updateStatus('Offline', 'offline');
                    addLog('error', 'API returned: ' + response.status);
                }
            } catch (e) {
                updateStatus('Offline', 'offline');
                addLog('error', 'Cannot reach API: ' + e.message);
            }
        }

        async function generateChat() {
            const apiBase = document.getElementById('apiBase').value.trim();
            const model = document.getElementById('modelName').value.trim();

            if (!model) {
                addLog('error', 'Please enter a model name');
                return;
            }

            updateBadge('genchatBadge', 'loading', 'Creating...');
            document.getElementById('genchatResult').innerHTML = 'Creating chat session...';
            addLog('info', 'Creating chat with model: ' + model);

            try {
                const response = await fetch(apiBase + '/genchat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: model })
                });

                const data = await response.json();

                if (response.ok && data.chatId) {
                    chatId = data.chatId;
                    updateBadge('genchatBadge', 'success', 'Ready');
                    document.getElementById('genchatResult').innerHTML =
                        '✅ Chat created!\n' +
                        'Chat ID: ' + data.chatId + '\n' +
                        'Model: ' + data.model;
                    document.getElementById('chatIdDisplay').textContent = data.chatId;
                    document.getElementById('msgCount').textContent = '0';
                    addLog('success', 'Chat created: ' + chatId);
                    document.getElementById('liveChat').innerHTML = '';
                    addLiveMessage('info', 'Chat session created! Start chatting.');
                } else {
                    updateBadge('genchatBadge', 'error', 'Failed');
                    document.getElementById('genchatResult').innerHTML =
                        '❌ Error\n' +
                        'Status: ' + response.status + '\n' +
                        'Response: ' + JSON.stringify(data, null, 2);
                    addLog('error', 'Chat creation failed: ' + response.status);
                }
            } catch (error) {
                updateBadge('genchatBadge', 'error', 'Error');
                document.getElementById('genchatResult').innerHTML =
                    '❌ Network Error\n' + error.message;
                addLog('error', 'Network error: ' + error.message);
            }
        }

        function addLiveMessage(role, content) {
            const chat = document.getElementById('liveChat');
            const msg = document.createElement('div');
            msg.className = 'msg ' + role;
            msg.textContent = content;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }

        function showTyping() {
            document.getElementById('typingIndicator').style.display = 'block';
        }

        function hideTyping() {
            document.getElementById('typingIndicator').style.display = 'none';
        }

        async function sendTestMessage() {
            if (!chatId) {
                addLog('error', 'Create a chat first!');
                alert('Please create a chat session first!');
                return;
            }

            const apiBase = document.getElementById('apiBase').value.trim();
            const message = document.getElementById('testMessage').value.trim();

            if (!message) {
                addLog('error', 'Enter a message');
                return;
            }

            updateBadge('chatBadge', 'loading', 'Sending...');
            document.getElementById('chatResult').innerHTML = 'Streaming response...\n';
            addLog('info', 'Sending: "' + message + '"');

            try {
                const response = await fetch(apiBase + '/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chatId: chatId, message: message })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    updateBadge('chatBadge', 'error', 'Failed');
                    document.getElementById('chatResult').innerHTML =
                        '❌ Error\nStatus: ' + response.status + '\n' + errorText;
                    addLog('error', 'Send failed: ' + response.status);
                    return;
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let fullResponse = '';
                let resultDiv = document.getElementById('chatResult');

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.trim()) {
                            resultDiv.innerHTML += line + '\n';
                            resultDiv.scrollTop = resultDiv.scrollHeight;

                            if (line.startsWith('data: ')) {
                                try {
                                    const jsonStr = line.substring(6);
                                    const data = JSON.parse(jsonStr);

                                    if (data.delta) {
                                        fullResponse += data.delta;
                                    }

                                    if (data.finish) {
                                        addLog('success', 'Response complete');
                                        document.getElementById('msgCount').textContent =
                                            parseInt(document.getElementById('msgCount').textContent) + 1;
                                    }

                                    if (data.done) {
                                        addLog('info', 'Stream finished');
                                    }
                                } catch (e) {}
                            }
                        }
                    }
                }

                updateBadge('chatBadge', 'success', 'Done');
                resultDiv.innerHTML += '\n✅ Complete - ' + fullResponse.length + ' chars';
                addLog('success', 'Response: ' + fullResponse.length + ' chars');

                addLiveMessage('user', message);
                addLiveMessage('ai', fullResponse || 'No response');

            } catch (error) {
                updateBadge('chatBadge', 'error', 'Error');
                document.getElementById('chatResult').innerHTML =
                    '❌ Network Error\n' + error.message;
                addLog('error', 'Network error: ' + error.message);
            }
        }

        async function sendLiveMessage() {
            if (isProcessing) return;

            const input = document.getElementById('liveMessage');
            const message = input.value.trim();

            if (!message) return;
            input.value = '';

            if (!chatId) {
                addLog('error', 'Create a chat first!');
                alert('Please create a chat session first!');
                return;
            }

            isProcessing = true;
            addLiveMessage('user', message);
            addLog('info', 'Live: "' + message + '"');
            showTyping();

            try {
                const apiBase = document.getElementById('apiBase').value.trim();
                const response = await fetch(apiBase + '/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chatId: chatId, message: message })
                });

                if (!response.ok) {
                    hideTyping();
                    addLiveMessage('error', 'Error: ' + response.status);
                    addLog('error', 'Live chat error: ' + response.status);
                    isProcessing = false;
                    return;
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let fullResponse = '';
                let msgDiv = null;

                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.trim().startsWith('data: ')) {
                            try {
                                const jsonStr = line.trim().substring(6);
                                const data = JSON.parse(jsonStr);

                                if (data.delta) {
                                    fullResponse += data.delta;

                                    if (!msgDiv) {
                                        hideTyping();
                                        msgDiv = document.createElement('div');
                                        msgDiv.className = 'msg ai';
                                        document.getElementById('liveChat').appendChild(msgDiv);
                                    }
                                    msgDiv.textContent = fullResponse;
                                    document.getElementById('liveChat').scrollTop = document.getElementById('liveChat').scrollHeight;
                                }

                                if (data.finish) {
                                    addLog('success', 'Live response complete');
                                }

                                if (data.done) {
                                    break;
                                }
                            } catch (e) {}
                        }
                    }
                }

                hideTyping();
                if (fullResponse) {
                    addLog('info', 'Live response: ' + fullResponse.length + ' chars');
                    document.getElementById('msgCount').textContent =
                        parseInt(document.getElementById('msgCount').textContent) + 1;
                } else {
                    addLiveMessage('error', 'No response');
                }
            } catch (error) {
                hideTyping();
                addLiveMessage('error', 'Error: ' + error.message);
                addLog('error', 'Live chat error: ' + error.message);
            }

            isProcessing = false;
        }

        function clearChat() {
            document.getElementById('liveChat').innerHTML = '';
            document.getElementById('chatResult').innerHTML = 'Send a message to test';
            document.getElementById('msgCount').textContent = '0';
            chatId = null;
            document.getElementById('chatIdDisplay').textContent = 'None';
            updateBadge('genchatBadge', 'waiting', 'Not tested');
            updateBadge('chatBadge', 'waiting', 'Not tested');
            document.getElementById('genchatResult').innerHTML = 'Click "Create Chat Session" to start';
            hideTyping();
            addLog('info', 'Chat cleared');
            addLiveMessage('info', 'Chat cleared. Create a new session.');
        }

        function clearAll() {
            clearChat();
            clearLogs();
            document.getElementById('genchatResult').innerHTML = 'Click "Create Chat Session" to start';
            document.getElementById('chatResult').innerHTML = 'Send a message to test';
            addLog('info', 'Everything cleared');
        }

        // Initialize
        window.addEventListener('load', function() {
            setTimeout(testHealth, 500);
            addLiveMessage('info', 'Welcome! Create a chat session to start.');
        });
    </script>
</body>
</html>
'''

# Add CORS headers to every response
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type, Authorization')
    return response

@app.route('/', methods=['GET', 'OPTIONS'])
def home():
    """Serve the web interface"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    
    return render_template_string(HTML_INTERFACE)

@app.route('/genchat', methods=['POST', 'OPTIONS'])
def generate_chat():
    """Generate a new chat session with a specific model"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    try:
        data = request.get_json()
        
        if not data or 'model' not in data:
            response = jsonify({
                "error": "Model is required",
                "message": "Please provide 'model' in the request body"
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        model = data['model']
        chat_id = str(uuid.uuid4())
        
        chat_sessions[chat_id] = {
            "model": model,
            "created_at": time.time(),
            "messages": []
        }
        
        response = jsonify({
            "chatId": chat_id,
            "model": model,
            "message": f"Chat session created with model: {model}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    except Exception as e:
        response = jsonify({
            "error": "Internal server error",
            "message": str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Send a message to an existing chat session"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
        
    try:
        data = request.get_json()
        
        if not data:
            response = jsonify({"error": "Missing request body"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
            
        if 'chatId' not in data:
            response = jsonify({"error": "chatId is required"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
            
        if 'message' not in data:
            response = jsonify({"error": "message is required"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        chat_id = data['chatId']
        message = data['message']
        
        if chat_id not in chat_sessions:
            response = jsonify({
                "error": "Chat session not found",
                "message": f"Chat ID {chat_id} does not exist"
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        session = chat_sessions[chat_id]
        model = session['model']
        
        session['messages'].append({
            "role": "user",
            "content": message
        })
        
        def generate():
            full_response = ""
            
            try:
                payload = {
                    "message": message,
                    "model": model,
                    "effort": "medium"
                }
                
                response = requests.post(
                    "https://unlimited.surf/api/chat",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    stream=True,
                    timeout=60
                )
                
                yield f"data: {json.dumps({'status': 'connected'})}\n\n"
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        yield f"{line_str}\n\n"
                        
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if 'delta' in data:
                                    full_response += data['delta']
                            except:
                                pass
                
                if full_response:
                    session['messages'].append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
        
        response = Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Expose-Headers': 'Content-Type'
            }
        )
        return response
        
    except Exception as e:
        response = jsonify({
            "error": "Internal server error",
            "message": str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/chat/history', methods=['GET', 'OPTIONS'])
def get_chat_history():
    """Get conversation history for a chat session"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    try:
        chat_id = request.args.get('chatId')
        
        if not chat_id:
            response = jsonify({"error": "chatId is required as query parameter"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if chat_id not in chat_sessions:
            response = jsonify({"error": "Chat session not found"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        session = chat_sessions[chat_id]
        
        response = jsonify({
            "chatId": chat_id,
            "model": session['model'],
            "messages": session['messages'],
            "message_count": len(session['messages'])
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    except Exception as e:
        response = jsonify({
            "error": "Internal server error",
            "message": str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/models', methods=['GET', 'OPTIONS'])
def list_models():
    """List available models"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    models = [
        "gateway-gpt-5",
        "gateway-gpt-5-5",
        "gateway-gpt-4",
        "gateway-claude-3",
        "gateway-gemini-pro",
        "gateway-llama-2",
        "gateway-mistral"
    ]
    
    response = jsonify({
        "models": models,
        "default": "gateway-gpt-5"
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
        
    response = jsonify({
        "status": "healthy",
        "active_sessions": len(chat_sessions),
        "timestamp": time.time()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
