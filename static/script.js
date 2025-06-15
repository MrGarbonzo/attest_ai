// Global state
let currentProof = null;
let isProcessing = false;

// Initialize on page load
window.addEventListener('load', function() {
    loadWalletInfo();
    loadSelfAttestation();
    
    // Enable enter key for sending messages
    document.getElementById('messageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// Load wallet information
async function loadWalletInfo() {
    try {
        const response = await fetch('/wallet-info');
        const data = await response.json();
        
        const walletInfo = document.getElementById('walletInfo');
        if (data.success || data.mock) {
            const statusClass = data.mock ? 'warning' : 'success';
            const statusIcon = data.mock ? '⚠️' : '✅';
            walletInfo.innerHTML = `
                <div class="${statusClass}">${statusIcon} ${data.mock ? 'Mock Wallet' : 'Wallet Loaded'}</div>
                <div>Address: ${data.address.substring(0, 10)}...</div>
                <div>Balance: ${data.balance_ar}</div>
            `;
        } else {
            walletInfo.innerHTML = `<div class="error">Error: ${data.error}</div>`;
        }
    } catch (error) {
        document.getElementById('walletInfo').innerHTML = 
            `<div class="error">Failed to load wallet info</div>`;
    }
}

// Load self-attestation
async function loadSelfAttestation() {
    try {
        const response = await fetch('/self-attestation');
        const data = await response.json();
        
        const selfAttestation = document.getElementById('selfAttestation');
        if (data.success) {
            selfAttestation.innerHTML = `
                <div class="success">✅ Verified SecretVM</div>
                <div>mr_td: ${data.mr_td ? data.mr_td.substring(0, 8) + '...' : 'N/A'}</div>
            `;
        } else {
            selfAttestation.innerHTML = `<div class="error">❌ ${data.error || 'Failed to get attestation'}</div>`;
        }
    } catch (error) {
        document.getElementById('selfAttestation').innerHTML = 
            `<div class="error">Failed to load attestation</div>`;
    }
}

// Send message to Secret AI
async function sendMessage() {
    if (isProcessing) return;
    
    const messageInput = document.getElementById('messageInput');
    const passwordInput = document.getElementById('passwordInput');
    const message = messageInput.value.trim();
    const password = passwordInput.value.trim();
    
    // Validation
    if (!message) {
        alert('Please enter a message');
        return;
    }
    if (!password) {
        alert('Please enter an encryption password');
        return;
    }
    
    isProcessing = true;
    document.getElementById('sendButton').disabled = true;
    document.getElementById('sendButton').textContent = 'Processing...';
    
    // Show user message
    addMessage('user', message);
    messageInput.value = '';
    
    // Show processing indicator
    addMessage('system', '🔄 Processing with Secret AI...');
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: message,
                password: password
            })
        });
        
        if (!response.ok) {
            const error = await response.text();
            throw new Error(`HTTP ${response.status}: ${error}`);
        }
        
        const data = await response.json();
        
        // Remove processing message
        removeLastMessage();
        
        // Show AI response
        addMessage('ai', data.response);
        
        // Update Secret AI status
        updateSecretAiStatus(data.secret_ai_status);
        
        // Store proof and show actions
        currentProof = data.proof;
        document.getElementById('proofSection').style.display = 'block';
        updateProofDetails(data.proof);
        
        // Clear upload status
        document.getElementById('uploadStatus').innerHTML = '';
        
    } catch (error) {
        removeLastMessage();
        addMessage('error', `Error: ${error.message}`);
    } finally {
        isProcessing = false;
        document.getElementById('sendButton').disabled = false;
        document.getElementById('sendButton').textContent = 'Send Message';
    }
}

// Download proof as JSON file
function downloadProof() {
    if (!currentProof) return;
    
    const dataStr = JSON.stringify(currentProof, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `attest_ai_proof_${currentProof.proof_id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    document.getElementById('uploadStatus').innerHTML = 
        '<div class="success">✅ Proof downloaded successfully!</div>';
}

// Upload proof to Arweave
async function uploadToArweave() {
    if (!currentProof) return;
    
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = '<div class="processing">🔄 Uploading to Arweave...</div>';
    
    try {
        const response = await fetch('/upload-to-arweave', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({proof: currentProof})
        });
        
        if (!response.ok) {
            const error = await response.text();
            throw new Error(`HTTP ${response.status}: ${error}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.innerHTML = `
                <div class="success">✅ Uploaded to Arweave!</div>
                <div>Transaction: <a href="${result.arweave_url}" target="_blank">${result.transaction_id.substring(0, 20)}...</a></div>
                <div>Cost: ${result.cost_ar} AR | Size: ${result.data_size} bytes</div>
            `;
        } else {
            const statusClass = result.mocked ? 'warning' : 'error';
            const icon = result.mocked ? '⚠️' : '❌';
            statusDiv.innerHTML = `
                <div class="${statusClass}">${icon} ${result.mocked ? 'Mock upload created' : 'Upload failed'}</div>
                <div>Transaction: ${result.transaction_id.substring(0, 20)}...</div>
                ${result.note ? `<div class="note">${result.note}</div>` : ''}
                <div class="note">Cost estimate: ${result.cost_ar} AR | Size: ${result.data_size} bytes</div>
            `;
        }
        
        // Refresh wallet info
        loadWalletInfo();
        
    } catch (error) {
        statusDiv.innerHTML = `<div class="error">❌ Upload error: ${error.message}</div>`;
    }
}

// Helper functions
function addMessage(type, content) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = content;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function removeLastMessage() {
    const messages = document.getElementById('messages');
    if (messages.lastChild) {
        messages.removeChild(messages.lastChild);
    }
}

function updateSecretAiStatus(status) {
    const statusDiv = document.getElementById('secretAiStatus');
    if (status.mock) {
        statusDiv.innerHTML = `
            <div class="warning">⚠️ Using mock responses</div>
            <div class="note">Real Secret AI unavailable</div>
        `;
    } else {
        statusDiv.innerHTML = `
            <div class="success">✅ Connected to Secret AI</div>
            <div>Model: ${status.model || 'Unknown'}</div>
        `;
    }
}

function updateProofDetails(proof) {
    const details = document.getElementById('proofDetails');
    
    // Create a summary view of the proof
    const summary = {
        proof_id: proof.proof_id,
        timestamp: proof.timestamp,
        version: proof.version,
        verification_hashes: proof.verification,
        attestation_status: {
            attest_ai_vm: proof.attestations.attest_ai_vm.status,
            secret_ai_vm: proof.attestations.secret_ai_vm.status
        },
        encrypted_conversation: proof.encrypted_conversation ? 'Present (encrypted)' : 'Missing'
    };
    
    details.innerHTML = `<pre>${JSON.stringify(summary, null, 2)}</pre>`;
}