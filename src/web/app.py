#!/usr/bin/env python3
"""
Flask web server for triggering LIhouses data scripts via browser UI.

This module provides a simple web interface that allows users to:
- Trigger data download scripts (rentcast_homes.py)
- Trigger report generation scripts (generate_reports.py)
- Monitor script execution in real-time via Server-Sent Events (SSE)
"""

import os
import sys
import json
import time
import webbrowser
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from executor import execute_script

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Global state (in-memory) - tracks the currently running operation
execution_state = {
    'current_operation': None,
    'process': None,
    'output_thread': None
}

# Required environment variables for each operation type
REQUIRED_ENV_VARS = {
    "download": ["RENTCAST_API_KEY"],
    "generate": ["GOOGLE_MAPS_API_KEY"]
}


def validate_env_vars(operation_type):
    """
    Validate required environment variables exist for operation.

    Args:
        operation_type (str): "download" or "generate"

    Raises:
        ValueError: If required env var is missing
    """
    required_vars = REQUIRED_ENV_VARS.get(operation_type, [])
    for var in required_vars:
        if not os.environ.get(var):
            raise ValueError(
                f"Missing required environment variable: {var}. "
                f"Please add it to your .env file."
            )


@app.route('/')
def index():
    """Serve main UI."""
    return render_template('index.html')


@app.route('/api/execute', methods=['POST'])
def execute_operation():
    """
    Start script execution.

    Request body:
        {
            "operation_type": "download" | "generate"
        }

    Returns:
        JSON response with operation ID or error
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "Request body must be JSON"
            }), 400

        operation_type = data.get('operation_type')
        if not operation_type:
            return jsonify({
                "status": "error",
                "error": "Missing required field: operation_type"
            }), 400

        # Validate operation type
        if operation_type not in ['download', 'generate']:
            return jsonify({
                "status": "error",
                "error": f"Invalid operation type: '{operation_type}'. Must be 'download' or 'generate'."
            }), 400

        # Check for running operation
        if execution_state['current_operation'] is not None:
            return jsonify({
                "status": "error",
                "error": "Cannot start operation: another operation is already running"
            }), 409

        # Validate environment variables
        try:
            validate_env_vars(operation_type)
        except ValueError as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 400

        # Execute script
        try:
            operation_id = execute_script(operation_type, execution_state)
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": f"Failed to start script: {str(e)}"
            }), 500

        # Return success with operation ID
        return jsonify({
            "status": "success",
            "operation_id": operation_id,
            "message": "Operation started successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route('/api/stream/<operation_id>')
def stream_operation(operation_id):
    """
    Stream real-time output via Server-Sent Events (SSE).

    Args:
        operation_id (str): The operation ID

    Returns:
        SSE stream with output events
    """
    def event_stream():
        """Generator function for SSE."""
        # Get current operation
        operation = execution_state.get('current_operation')

        if not operation or operation['id'] != operation_id:
            yield f"event: error\ndata: {json.dumps({'error': 'Operation not found'})}\n\n"
            return

        # Track which lines we've already sent
        sent_lines = 0
        last_heartbeat = time.time()

        # Stream existing output lines
        current_lines = list(operation['output_lines'])
        for line in current_lines:
            yield f"event: output\ndata: {json.dumps({'line': line})}\n\n"
        sent_lines = len(current_lines)

        # Stream new output as it arrives
        while operation['status'] == 'running':
            # Check for new lines
            current_lines = list(operation['output_lines'])
            if len(current_lines) > sent_lines:
                # Send new lines
                for line in current_lines[sent_lines:]:
                    yield f"event: output\ndata: {json.dumps({'line': line})}\n\n"
                sent_lines = len(current_lines)
                last_heartbeat = time.time()

            # Send heartbeat to keep connection alive
            if time.time() - last_heartbeat > 15:
                yield f"event: heartbeat\ndata: {json.dumps({})}\n\n"
                last_heartbeat = time.time()

            # Small delay to avoid busy-waiting
            time.sleep(0.1)

        # Send any final lines
        current_lines = list(operation['output_lines'])
        if len(current_lines) > sent_lines:
            for line in current_lines[sent_lines:]:
                yield f"event: output\ndata: {json.dumps({'line': line})}\n\n"

        # Send completion event
        if operation['status'] == 'completed':
            event_data = {
                'exit_code': operation['exit_code'],
                'summary': operation['result_summary'],
                'links': operation['report_links']
            }
            yield f"event: completed\ndata: {json.dumps(event_data)}\n\n"
        else:
            event_data = {
                'exit_code': operation['exit_code'],
                'error': operation['error_message']
            }
            yield f"event: failed\ndata: {json.dumps(event_data)}\n\n"

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get server and current operation status.

    Returns:
        JSON response with server status and current operation (if any)
    """
    operation = execution_state.get('current_operation')

    if operation:
        operation_info = {
            'id': operation['id'],
            'type': operation['type'],
            'status': operation['status'],
            'start_time': operation['start_time']
        }
    else:
        operation_info = None

    return jsonify({
        'server_status': 'running',
        'current_operation': operation_info
    }), 200


@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses for browser compatibility."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


if __name__ == '__main__':
    # Create .tmp directory if doesn't exist
    os.makedirs('.tmp', exist_ok=True)

    # Display startup message
    print("=" * 60)
    print("LIhouses Web Interface")
    print("=" * 60)
    print("Server starting...")
    print(f"Server URL: http://localhost:8080")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Open browser automatically (with small delay to ensure server is ready)
    import threading
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://localhost:8080')

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start Flask dev server
    try:
        app.run(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server stopped. Goodbye!")
        print("=" * 60)
