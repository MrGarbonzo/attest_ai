// Attest AI - Frontend JavaScript Application

// Global state
let latestProofId = null;
let currentAttestations = {};
let isConnected = false;

// DOM elements
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendMessage');
const chatMessages = document.getElementById('chatMessages');
const proofPasswordInput = document.getElementById('proofPassword');
const downloadButton = document.getElementById('downloadProof');
const downloadStatus = document.getElementById('downloadStatus');
const proofFileInput = document.getElementById('proofFile');
const decryptPasswordInput = document.getElementById('decryptPassword');
const decryptButton = document.getElementById('decryptButton');
const decryptStatus = document.getElementById('decryptStatus');
const decryptedContent = document.getElementById('decryptedContent');
const chatStatus = document.getElementById('chatStatus');

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Attest AI Frontend Initialized');
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial status
    loadAttestationStatus();
    checkConnection();
    
    // Auto-update attestation status every 30 seconds
    setInterval(loadAttestationStatus, 30000);
    
    // Auto-update connection status every 10 seconds
    setInterval(checkConnection, 10000);
});

function setupEventListeners() {
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Proof functionality  
    downloadButton.addEventListener('click', downloadProof);
    decryptButton.addEventListener('click', decryptProofFile);
    
    // File input change
    proofFileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            updateDecryptStatus(`File selected: ${this.files[0].name}`, 'info');
        }
    });
}

// Chat Functions
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }
    
    const proofPassword = proofPasswordInput.value.trim() || null;
    
    // Disable input during request
    messageInput.disabled = true;
    sendButton.disabled = true;
    updateChatStatus('Sending message...', 'info');
    
    try {
        // Display user message immediately
        displayChatMessage('user', message);
        messageInput.value = '';
        
        // Send to API
        const response = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                proof_password: proofPassword
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Display AI response
            displayChatMessage('ai', data.response);
            
            // Update attestation data
            currentAttestations = data.attestations;
            updateAttestationDisplay(data.attestations);
            
            // Handle proof generation
            if (data.proof_generated && data.proof_id) {
                latestProofId = data.proof_id;
                updateDownloadButton(true, data.proof_id);
                updateChatStatus(`Message sent. Proof generated: ${data.proof_id}`, 'success');
            } else {
                updateChatStatus(`Message sent. Mode: ${data.mode}`, 'success');
            }
            
            // Update footer status
            updateSecretAiMode(data.mode);
            
        } else {
            throw new Error('API returned success: false');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        displayChatMessage('system', `Error: ${error.message}`);
        updateChatStatus(`Error: ${error.message}`, 'error');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

function displayChatMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const roleDiv = document.createElement('div');
    roleDiv.className = 'message-role';
    roleDiv.textContent = role.toUpperCase();
    
    const contentDiv = document.createElement('div');
    contentDiv.textContent = content;
    
    messageDiv.appendChild(roleDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Attestation Functions
async function loadAttestationStatus() {
    try {
        const response = await fetch('/api/v1/attestation/dual');
        if (response.ok) {
            const attestations = await response.json();
            updateAttestationDisplay(attestations);
            currentAttestations = attestations;
        } else {
            console.warn('Failed to load attestation status');
        }
    } catch (error) {
        console.error('Error loading attestation status:', error);
    }
}

function updateAttestationDisplay(attestations) {
    if (!attestations || !attestations.summary) {
        return;
    }
    
    const summary = attestations.summary;
    
    // Update self attestation
    updateAttestationStatus(
        'self',
        summary.self_status,
        summary.self_details,
        summary.self_mode
    );
    
    // Update Secret AI attestation
    updateAttestationStatus(
        'secretai',
        summary.secret_ai_status,
        summary.secret_ai_details,
        summary.secret_ai_mode
    );
    
    // Update overall quality
    updateOverallAttestationQuality(summary.attestation_quality);
    
    // Update details content
    updateAttestationDetails('selfDetails', attestations.self);
    updateAttestationDetails('secretaiDetails', attestations.secret_ai);
}

function updateAttestationStatus(type, status, details, mode) {
    const statusElement = document.getElementById(`${type}Status`);
    const textElement = document.getElementById(`${type}StatusText`);
    
    if (!statusElement || !textElement) return;
    
    // Update status indicator
    if (status === 'success' && mode === 'real') {
        statusElement.textContent = '✅';
        statusElement.title = 'Real attestation data available';
    } else if (status === 'success' && mode === 'mock') {
        statusElement.textContent = '⚠️';
        statusElement.title = 'Using mock attestation data';
    } else if (status === 'error') {
        statusElement.textContent = '❌';
        statusElement.title = 'Attestation failed or unavailable';
    } else {
        statusElement.textContent = '⏳';
        statusElement.title = 'Checking attestation status';
    }
    
    // Update status text
    textElement.textContent = details || status;
}

function updateOverallAttestationQuality(quality) {
    const qualityElement = document.getElementById('attestationQuality');
    if (!qualityElement) return;
    
    qualityElement.textContent = quality.charAt(0).toUpperCase() + quality.slice(1);
    qualityElement.className = `text-${getQualityColor(quality)}`;
}

function getQualityColor(quality) {
    switch (quality) {
        case 'high': return 'success';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'danger';
    }
}

function updateAttestationDetails(elementId, attestationData) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const detailsContent = element.querySelector('.details-content');
    if (!detailsContent) return;
    
    detailsContent.textContent = JSON.stringify(attestationData, null, 2);
}

function toggleDetails(targetId) {
    const element = document.getElementById(targetId);
    if (element) {
        element.classList.toggle('hidden');
    }
}

// Proof Download Functions
function updateDownloadButton(enabled, proofId) {
    downloadButton.disabled = !enabled;
    
    if (enabled && proofId) {
        downloadStatus.textContent = `Proof ${proofId} ready for download`;
        downloadStatus.className = 'status-message success';
        
        // Show proof info
        const proofInfo = document.getElementById('latestProofInfo');
        const proofDetails = document.getElementById('proofDetails');
        if (proofInfo && proofDetails) {
            proofDetails.textContent = `ID: ${proofId}`;
            proofInfo.classList.remove('hidden');
        }
    } else {
        downloadStatus.textContent = 'No proof available';
        downloadStatus.className = 'status-message';
        
        const proofInfo = document.getElementById('latestProofInfo');
        if (proofInfo) {
            proofInfo.classList.add('hidden');
        }
    }
}

async function downloadProof() {
    if (!latestProofId) {
        updateDownloadStatus('No proof available for download', 'error');
        return;
    }
    
    try {
        updateDownloadStatus('Downloading proof file...', 'info');
        
        const response = await fetch(`/api/v1/proof/download/${latestProofId}`);
        
        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }
        
        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${latestProofId}.attestproof`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        updateDownloadStatus(`Proof file downloaded: ${latestProofId}.attestproof`, 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        updateDownloadStatus(`Download failed: ${error.message}`, 'error');
    }
}

function updateDownloadStatus(message, type) {
    downloadStatus.textContent = message;
    downloadStatus.className = `status-message ${type || ''}`;
}

// Proof Decryption Functions
async function decryptProofFile() {
    const file = proofFileInput.files[0];
    const password = decryptPasswordInput.value.trim();
    
    if (!file) {
        updateDecryptStatus('Please select a .attestproof file', 'error');
        return;
    }
    
    if (!password) {
        updateDecryptStatus('Please enter the decryption password', 'error');
        return;
    }
    
    try {
        updateDecryptStatus('Decrypting proof file...', 'info');
        decryptButton.disabled = true;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('password', password);
        
        const response = await fetch('/api/v1/proof/decrypt', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            updateDecryptStatus(`Successfully decrypted: ${data.filename}`, 'success');
            displayDecryptedContent(data.proof_data);
        } else {
            throw new Error(data.detail || 'Decryption failed');
        }
        
    } catch (error) {
        console.error('Decryption error:', error);
        updateDecryptStatus(`Decryption failed: ${error.message}`, 'error');
        hideDecryptedContent();
    } finally {
        decryptButton.disabled = false;
    }
}

function displayDecryptedContent(proofData) {
    // Show chat data
    const chatDiv = document.getElementById('decryptedChat');
    if (chatDiv && proofData.chat_data) {
        let chatHtml = '';
        if (proofData.chat_data.messages) {
            proofData.chat_data.messages.forEach(msg => {
                chatHtml += `<div class="message ${msg.role}-message">
                    <div class="message-role">${msg.role.toUpperCase()}</div>
                    <div>${msg.content}</div>
                </div>`;
            });
        }
        chatDiv.innerHTML = chatHtml;
    }
    
    // Show attestation data
    const attestDiv = document.getElementById('decryptedAttestations');
    if (attestDiv && proofData.attestations) {
        attestDiv.innerHTML = `<div class="details-content">${JSON.stringify(proofData.attestations, null, 2)}</div>`;
    }
    
    // Show integrity data
    const integrityDiv = document.getElementById('decryptedIntegrity');
    if (integrityDiv && proofData.integrity) {
        let integrityHtml = '<div class="integrity-checks">';
        integrityHtml += `<p><strong>Chat Hash:</strong> ${proofData.integrity.chat_hash}</p>`;
        integrityHtml += `<p><strong>Attestation Hash:</strong> ${proofData.integrity.attestation_hash}</p>`;
        integrityHtml += `<p><strong>Combined Hash:</strong> ${proofData.integrity.combined_hash}</p>`;
        integrityHtml += `<p><strong>Algorithm:</strong> ${proofData.integrity.algorithm}</p>`;
        integrityHtml += '</div>';
        integrityDiv.innerHTML = integrityHtml;
    }
    
    // Show the decrypted content section
    decryptedContent.classList.remove('hidden');
}

function hideDecryptedContent() {
    decryptedContent.classList.add('hidden');
}

function updateDecryptStatus(message, type) {
    decryptStatus.textContent = message;
    decryptStatus.className = `status-message ${type || ''}`;
}

// Status Functions
function updateChatStatus(message, type) {
    chatStatus.textContent = message;
    chatStatus.className = `chat-status ${type || ''}`;
    
    // Clear status after 5 seconds
    setTimeout(() => {
        chatStatus.textContent = '';
        chatStatus.className = 'chat-status';
    }, 5000);
}

async function checkConnection() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            const data = await response.json();
            isConnected = true;
            updateConnectionStatus('🟢 Connected', data.components);
            updateLastUpdate();
        } else {
            throw new Error('Health check failed');
        }
    } catch (error) {
        isConnected = false;
        updateConnectionStatus('🔴 Disconnected');
    }
}

function updateConnectionStatus(status, components) {
    const connectionElement = document.getElementById('connectionStatus');
    if (connectionElement) {
        connectionElement.textContent = status;
    }
    
    // Update component statuses in footer if available
    if (components) {
        if (components.self_attestation === 'success') {
            // Host attestation is working
        }
    }
}

function updateSecretAiMode(mode) {
    const secretAiElement = document.getElementById('secretAiMode');
    if (secretAiElement) {
        const modeText = mode === 'real' ? '🟢 Real' : '🟡 Mock';
        secretAiElement.textContent = `Secret AI: ${modeText}`;
    }
}

function updateLastUpdate() {
    const lastUpdateElement = document.getElementById('lastUpdate');
    if (lastUpdateElement) {
        const now = new Date();
        lastUpdateElement.textContent = `Last update: ${now.toLocaleTimeString()}`;
    }
}

// Utility Functions
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function truncateString(str, maxLength) {
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

// Error Handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    updateChatStatus('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    updateChatStatus('An unexpected error occurred', 'error');
});

// Export functions for debugging
window.attestAI = {
    sendMessage,
    loadAttestationStatus,
    downloadProof,
    decryptProofFile,
    checkConnection,
    toggleDetails
};