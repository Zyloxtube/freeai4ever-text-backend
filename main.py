# ============================================================
# COMPLETE API FOR RENDER.COM WITH QUERY PARAMETER SUPPORT
# File: main.py
# ============================================================

from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
import requests
import json
import uuid
import time
import os

app = Flask(__name__, static_folder='.')

# Store chat sessions in memory (will reset on restart)
chat_sessions = {}

# Your API key
API_KEY = "ua_j7N_FLn1MXA0WJF_4B8XVKSvs1geQfR0"

@app.route('/')
def home():
    """Serve the HTML interface"""
    return send_from_directory('.', 'index.html')

@app.route('/genchat', methods=['POST', 'GET'])
def generate_chat():
    """
    Generate a new chat session with a specific model
    POST /genchat - Body: {"model": "gateway-gpt-5-5"}
    GET /genchat?model=gateway-gpt-5-5
    """
    try:
        # Get model from POST body or GET query
        model = None
        
        if request.method == 'POST':
            data = request.get_json()
            if data:
                model = data.get('model')
        else:  # GET
            model = request.args.get('model')
        
        # Check if model is provided
        if not model:
            return jsonify({
                "error": "Model is required",
                "message": "Please provide 'model' in POST body or GET query parameter"
            }), 400
        
        # Generate a unique chat ID
        chat_id = str(uuid.uuid4())
        
        # Store the chat session with model
        chat_sessions[chat_id] = {
            "model": model,
            "created_at": time.time(),
            "messages": []
        }
        
        return jsonify({
            "chatId": chat_id,
            "model": model,
            "message": f"Chat session created with model: {model}"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    """
    Send a message to an existing chat session
    POST /chat - Body: {"chatId": "abc-123", "message": "Hello!"}
    GET /chat?chatId=abc-123&message=Hello!
    """
    try:
        # Get parameters from POST body or GET query
        chat_id = None
        message = None
        
        if request.method == 'POST':
            data = request.get_json()
            if data:
                chat_id = data.get('chatId')
                message = data.get('message')
        else:  # GET
            chat_id = request.args.get('chatId')
            message = request.args.get('message')
        
        # Validate required fields
        if not chat_id:
            return jsonify({
                "error": "chatId is required"
            }), 400
            
        if not message:
            return jsonify({
                "error": "message is required"
            }), 400
        
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
        
        # For GET requests, return JSON response instead of streaming
        if request.method == 'GET':
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
                    timeout=60
                )
                
                if response.status_code == 200:
                    # Parse the streaming response into full text
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data: '):
                                try:
                                    data = json.loads(line_str[6:])
                                    if 'delta' in data:
                                        full_response += data['delta']
                                except:
                                    pass
                    
                    # Store assistant response
                    session['messages'].append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
                    return jsonify({
                        "chatId": chat_id,
                        "response": full_response,
                        "model": model
                    }), 200
                else:
                    return jsonify({
                        "error": "API error",
                        "status": response.status_code
                    }), response.status_code
                    
            except Exception as e:
                return jsonify({
                    "error": "Error processing request",
                    "message": str(e)
                }), 500
        
        # For POST requests, return streaming response
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
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """
    Get conversation history for a chat session
    GET /chat/history?chatId=abc-123
    """
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
        
        return jsonify({
            "chatId": chat_id,
            "model": session['model'],
            "messages": session['messages'],
            "message_count": len(session['messages'])
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/chat/delete', methods=['DELETE', 'GET'])
def delete_chat():
    """
    Delete a chat session
    DELETE /chat/delete - Body: {"chatId": "abc-123"}
    GET /chat/delete?chatId=abc-123
    """
    try:
        chat_id = None
        
        if request.method == 'DELETE':
            data = request.get_json()
            if data:
                chat_id = data.get('chatId')
        else:  # GET
            chat_id = request.args.get('chatId')
        
        if not chat_id:
            return jsonify({
                "error": "chatId is required"
            }), 400
        
        if chat_id in chat_sessions:
            del chat_sessions[chat_id]
            return jsonify({
                "message": f"Chat session {chat_id} deleted successfully"
            }), 200
        else:
            return jsonify({
                "error": "Chat session not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    models = [
        "gateway-gpt-5",
        "gateway-gpt-5-5",
        "gateway-gpt-4",
        "gateway-claude-3",
        "gateway-gemini-pro",
        "gateway-llama-2",
        "gateway-mistral"
    ]
    
    return jsonify({
        "models": models,
        "default": "gateway-gpt-5"
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "active_sessions": len(chat_sessions),
        "timestamp": time.time()
    }), 200

@app.route('/api-docs', methods=['GET'])
def api_docs():
    """API Documentation"""
    return jsonify({
        "name": "AI Chat API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "HTML chat interface",
            "POST /genchat": "Generate chat - Body: {'model': 'model-name'}",
            "GET /genchat": "Generate chat - ?model=model-name",
            "POST /chat": "Send message - Body: {'chatId': 'id', 'message': 'text'}",
            "GET /chat": "Send message - ?chatId=id&message=text",
            "GET /chat/history": "Get history - ?chatId=id",
            "DELETE /chat/delete": "Delete chat - Body: {'chatId': 'id'}",
            "GET /chat/delete": "Delete chat - ?chatId=id",
            "GET /models": "List available models",
            "GET /health": "Health check"
        },
        "examples": {
            "generate_chat_post": {
                "method": "POST",
                "url": "/genchat",
                "body": {"model": "gateway-gpt-5-5"}
            },
            "generate_chat_get": {
                "method": "GET",
                "url": "/genchat?model=gateway-gpt-5-5"
            },
            "send_message_post": {
                "method": "POST",
                "url": "/chat",
                "body": {"chatId": "chat-id", "message": "Hello!"}
            },
            "send_message_get": {
                "method": "GET",
                "url": "/chat?chatId=chat-id&message=Hello!"
            }
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
