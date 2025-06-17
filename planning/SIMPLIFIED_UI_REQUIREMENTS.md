# **Simplified UI Requirements**

## **Core Functionality Focus**
Keep the UI simple and functional. Focus on these 4 key features:

---

## **1. Automatic Proof Generation**

### **Behavior:**
- **IF password provided** → Automatically generate proof after each chat interaction
- **IF no password** → No proof generated
- **Simple password input** at top of interface
- **No complex encryption options** (just password or nothing)

### **Implementation:**
```html
<div class="proof-password-section">
    <label for="proofPassword">Proof Password (optional):</label>
    <input type="password" id="proofPassword" placeholder="Enter password to enable automatic proof generation">
    <small>Leave blank to disable proof generation</small>
</div>
```

### **Logic:**
- Check password field on every chat response
- If password exists → Generate proof automatically in background
- Show simple status: "Proof generated" or "No password set"

---

## **2. Download Button**

### **Simple Download Interface:**
```html
<div class="download-section">
    <h3>Download Latest Proof</h3>
    <button id="downloadProof" disabled>Download Proof File</button>
    <div id="downloadStatus">No proof available</div>
</div>
```

### **States:**
- **Disabled**: "No proof available" (when no password set or no chat yet)
- **Enabled**: "Download Proof File" (when proof exists)
- **Downloading**: "Downloading..." (during download)

---

## **3. Upload & Decrypt Proof Area**

### **Separate Section for Decryption:**
```html
<div class="decrypt-section">
    <h3>Decrypt Proof File</h3>
    <div class="upload-area">
        <input type="file" id="proofFile" accept=".attestproof">
        <label for="proofFile">Choose proof file to decrypt</label>
    </div>
    <div class="decrypt-password">
        <input type="password" id="decryptPassword" placeholder="Enter decryption password">
        <button id="decryptButton">Decrypt & View</button>
    </div>
    <div id="decryptedContent" class="hidden">
        <!-- Decrypted proof content will be displayed here -->
    </div>
</div>
```

### **Workflow:**
1. User uploads `.attestproof` file
2. User enters password
3. Click "Decrypt & View"
4. Show decrypted content (chat + attestation data)

---

## **4. Attestation Reports with Details**

### **Simple Attestation Display:**
```html
<div class="attestation-reports">
    <h3>Attestation Status</h3>
    
    <!-- Host Machine Attestation -->
    <div class="attestation-item">
        <div class="attestation-summary">
            <span class="status-indicator success">✓</span>
            <span class="attestation-title">Host Machine Attestation</span>
            <span class="attestation-status">Active</span>
        </div>
        <button class="details-btn" data-target="host-details">View Details</button>
        <div id="host-details" class="attestation-details hidden">
            <!-- Detailed attestation data -->
        </div>
    </div>
    
    <!-- Secret AI Attestation -->
    <div class="attestation-item">
        <div class="attestation-summary">
            <span class="status-indicator warning">⚠</span>
            <span class="attestation-title">Secret AI Attestation</span>
            <span class="attestation-status">Mock Data</span>
        </div>
        <button class="details-btn" data-target="secretai-details">View Details</button>
        <div id="secretai-details" class="attestation-details hidden">
            <!-- Detailed attestation data -->
        </div>
    </div>
</div>
```

### **Details View:**
- **Collapsed by default** - just shows status summary
- **"View Details" button** expands to show full attestation data
- **Color-coded status indicators**: ✓ (green), ⚠ (yellow), ✗ (red)

---

## **Complete Simplified Layout**

### **Full Page Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Attest AI - Simple Interface</title>
</head>
<body>
    <div class="container">
        <header>
            <h1>Attest AI</h1>
            <p>Privacy-Preserving AI Chat with Attestation</p>
        </header>
        
        <!-- 1. Proof Password Setting -->
        <section class="proof-password-section">
            <label for="proofPassword">Proof Password (optional):</label>
            <input type="password" id="proofPassword" placeholder="Enter password to enable automatic proof generation">
        </section>
        
        <!-- Chat Interface -->
        <section class="chat-section">
            <div id="chatMessages"></div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Type your message...">
                <button id="sendMessage">Send</button>
            </div>
        </section>
        
        <!-- 4. Attestation Reports -->
        <section class="attestation-reports">
            <h3>Attestation Status</h3>
            <!-- Host and Secret AI attestation items -->
        </section>
        
        <!-- 2. Download Section -->
        <section class="download-section">
            <h3>Download Latest Proof</h3>
            <button id="downloadProof">Download Proof File</button>
            <div id="downloadStatus">No proof available</div>
        </section>
        
        <!-- 3. Upload & Decrypt Section -->
        <section class="decrypt-section">
            <h3>Decrypt Proof File</h3>
            <input type="file" id="proofFile" accept=".attestproof">
            <input type="password" id="decryptPassword" placeholder="Enter decryption password">
            <button id="decryptButton">Decrypt & View</button>
            <div id="decryptedContent" class="hidden"></div>
        </section>
    </div>
</body>
</html>
```

---

## **Updated Build Plan Integration**

### **Phase 5: Simplified UI Implementation (Week 3-4)**

#### **Task 5.1: Core Functionality Implementation**
1. **Automatic proof generation** with password check
2. **Simple download button** with status indicators
3. **File upload & decrypt** interface
4. **Collapsible attestation details** with summary view

#### **Task 5.2: API Endpoints (Updated)**
```python
# Simplified proof workflow
POST /api/v1/chat
{
    "message": "Should I invest in SCRT?",
    "proof_password": "optional-password"  # If provided, auto-generate proof
}

Response:
{
    "response": "Based on analysis...",
    "attestations": { /* attestation data */ },
    "proof_generated": true,  # if password was provided
    "proof_id": "uuid-here"   # for download
}

# Simple download endpoint
GET /api/v1/proof/download/{proof_id}
# Returns encrypted .attestproof file

# Decrypt endpoint (for uploaded files)
POST /api/v1/proof/decrypt
{
    "file_data": "base64-encoded-file",
    "password": "decryption-password"
}

Response:
{
    "success": true,
    "chat_history": [ /* messages */ ],
    "attestations": { /* attestation data */ },
    "timestamp": "2025-06-17T10:30:00Z"
}
```

#### **Task 5.3: Simple JavaScript Logic**
- **Password monitoring**: Check proof password field on each chat
- **Automatic proof generation**: Trigger in background if password exists
- **Download management**: Enable/disable download button based on proof availability
- **File upload handling**: Process uploaded .attestproof files
- **Details toggle**: Show/hide attestation details on button click

---

## **Success Criteria (Simplified)**

### **Functional Requirements:**
- [ ] **Password field** controls automatic proof generation
- [ ] **Download button** provides latest proof file when available
- [ ] **File upload** accepts .attestproof files for decryption
- [ ] **Attestation summaries** show status with expandable details
- [ ] **No complex UI** - focus on core functionality

### **User Workflow:**
1. **Optional**: Enter proof password to enable automatic proof generation
2. **Chat**: Send messages to Secret AI (proofs auto-generated if password set)
3. **Download**: Click download button to get latest proof file
4. **Decrypt**: Upload any proof file with password to view contents
5. **Attestation**: View status summaries, expand for technical details

This simplified approach removes all the complex UI elements and focuses on the 4 core features you specified while maintaining all the backend functionality from the original build plan.
