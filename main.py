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

# Enable CORS for all routes with proper settings
CORS(app, 
     origins='*', 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], 
     allow_headers=['*'],
     supports_credentials=True,
     expose_headers=['*'])

# Store chat sessions in memory (will reset on restart)
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
    <title>AI Chat API</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0a0a1a;
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: #1a1a2e;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        
        h1 {
            color: #e94560;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #888;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .test-section {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #e94560;
        }
        
        .test-section h3 {
            color: #e94560;
            margin-bottom: 15px;
            font-size: 16px;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }
        
        .input-group label {
            min-width: 100px;
            color: #aaa;
            font-size: 14px;
            display: flex;
            align-items: center;
        }
        
        .input-group input, .input-group select {
            flex: 1;
            min-width: 200px;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid #333;
            background: #0a0a1a;
            color: white;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus, .input-group select:focus {
            outline: none;
            border-color: #e94560;
        }
        
        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #e94560;
            color: white;
        }
        
        .btn-primary:hover {
            background: #c73e54;
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #333;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #444;
        }
        
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c0392b;
        }
        
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        
        .btn-warning:hover {
            background: #d68910;
        }
        
        .btn-success {
            background: #2ecc71;
            color: white;
        }
        
        .btn-success:hover {
            background: #27ae60;
        }
        
        .response-box {
            background: #0a0a1a;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-wrap: break-word;
            border: 1px solid #333;
        }
        
        .response-box .success {
            color: #2ecc71;
        }
        
        .response-box .error {
            color: #e74c3c;
        }
        
        .response-box .info {
            color: #3498db;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .status-badge.success {
            background: #2ecc71;
            color: #fff;
        }
        
        .status-badge.error {
            background: #e74c3c;
            color: #fff;
        }
        
        .status-badge.loading {
            background: #f39c12;
            color: #fff;
            animation: pulse 1s infinite;
        }
        
        .status-badge.waiting {
            background: #555;
            color: #fff;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .log-entry {
            padding: 4px 0;
            border-bottom: 1px solid #1a1a2e;
        }
        
        .log-entry .timestamp {
            color: #555;
            font-size: 11px;
            margin-right: 10px;
        }
        
        .quick-models {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        
        .quick-models button {
            padding: 4px 12px;
            background: #0a0a1a;
            border: 1px solid #333;
            border-radius: 4px;
            color: #aaa;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .quick-models button:hover {
            border-color: #e94560;
            color: white;
        }
        
        .quick-models button.active {
            border-color: #e94560;
            color: #e94560;
        }
        
        .chat-messages {
            max-height: 400px;
            overflow-y: auto;
            margin-top: 15px;
            background: #0a0a1a;
            border-radius: 8px;
            padding: 10px;
        }
        
        .chat-messages .msg {
            padding: 10px 14px;
            margin: 5px 0;
            border-radius: 8px;
            font-size: 14px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .chat-messages .msg.user {
            background: #e94560;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .chat-messages .msg.ai {
            background: #0f3460;
            color: white;
            margin-right: auto;
            text-align: left;
        }
        
        .chat-messages .msg.error {
            background: #c0392b;
            color: white;
            text-align: center;
            max-width: 100%;
        }
        
        .chat-messages .msg.info {
            background: #2c3e50;
            color: #3498db;
            text-align: center;
            max-width: 100%;
        }
        
        .flex-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .typing-indicator {
            display: none;
            color: #888;
            font-style: italic;
            padding: 10px;
        }
        
        .api-info {
            background: #0a0a1a;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            border: 1px solid #333;
        }
        
        .api-info code {
            color: #e94560;
            background: #1a1a2e;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 13px;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 15px;
            }
            
            .input-group {
                flex-direction: column;
            }
            
            .input-group label {
                min-width: auto;
            }
            
            .input-group input, .input-group select {
                min-width: auto;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Chat API</h1>
        <div class="subtitle">Test your API endpoints - CORS enabled</div>
        
        <div class="api-info">
            <strong>📡 API Endpoints:</strong><br>
            <code>POST /genchat</code> - Generate chat session<br>
            <code>POST /chat</code> - Send message<br>
            <code>GET /health</code> - Health check<br>
            <code>GET /models</code> - List models
        </div>
        
        <div class="test-section">
            <h3>⚙️ Settings</h3>
            <div class="input-group">
                <label>API URL</label>
                <input type="text" id="apiBase" value="https://freeai4ever-text-backend.onrender.com">
            </div>
            <div class="input-group">
                <label>Model</label>
                <input type="text" id="modelName" value="gateway-gpt-5-5">
            </div>
            <div class="quick-models">
                <span style="color:#555;font-size:12px;">Quick models:</span>
                <button onclick="setModel('gateway-gpt-5')">GPT-5</button>
                <button onclick="setModel('gateway-gpt-5-5')" class="active">GPT-5.5</button>
                <button onclick="setModel('gateway-gpt-4')">GPT-4</button>
                <button onclick="setModel('gateway-claude-3')">Claude 3</button>
                <button onclick="setModel('gateway-gemini-pro')">Gemini</button>
                <button onclick="setModel('gateway-llama-2')">Llama 2</button>
                <button onclick="setModel('gateway-mistral')">Mistral</button>
            </div>
        </div>
        
        <div class="test-section">
            <h3>📝 Step 1: Generate Chat <span id="genchatStatus" class="status-badge waiting">Not tested</span></h3>
            <div class="flex-row">
                <button class="btn btn-primary" onclick="testGenChat()">Test /genchat</button>
                <button class="btn btn-secondary" onclick="clearLogs()">Clear Logs</button>
                <button class="btn btn-warning" onclick="testHealth()">Test Health</button>
            </div>
            <div id="genchatResult" class="response-box">Waiting to test...</div>
        </div>
        
        <div class="test-section">
            <h3>💬 Step 2: Send Message <span id="chatStatus" class="status-badge waiting">Not tested</span></h3>
            <div class="input-group">
                <label>Message</label>
                <input type="text" id="testMessage" value="Hello! Who are you?">
            </div>
            <div class="flex-row">
                <button class="btn btn-primary" onclick="testChat()">Test /chat</button>
                <button class="btn btn-danger" onclick="clearChat()">Clear Chat</button>
            </div>
            <div id="chatResult" class="response-box">Waiting to test...</div>
        </div>
        
        <div class="test-section">
            <h3>💬 Live Chat</h3>
            <div id="liveChat" class="chat-messages"></div>
            <div id="typingIndicator" class="typing-indicator">AI is typing...</div>
            <div class="input-group" style="margin-top:10px;">
                <input type="text" id="liveMessage" placeholder="Type your message..." style="flex:1;padding:10px;border-radius:8px;border:1px solid #333;background:#0a0a1a;color:white;" onkeypress="if(event.key==='Enter') sendLiveMessage()">
                <button class="btn btn-primary" onclick="sendLiveMessage()">Send</button>
            </div>
        </div>
        
        <div class="test-section">
            <h3>📋 Logs</h3>
            <div id="logs" class="response-box" style="max-height:300px;">Ready...</div>
        </div>
    </div>

    <script>
        let chatId = null;
        let isProcessing = false;
        
        function setModel(model) {
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
            entry.innerHTML = '<span class="timestamp">[' + timestamp + ']</span><span class="' + type + '">' + emoji + ' ' + message + '</span>';
            logs.appendChild(entry);
            logs.scrollTop = logs.scrollHeight;
        }
        
        function clearLogs() {
            document.getElementById('logs').innerHTML = 'Ready...';
            addLog('info', 'Logs cleared');
        }
        
        function updateStatus(elementId, status, text) {
            const el = document.getElementById(elementId);
            el.className = 'status-badge ' + status;
            el.textContent = text;
        }
        
        async function testHealth() {
            const apiBase = document.getElementById('apiBase').value.trim();
            addLog('info', 'Testing health at ' + apiBase + '/health');
            
            try {
                const response = await fetch(apiBase + '/health');
                const data = await response.json();
                
                if (response.ok) {
                    addLog('success', 'Health check passed: ' + JSON.stringify(data));
                } else {
                    addLog('error', 'Health check failed: ' + response.status);
                }
            } catch (e) {
                addLog('error', 'Cannot reach API: ' + e.message);
            }
        }
        
        async function testGenChat() {
            const apiBase = document.getElementById('apiBase').value.trim();
            const model = document.getElementById('modelName').value.trim();
            
            if (!model) {
                addLog('error', 'Please enter a model name');
                return;
            }
            
            updateStatus('genchatStatus', 'loading', 'Testing...');
            document.getElementById('genchatResult').innerHTML = 'Sending request...';
            addLog('info', 'Generating chat with model: ' + model);
            
            try {
                const startTime = Date.now();
                const response = await fetch(apiBase + '/genchat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model: model })
                });
                
                const data = await response.json();
                const elapsed = Date.now() - startTime;
                
                if (response.ok && data.chatId) {
                    chatId = data.chatId;
                    updateStatus('genchatStatus', 'success', 'Success');
                    document.getElementById('genchatResult').innerHTML = 
                        '✅ SUCCESS (' + elapsed + 'ms)\n' +
                        'Chat ID: ' + data.chatId + '\n' +
                        'Model: ' + data.model + '\n' +
                        'Message: ' + (data.message || 'Chat created');
                    addLog('success', 'Chat generated: ' + chatId + ' (' + elapsed + 'ms)');
                } else {
                    updateStatus('genchatStatus', 'error', 'Failed');
                    document.getElementById('genchatResult').innerHTML = 
                        '❌ ERROR (' + elapsed + 'ms)\n' +
                        'Status: ' + response.status + '\n' +
                        'Response: ' + JSON.stringify(data, null, 2);
                    addLog('error', 'GenChat failed: ' + response.status);
                }
            } catch (error) {
                updateStatus('genchatStatus', 'error', 'Error');
                document.getElementById('genchatResult').innerHTML = 
                    '❌ NETWORK ERROR\n' + error.message;
                addLog('error', 'Network error: ' + error.message);
            }
        }
        
        async function testChat() {
            if (!chatId) {
                addLog('error', 'Generate a chat first (Step 1)');
                alert('Please generate a chat first!');
                return;
            }
            
            const apiBase = document.getElementById('apiBase').value.trim();
            const message = document.getElementById('testMessage').value.trim();
            
            if (!message) {
                addLog('error', 'Please enter a message');
                return;
            }
            
            updateStatus('chatStatus', 'loading', 'Testing...');
            document.getElementById('chatResult').innerHTML = 'Streaming response...\n';
            addLog('info', 'Sending message: "' + message + '"');
            
            try {
                const startTime = Date.now();
                const response = await fetch(apiBase + '/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chatId: chatId, message: message })
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    updateStatus('chatStatus', 'error', 'Failed');
                    document.getElementById('chatResult').innerHTML = 
                        '❌ ERROR\nStatus: ' + response.status + '\nResponse: ' + errorText;
                    addLog('error', 'Chat failed: ' + response.status);
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
                                    }
                                    
                                    if (data.done) {
                                        addLog('info', 'Stream done');
                                    }
                                    
                                    if (data.status) {
                                        addLog('info', 'Status: ' + data.status);
                                    }
                                } catch (e) {}
                            }
                        }
                    }
                }
                
                const elapsed = Date.now() - startTime;
                updateStatus('chatStatus', 'success', 'Success');
                resultDiv.innerHTML += '\n\n✅ COMPLETE (' + elapsed + 'ms) - ' + fullResponse.length + ' chars';
                addLog('success', 'Chat complete: ' + fullResponse.length + ' chars (' + elapsed + 'ms)');
                
                addLiveMessage('user', message);
                addLiveMessage('ai', fullResponse || 'No response received');
                
            } catch (error) {
                updateStatus('chatStatus', 'error', 'Error');
                document.getElementById('chatResult').innerHTML = 
                    '❌ NETWORK ERROR\n' + error.message;
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
        
        async function sendLiveMessage() {
            if (isProcessing) return;
            
            const input = document.getElementById('liveMessage');
            const message = input.value.trim();
            
            if (!message) return;
            input.value = '';
            
            if (!chatId) {
                addLog('error', 'Generate a chat first!');
                alert('Please generate a chat first!');
                return;
            }
            
            isProcessing = true;
            addLiveMessage('user', message);
            addLog('info', 'Live message: "' + message + '"');
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
                } else {
                    addLiveMessage('error', 'No response received');
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
            document.getElementById('chatResult').innerHTML = 'Waiting to test...';
            chatId = null;
            updateStatus('genchatStatus', 'waiting', 'Not tested');
            updateStatus('chatStatus', 'waiting', 'Not tested');
            document.getElementById('genchatResult').innerHTML = 'Waiting to test...';
            hideTyping();
            addLog('info', 'Chat cleared');
        }
        
        window.addEventListener('load', function() {
            setTimeout(testHealth, 500);
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
