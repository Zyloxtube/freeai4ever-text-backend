# ============================================================
# COMPLETE API FOR RENDER.COM WITH CORS
# File: main.py
# ============================================================

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests
import json
import uuid
import time
import os

app = Flask(__name__)

# Enable CORS for all routes and all origins
CORS(app, origins='*', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], allow_headers=['*'])

# Store chat sessions in memory (will reset on restart)
chat_sessions = {}

# Your API key
API_KEY = "ua_j7N_FLn1MXA0WJF_4B8XVKSvs1geQfR0"

@app.route('/genchat', methods=['POST', 'OPTIONS'])
def generate_chat():
    """
    Generate a new chat session with a specific model
    POST /genchat
    Body: {"model": "gateway-gpt-5-5"}
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        # Check if model is provided
        if not data or 'model' not in data:
            return jsonify({
                "error": "Model is required",
                "message": "Please provide 'model' in the request body"
            }), 400
        
        model = data['model']
        
        # Generate a unique chat ID
        chat_id = str(uuid.uuid4())
        
        # Store the chat session with model
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
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    """
    Send a message to an existing chat session
    POST /chat
    Body: {"chatId": "abc-123", "message": "Hello!"}
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                "error": "Missing request body"
            }), 400
            
        if 'chatId' not in data:
            return jsonify({
                "error": "chatId is required"
            }), 400
            
        if 'message' not in data:
            return jsonify({
                "error": "message is required"
            }), 400
        
        chat_id = data['chatId']
        message = data['message']
        
        # Check if chat exists
        if chat_id not in chat_sessions:
            return jsonify({
                "error": "Chat session not found",
                "message": f"Chat ID {chat_id} does not exist"
            }), 404
        
        # Get the chat session
        session = chat_sessions[chat_id]
        model = session['model']
        
        # Add user message to history
        session['messages'].append({
            "role": "user",
            "content": message
        })
        
        # Forward request to actual API
        def generate():
            full_response = ""
            
            try:
                # Build the request to the actual API
                payload = {
                    "message": message,
                    "model": model,
                    "effort": "medium"
                }
                
                # Send request to the real API
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
                
                # Stream the response back to the client
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        
                        # Forward raw line
                        yield f"{line_str}\n\n"
                        
                        # Parse and store delta if present
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if 'delta' in data:
                                    full_response += data['delta']
                                elif 'finish' in data:
                                    # Response complete
                                    pass
                            except:
                                pass
                
                # Store assistant response in history
                if full_response:
                    session['messages'].append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
        
        # Return streaming response with CORS headers
        response = Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        )
        return response
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/chat/history', methods=['GET', 'OPTIONS'])
def get_chat_history():
    """
    Get conversation history for a chat session
    GET /chat/history?chatId=abc-123
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        chat_id = request.args.get('chatId')
        
        if not chat_id:
            return jsonify({
                "error": "chatId is required as query parameter"
            }), 400
        
        if chat_id not in chat_sessions:
            return jsonify({
                "error": "Chat session not found"
            }), 404
        
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
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/chat/delete', methods=['DELETE', 'OPTIONS'])
def delete_chat():
    """
    Delete a chat session
    DELETE /chat/delete
    Body: {"chatId": "abc-123"}
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        if not data or 'chatId' not in data:
            return jsonify({
                "error": "chatId is required"
            }), 400
        
        chat_id = data['chatId']
        
        if chat_id in chat_sessions:
            del chat_sessions[chat_id]
            response = jsonify({
                "message": f"Chat session {chat_id} deleted successfully"
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 200
        else:
            return jsonify({
                "error": "Chat session not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/models', methods=['GET', 'OPTIONS'])
def list_models():
    """
    List available models
    GET /models
    """
    if request.method == 'OPTIONS':
        return '', 200
        
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
        return '', 200
        
    response = jsonify({
        "status": "healthy",
        "active_sessions": len(chat_sessions),
        "timestamp": time.time()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

@app.route('/', methods=['GET', 'OPTIONS'])
def home():
    """API information"""
    if request.method == 'OPTIONS':
        return '', 200
        
    response = jsonify({
        "name": "AI Chat API",
        "version": "1.0.0",
        "endpoints": {
            "POST /genchat": "Generate a new chat session - Body: {'model': 'model-name'}",
            "POST /chat": "Send a message - Body: {'chatId': 'id', 'message': 'text'}",
            "GET /chat/history": "Get chat history - Query: ?chatId=id",
            "DELETE /chat/delete": "Delete chat session - Body: {'chatId': 'id'}",
            "GET /models": "List available models",
            "GET /health": "Health check"
        },
        "example": {
            "genchat": {
                "method": "POST",
                "url": "/genchat",
                "body": {"model": "gateway-gpt-5-5"}
            },
            "chat": {
                "method": "POST",
                "url": "/chat",
                "body": {"chatId": "generated-id", "message": "Hello!"}
            }
        }
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 200

# Handle preflight requests for all routes
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
