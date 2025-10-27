"""
Script execution logic using subprocess.

This module handles the execution of existing Python scripts (download and generate)
as subprocesses, capturing their output in real-time for streaming to the web UI.
"""

import subprocess
import threading
import os
import uuid
import sys
from datetime import datetime
from collections import deque


# Map operation types to script paths
SCRIPT_PATHS = {
    "download": os.path.join("src", "homes", "rentcast_homes.py"),
    "generate": os.path.join("src", "report", "generate_reports.py")
}

# Maximum number of output lines to keep in memory
MAX_OUTPUT_LINES = 1000


def execute_script(script_type, execution_state):
    """
    Execute a Python script (download or generate) and capture output.

    Args:
        script_type (str): "download" or "generate"
        execution_state (dict): Global state dict to store operation

    Returns:
        str: Operation ID (UUID)

    Raises:
        ValueError: If script_type is invalid
        FileNotFoundError: If script file doesn't exist
    """
    if script_type not in SCRIPT_PATHS:
        raise ValueError(f"Invalid script type: {script_type}")

    script_path = SCRIPT_PATHS[script_type]
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Create operation ID
    operation_id = str(uuid.uuid4())

    # Create Operation data structure
    operation = {
        "id": operation_id,
        "type": script_type,
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "exit_code": None,
        "output_lines": deque(maxlen=MAX_OUTPUT_LINES),
        "error_message": None,
        "result_summary": None,
        "report_links": None,
        "download_stats": None
    }

    # Start subprocess
    try:
        # Set environment variables
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        # Set matplotlib to use non-interactive backend (required for subprocess)
        env['MPLBACKEND'] = 'Agg'

        # Use pipenv run to execute in the proper environment
        process = subprocess.Popen(
            ['pipenv', 'run', 'python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=os.getcwd(),
            env=env
        )
    except Exception as e:
        raise RuntimeError(f"Failed to start script: {str(e)}")

    # Start output capture thread
    output_thread = threading.Thread(
        target=_capture_output,
        args=(process, operation, execution_state),
        daemon=True
    )
    output_thread.start()

    # Store in execution state
    execution_state['current_operation'] = operation
    execution_state['process'] = process
    execution_state['output_thread'] = output_thread

    return operation_id


def _capture_output(process, operation, execution_state):
    """
    Thread function to capture subprocess output line-by-line.

    Args:
        process (Popen): The running subprocess
        operation (dict): The Operation dict
        execution_state (dict): Global state dict
    """
    try:
        # Read stdout/stderr line-by-line
        for line in iter(process.stdout.readline, ''):
            if line:
                # Strip newline and append to operation output
                clean_line = line.rstrip('\n\r')
                operation['output_lines'].append(clean_line)

        # Wait for process to complete
        process.wait()

        # Update operation with completion status
        operation['end_time'] = datetime.now().isoformat()
        operation['exit_code'] = process.returncode

        if process.returncode == 0:
            operation['status'] = 'completed'
            # Try to extract result summary from output
            operation['result_summary'] = _extract_result_summary(operation)
            # Try to extract report links if generate operation
            if operation['type'] == 'generate':
                operation['report_links'] = _extract_report_links(operation)
            # Try to extract download stats if download operation
            elif operation['type'] == 'download':
                operation['download_stats'] = _extract_download_stats(operation)
        else:
            operation['status'] = 'failed'
            operation['error_message'] = _extract_error_message(operation)

    except Exception as e:
        # Handle unexpected errors
        operation['status'] = 'failed'
        operation['exit_code'] = -1
        operation['end_time'] = datetime.now().isoformat()
        operation['error_message'] = f"Unexpected error during execution: {str(e)}"
        operation['output_lines'].append(f"ERROR: {str(e)}")

    finally:
        # Clean up
        if process.stdout:
            process.stdout.close()


def _extract_result_summary(operation):
    """
    Extract a result summary from the operation output.

    Args:
        operation (dict): The Operation dict

    Returns:
        str: Result summary or None
    """
    try:
        # Look for specific patterns in the output
        output_lines = list(operation['output_lines'])

        # For download operations, provide a clean summary
        if operation['type'] == 'download':
            # Look for listing count information
            for line in reversed(output_lines):
                if 'listings' in line.lower():
                    # Extract just the count info
                    return "Data download completed successfully"
            return "Data download completed successfully"

        # For generate operations, look for report generation messages
        elif operation['type'] == 'generate':
            # Check for index generation or report generation
            for line in reversed(output_lines):
                if 'index saved to' in line.lower():
                    return "Reports generated successfully"
                if 'report saved to' in line.lower():
                    return "Reports generated successfully"
                if 'all reports generated successfully' in line.lower():
                    return "Reports generated successfully"
                if 'report already exists' in line.lower():
                    return "Reports up to date (already generated)"
            return "Report generation completed successfully"

        return "Operation completed successfully"
    except Exception:
        return "Operation completed successfully"


def _extract_report_links(operation):
    """
    Extract report file links from the operation output.

    Args:
        operation (dict): The Operation dict

    Returns:
        list: List of relative report paths (e.g., ["index.html"]) or None
    """
    try:
        # Look for .html files in the output
        output_lines = list(operation['output_lines'])
        report_links = []
        index_link = None

        for line in output_lines:
            # Look for "saved to:" patterns
            if 'saved to:' in line.lower() and '.html' in line:
                # Try to extract file path after "saved to:"
                parts = line.split('saved to:')
                if len(parts) > 1:
                    file_path = parts[1].strip()

                    # Handle paths with .tmp in them
                    if '.tmp' in file_path:
                        # Convert to relative path (remove .tmp/ prefix and any backslashes)
                        # Handle both forward slashes and backslashes
                        relative_path = file_path.replace('\\', '/').split('.tmp/')[-1]

                        # Prioritize index.html
                        if 'index.html' in relative_path:
                            index_link = relative_path
                        else:
                            report_links.append(relative_path)

        # Return index.html as the primary link if found
        if index_link:
            return [index_link]

        return report_links if report_links else None
    except Exception:
        return None


def _extract_download_stats(operation):
    """
    Extract download statistics from the operation output.

    Args:
        operation (dict): The Operation dict

    Returns:
        dict: Download stats or None
    """
    try:
        # Look for listing count information
        output_lines = list(operation['output_lines'])
        import re

        # Look for the final total count first (most accurate)
        for line in reversed(output_lines):
            # Match patterns like "Total Long Island homes loaded: 234"
            if 'total long island homes loaded' in line.lower():
                match = re.search(r'loaded:\s*(\d+)', line.lower())
                if match:
                    count = match.group(1)
                    return {'listings': count}

            # Match patterns like "Total homes found: 234"
            if 'total homes found' in line.lower():
                match = re.search(r'found:\s*(\d+)', line.lower())
                if match:
                    count = match.group(1)
                    return {'listings': count}

        # Fallback: look for any listing count
        for line in reversed(output_lines):
            if 'listing' in line.lower():
                match = re.search(r'(\d+)\s+listing', line.lower())
                if match:
                    count = match.group(1)
                    return {'listings': count}

        return None
    except Exception:
        # If extraction fails, just return None
        return None


def _extract_error_message(operation):
    """
    Extract a user-friendly error message from the operation output.

    Args:
        operation (dict): The Operation dict

    Returns:
        str: Error message
    """
    # Look for error patterns in the output
    output_lines = list(operation['output_lines'])

    for line in reversed(output_lines):
        # Look for specific error patterns
        if 'Error:' in line or 'ERROR:' in line:
            return line
        if 'environment variable' in line.lower():
            return line
        if 'failed' in line.lower():
            return line

    # Default error message
    return f"Script failed with exit code {operation['exit_code']}"
