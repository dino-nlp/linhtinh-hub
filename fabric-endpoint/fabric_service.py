#!/usr/bin/env python3
"""
Fabric Endpoint Service for LibreChat
Cung cấp bridge giữa LibreChat và Fabric AI framework
"""

import os
import json
import requests
import subprocess
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
import time
from typing import Dict, List, Optional, Generator
import threading
import queue

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cấu hình Fabric
FABRIC_BASE_URL = os.environ.get('FABRIC_BASE_URL', 'http://localhost:8080')
FABRIC_API_KEY = os.environ.get('FABRIC_API_KEY', '')

# Danh sách patterns có sẵn trong Fabric
AVAILABLE_PATTERNS = [
    'analyze_claims',
    'extract_wisdom', 
    'summarize',
    'create_summary',
    'improve_writing',
    'translate',
    'create_quiz',
    'analyze_paper',
    'create_report',
    'extract_insights',
    'create_outline',
    'analyze_code',
    'debug_code',
    'explain_code',
    'write_essay',
    'create_presentation'
]

class FabricClient:
    """Client để tương tác với Fabric API"""
    
    def __init__(self, base_url: str = FABRIC_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def format_fabric_output(self, raw_output: str) -> str:
        """Format Fabric output để hiển thị tốt hơn trong LibreChat UI"""
        if not raw_output:
            return raw_output
        
        # Convert markdown headers to plain text with proper formatting
        lines = raw_output.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Convert markdown headers to formatted text
            if line.startswith('# '):
                # Main headers - sử dụng ASCII characters
                header_text = line[2:].strip()
                formatted_lines.append('')
                formatted_lines.append('=' * 50)
                formatted_lines.append(f'>> {header_text.upper()}')
                formatted_lines.append('=' * 50)
            elif line.startswith('## '):
                # Sub headers
                header_text = line[3:].strip()
                formatted_lines.append('')
                formatted_lines.append(f'-- {header_text}')
                formatted_lines.append('-' * 30)
            elif line.startswith('### '):
                # Sub-sub headers
                header_text = line[4:].strip()
                formatted_lines.append('')
                formatted_lines.append(f'* {header_text}')
            elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                # Numbered lists - add spacing and bullet
                formatted_lines.append(f'  - {line.strip()}')
            elif line.strip().startswith('-'):
                # Bullet points
                content = line.strip()[1:].strip()
                formatted_lines.append(f'  - {content}')
            elif line.strip():
                # Regular content - preserve
                formatted_lines.append(line)
            else:
                # Empty lines - preserve but limit consecutive empty lines
                if not formatted_lines or formatted_lines[-1].strip():
                    formatted_lines.append('')
        
        # Join lines and clean up excessive empty lines
        result = '\n'.join(formatted_lines)
        
        # Remove excessive empty lines (more than 2 consecutive)
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
        
    def list_patterns(self) -> List[str]:
        """Lấy danh sách patterns có sẵn"""
        try:
            # Thử gọi Fabric CLI để lấy patterns
            result = subprocess.run(['fabric', '--listpatterns'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                patterns = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return patterns
        except Exception as e:
            logger.warning(f"Không thể lấy patterns từ Fabric CLI: {e}")
        
        # Fallback về danh sách mặc định
        return AVAILABLE_PATTERNS
    
    def call_fabric_pattern(self, pattern: str, input_text: str, 
                           variables: Optional[Dict] = None, 
                           stream: bool = False) -> Dict:
        """Gọi Fabric pattern với input text"""
        try:
            # Nếu có API endpoint, sử dụng REST API
            if self.base_url != 'http://localhost:8080':
                return self._call_fabric_api(pattern, input_text, variables, stream)
            else:
                # Sử dụng Fabric CLI
                return self._call_fabric_cli(pattern, input_text, stream)
        except Exception as e:
            logger.error(f"Lỗi khi gọi Fabric pattern {pattern}: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu với pattern {pattern}."
            }
    
    def _call_fabric_api(self, pattern: str, input_text: str, 
                        variables: Optional[Dict] = None, stream: bool = False) -> Dict:
        """Gọi Fabric thông qua REST API"""
        payload = {
            "prompts": [{
                "userInput": input_text,
                "patternName": pattern,
                "model": "gpt-4o",
                "vendor": "openai",
                "variables": variables or {}
            }],
            "temperature": 0.7,
            "stream": stream
        }
        
        headers = {'Content-Type': 'application/json'}
        if FABRIC_API_KEY:
            headers['Authorization'] = f'Bearer {FABRIC_API_KEY}'
            
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            raw_response = response.json().get('response', response.text)
            formatted_response = self.format_fabric_output(raw_response)
            return {
                'success': True,
                'response': formatted_response
            }
        else:
            return {
                'success': False,
                'error': f"API Error: {response.status_code}",
                'response': "Không thể xử lý yêu cầu qua Fabric API."
            }
    
    def _call_fabric_cli(self, pattern: str, input_text: str, stream: bool = False) -> Dict:
        """Gọi Fabric thông qua CLI"""
        try:
            cmd = ['fabric', '--pattern', pattern]
            if stream:
                cmd.append('--stream')
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=input_text, timeout=120)
            
            if process.returncode == 0:
                # Format output cho LibreChat UI
                formatted_output = self.format_fabric_output(stdout.strip())
                return {
                    'success': True,
                    'response': formatted_output
                }
            else:
                logger.error(f"Fabric CLI error: {stderr}")
                return {
                    'success': False,
                    'error': stderr,
                    'response': "Không thể xử lý yêu cầu qua Fabric CLI."
                }
                
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'error': "Timeout",
                'response': "Yêu cầu đã hết thời gian chờ."
            }

# Khởi tạo Fabric client
fabric_client = FabricClient()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Fabric Endpoint Service',
        'version': '1.0.0'
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    """Liệt kê các models/patterns có sẵn"""
    patterns = fabric_client.list_patterns()
    
    models = []
    for pattern in patterns:
        models.append({
            'id': f'fabric-{pattern}',
            'object': 'model',
            'created': int(time.time()),
            'owned_by': 'fabric',
            'permission': [],
            'root': f'fabric-{pattern}',
            'parent': None
        })
    
    return jsonify({
        'object': 'list',
        'data': models
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Main endpoint để xử lý chat completions từ LibreChat"""
    try:
        data = request.get_json()
        
        # Extract thông tin từ request
        messages = data.get('messages', [])
        model = data.get('model', 'fabric-summarize')
        stream = data.get('stream', False)
        temperature = data.get('temperature', 0.7)
        
        # Lấy pattern từ model name
        pattern = model.replace('fabric-', '') if model.startswith('fabric-') else 'summarize'
        
        # Kết hợp tất cả messages thành input text
        input_text = ""
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                input_text += f"System: {content}\n\n"
            elif role == 'user':
                input_text += f"User: {content}\n\n"
            elif role == 'assistant':
                input_text += f"Assistant: {content}\n\n"
        
        input_text = input_text.strip()
        
        logger.info(f"Processing request with pattern: {pattern}")
        logger.info(f"Input length: {len(input_text)} characters")
        
        if stream:
            return stream_fabric_response(pattern, input_text)
        else:
            return process_fabric_request(pattern, input_text)
            
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}")
        return jsonify({
            'error': {
                'message': f'Internal server error: {str(e)}',
                'type': 'internal_error',
                'code': 'internal_error'
            }
        }), 500

def process_fabric_request(pattern: str, input_text: str) -> Response:
    """Xử lý request Fabric không streaming"""
    result = fabric_client.call_fabric_pattern(pattern, input_text)
    
    if result['success']:
        response_text = result['response']
    else:
        response_text = result.get('response', 'Đã xảy ra lỗi khi xử lý yêu cầu.')
    
    # Format response theo OpenAI API
    response = {
        'id': f'chatcmpl-{int(time.time())}',
        'object': 'chat.completion',
        'created': int(time.time()),
        'model': f'fabric-{pattern}',
        'choices': [{
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': response_text
            },
            'finish_reason': 'stop'
        }],
        'usage': {
            'prompt_tokens': len(input_text.split()),
            'completion_tokens': len(response_text.split()),
            'total_tokens': len(input_text.split()) + len(response_text.split())
        }
    }
    
    return jsonify(response)

def stream_fabric_response(pattern: str, input_text: str) -> Response:
    """Xử lý request Fabric với streaming"""
    def generate():
        try:
            # Gọi Fabric
            result = fabric_client.call_fabric_pattern(pattern, input_text, stream=True)
            
            if result['success']:
                response_text = result['response']
                
                # Chia response thành chunks
                words = response_text.split()
                chunk_size = 5  # Gửi 5 từ mỗi lần
                
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = ' ' + ' '.join(chunk_words)
                    
                    chunk = {
                        'id': f'chatcmpl-{int(time.time())}',
                        'object': 'chat.completion.chunk',
                        'created': int(time.time()),
                        'model': f'fabric-{pattern}',
                        'choices': [{
                            'index': 0,
                            'delta': {
                                'content': chunk_text
                            },
                            'finish_reason': None
                        }]
                    }
                    
                    yield f"data: {json.dumps(chunk)}\n\n"
                    time.sleep(0.05)  # Delay nhỏ để có hiệu ứng streaming
                
                # Final chunk
                final_chunk = {
                    'id': f'chatcmpl-{int(time.time())}',
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': f'fabric-{pattern}',
                    'choices': [{
                        'index': 0,
                        'delta': {},
                        'finish_reason': 'stop'
                    }]
                }
                
                yield f"data: {json.dumps(final_chunk)}\n\n"
            else:
                # Error chunk
                error_chunk = {
                    'id': f'chatcmpl-{int(time.time())}',
                    'object': 'chat.completion.chunk',
                    'created': int(time.time()),
                    'model': f'fabric-{pattern}',
                    'choices': [{
                        'index': 0,
                        'delta': {
                            'content': result.get('response', 'Đã xảy ra lỗi khi xử lý yêu cầu.')
                        },
                        'finish_reason': 'stop'
                    }]
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            error_chunk = {
                'id': f'chatcmpl-{int(time.time())}',
                'object': 'chat.completion.chunk',
                'created': int(time.time()),
                'model': f'fabric-{pattern}',
                'choices': [{
                    'index': 0,
                    'delta': {
                        'content': f'Lỗi: {str(e)}'
                    },
                    'finish_reason': 'stop'
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/v1/patterns', methods=['GET'])
def list_patterns():
    """Endpoint để liệt kê tất cả patterns có sẵn"""
    patterns = fabric_client.list_patterns()
    return jsonify({
        'patterns': patterns,
        'count': len(patterns)
    })

@app.route('/v1/patterns/<pattern_name>', methods=['POST'])
def execute_pattern(pattern_name: str):
    """Endpoint để thực thi một pattern cụ thể"""
    try:
        data = request.get_json()
        input_text = data.get('input', '')
        variables = data.get('variables', {})
        stream = data.get('stream', False)
        
        if not input_text:
            return jsonify({
                'error': 'Input text is required'
            }), 400
            
        result = fabric_client.call_fabric_pattern(pattern_name, input_text, variables, stream)
        
        return jsonify({
            'pattern': pattern_name,
            'success': result['success'],
            'response': result['response'],
            'error': result.get('error')
        })
        
    except Exception as e:
        logger.error(f"Error executing pattern {pattern_name}: {e}")
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Fabric Endpoint Service...")
    logger.info(f"Fabric Base URL: {FABRIC_BASE_URL}")
    
    # Kiểm tra Fabric có sẵn không
    try:
        result = subprocess.run(['fabric', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Fabric CLI detected: {result.stdout.strip()}")
        else:
            logger.warning("Fabric CLI not found, will use API mode")
    except Exception as e:
        logger.warning(f"Fabric CLI check failed: {e}")
    
    # Start server
    app.run(host='0.0.0.0', port=8081, debug=False)
