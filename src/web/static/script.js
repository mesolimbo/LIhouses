/**
 * Client-side logic for LIhouses web interface
 *
 * Handles:
 * - Button clicks to trigger operations
 * - Real-time output streaming via Server-Sent Events (SSE)
 * - UI updates and status messages
 * - Automatic reconnection if page reloaded during operation
 */

// DOM elements
const btnDownload = document.getElementById('btn-download');
const btnGenerate = document.getElementById('btn-generate');
const btnClearLog = document.getElementById('btn-clear-log');
const logOutput = document.getElementById('log-output');
const statusMessage = document.getElementById('status-message');

// State
let currentEventSource = null;
let isOperationRunning = false;
let currentOperationType = null;

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('LIhouses Web Interface loaded');

    // Check server status on page load
    checkServerStatus();

    // Add button event listeners
    btnDownload.addEventListener('click', () => executeOperation('download'));
    btnGenerate.addEventListener('click', () => executeOperation('generate'));
    btnClearLog.addEventListener('click', clearLog);
});

/**
 * Execute an operation (download or generate)
 *
 * @param {string} operationType - "download" or "generate"
 */
async function executeOperation(operationType) {
    if (isOperationRunning) {
        showStatusMessage('error', 'Another operation is already running. Please wait.');
        return;
    }

    try {
        // Disable buttons
        currentOperationType = operationType;
        setButtonsEnabled(false);
        isOperationRunning = true;

        // Clear previous log
        clearLog();
        showStatusMessage('info', `Starting ${operationType} operation...`);

        // POST to /api/execute
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ operation_type: operationType })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to start operation');
        }

        // Get operation ID
        const operationId = data.operation_id;
        console.log('Operation started:', operationId);

        // Show success message
        showStatusMessage('info', `Operation started successfully. Streaming output...`);

        // Open SSE stream
        streamOperationOutput(operationId);

    } catch (error) {
        console.error('Error starting operation:', error);
        showStatusMessage('error', `Error: ${error.message}`);
        setButtonsEnabled(true);
        isOperationRunning = false;
        currentOperationType = null;
    }
}

/**
 * Open SSE connection to stream operation output
 *
 * @param {string} operationId - The operation ID
 */
function streamOperationOutput(operationId) {
    // Close existing EventSource if any
    if (currentEventSource) {
        currentEventSource.close();
    }

    // Create new EventSource
    const eventSource = new EventSource(`/api/stream/${operationId}`);
    currentEventSource = eventSource;

    // Listen for 'output' events
    eventSource.addEventListener('output', (event) => {
        const data = JSON.parse(event.data);
        appendLogLine(data.line);
    });

    // Listen for 'completed' events
    eventSource.addEventListener('completed', (event) => {
        const data = JSON.parse(event.data);
        console.log('Operation completed:', data);

        // Show success message
        let message = `<span>✓ ${data.summary || 'Operation completed successfully'}</span>`;

        // Add report links if available (for generate operations)
        if (data.links && data.links.length > 0) {
            message += '<div class="report-links">Reports: ';
            data.links.forEach((link, index) => {
                const filename = link.split('/').pop();
                message += `<a href="/reports/${link}" target="_blank">${filename}</a> `;
            });
            message += '</div>';
        }

        // Add download stats if available (for download operations)
        if (data.stats && data.stats.listings) {
            message += `<div class="download-stats">${data.stats.listings} listings downloaded</div>`;
        }

        showStatusMessage('success', message);

        // Clean up
        eventSource.close();
        currentEventSource = null;
        setButtonsEnabled(true);
        isOperationRunning = false;
        currentOperationType = null;
    });

    // Listen for 'failed' events
    eventSource.addEventListener('failed', (event) => {
        const data = JSON.parse(event.data);
        console.error('Operation failed:', data);

        showStatusMessage('error', `✗ ${data.error || 'Operation failed'}`);

        // Clean up
        eventSource.close();
        currentEventSource = null;
        setButtonsEnabled(true);
        isOperationRunning = false;
        currentOperationType = null;
    });

    // Listen for 'error' events
    eventSource.addEventListener('error', (event) => {
        console.error('SSE error:', event);

        // Only show error if we haven't already completed
        if (isOperationRunning) {
            showStatusMessage('error', 'Connection error. Please check if the server is running.');
        }

        // Clean up
        eventSource.close();
        currentEventSource = null;
        setButtonsEnabled(true);
        isOperationRunning = false;
        currentOperationType = null;
    });

    // Listen for 'heartbeat' events (just to keep connection alive)
    eventSource.addEventListener('heartbeat', (event) => {
        console.log('Heartbeat received');
    });
}

/**
 * Check server status on page load
 * If an operation is running, reconnect to its stream
 */
async function checkServerStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.current_operation) {
            console.log('Found running operation:', data.current_operation);

            // Disable buttons
            currentOperationType = data.current_operation.type;
            setButtonsEnabled(false);
            isOperationRunning = true;

            // Show status message
            showStatusMessage('info', `Resuming ${data.current_operation.type} operation...`);

            // Reconnect to stream
            streamOperationOutput(data.current_operation.id);
        }
    } catch (error) {
        console.error('Error checking server status:', error);
        showStatusMessage('error', 'Unable to connect to server. Is it running?');
    }
}

/**
 * Append a line to the log output
 *
 * @param {string} line - The log line to append
 */
function appendLogLine(line) {
    // Remove empty state message if present
    const emptyMessage = logOutput.querySelector('.log-empty');
    if (emptyMessage) {
        emptyMessage.remove();
    }

    // Create line element
    const lineElement = document.createElement('div');
    lineElement.className = 'log-line';

    // Add styling based on content
    if (line.toLowerCase().includes('error') || line.toLowerCase().includes('failed')) {
        lineElement.classList.add('error');
    } else if (line.toLowerCase().includes('complete') || line.toLowerCase().includes('success')) {
        lineElement.classList.add('success');
    } else if (line.toLowerCase().includes('warning')) {
        lineElement.classList.add('warning');
    }

    lineElement.textContent = line;

    // Append to log
    logOutput.appendChild(lineElement);

    // Auto-scroll to bottom
    logOutput.scrollTop = logOutput.scrollHeight;
}

/**
 * Clear the log output
 */
function clearLog() {
    logOutput.innerHTML = '<div class="log-empty">Waiting for output...</div>';
    hideStatusMessage();
}

/**
 * Show a status message
 *
 * @param {string} type - "success", "error", or "info"
 * @param {string} message - The message to display
 */
function showStatusMessage(type, message) {
    statusMessage.className = `status-message ${type}`;
    statusMessage.innerHTML = message;
    statusMessage.classList.remove('hidden');
}

/**
 * Hide the status message
 */
function hideStatusMessage() {
    statusMessage.classList.add('hidden');
}

/**
 * Enable or disable action buttons
 *
 * @param {boolean} enabled - Whether buttons should be enabled
 */
function setButtonsEnabled(enabled) {
    if (!enabled) {
        // Disable both buttons but only show loading on the active one
        btnDownload.disabled = true;
        btnGenerate.disabled = true;

        if (currentOperationType === 'download') {
            btnDownload.innerHTML = '<span class="loading"></span><span>Running...</span>';
        } else if (currentOperationType === 'generate') {
            btnGenerate.innerHTML = '<span class="loading"></span><span>Running...</span>';
        }
    } else {
        // Re-enable both buttons and restore their original content
        btnDownload.disabled = false;
        btnGenerate.disabled = false;

        btnDownload.innerHTML = `
            <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>Download Data</span>
        `;
        btnGenerate.innerHTML = `
            <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>Generate Reports</span>
        `;
    }
}
