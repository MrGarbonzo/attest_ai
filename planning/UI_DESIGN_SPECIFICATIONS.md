# **UI Design Specifications - Attest AI Interface**

## **Overview**
Update the attest_ai application UI to match the provided "Attest AI [MOCK MODE]" design with cryptographic attestation theme, dark UI, and professional layout.

---

## **New UI Design Theme: "Attest AI"**

### **Design Goals**
- **Professional cryptographic interface** with dark theme
- **Clear attestation status visualization** using status cards
- **Intuitive proof generation workflow** 
- **Clean, modern layout** with good visual hierarchy
- **Mobile-responsive design** for accessibility

### **Color Palette & Typography**
```css
/* Primary Colors */
--primary-bg: #1a1f3a;           /* Dark navy background */
--secondary-bg: #2d3553;         /* Card backgrounds */
--accent-blue: #4a9eff;          /* Attest AI branding blue */
--accent-teal: #22d3ee;          /* Interactive elements */

/* Status Colors */
--status-success: #10b981;       /* Green for success */
--status-error: #ef4444;         /* Red for failed/error */
--status-warning: #f59e0b;       /* Amber for warnings */
--status-info: #3b82f6;          /* Blue for info */

/* Text Colors */
--text-primary: #f1f5f9;         /* Primary white text */
--text-secondary: #94a3b8;       /* Secondary gray text */
--text-muted: #64748b;           /* Muted text */

/* Typography */
--font-primary: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Courier New', monospace;
```

---

## **Layout Structure**

### **Header Section**
```html
<header class="app-header">
    <div class="header-content">
        <h1 class="app-title">
            Attest AI 
            <span class="mode-indicator">[MOCK MODE]</span>
        </h1>
        <p class="app-subtitle">Privacy-Preserving AI Chat with Cryptographic Attestation</p>
    </div>
</header>
```

**Design Requirements:**
- **Title**: Large, prominent "Attest AI" in accent blue
- **Mode indicator**: "[MOCK MODE]" in red when using fallback data, "[LIVE MODE]" in green when real
- **Subtitle**: Descriptive tagline in secondary text color
- **Full-width header** with gradient background

### **Main Content Layout**
```html
<main class="main-content">
    <!-- Attestation Status Section -->
    <section class="attestation-section">
        <h2>Attestation Status</h2>
        <div class="attestation-grid">
            <div class="attestation-card self-attestation">
                <!-- Self Attestation Status -->
            </div>
            <div class="attestation-card secretai-attestation">
                <!-- Secret AI Attestation Status -->
            </div>
        </div>
    </section>

    <!-- Chat Interface Section -->
    <section class="chat-section">
        <!-- Chat messages and input -->
    </section>

    <!-- Proof Generation Section -->
    <section class="proof-section">
        <!-- Proof generation controls -->
    </section>
</main>
```

---

## **Attestation Status Cards**

### **Card Structure**
Each attestation card follows this pattern:

```html
<div class="attestation-card" data-status="failed|success|error|loading">
    <div class="card-header">
        <h3 class="card-title">Self Attestation</h3>
        <div class="status-badge status-failed">FAILED</div>
    </div>
    
    <div class="card-content">
        <div class="attestation-details">
            <div class="detail-row">
                <span class="detail-label">Machine ID:</span>
                <span class="detail-value">secretvm-mock-1234</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Type:</span>
                <span class="detail-value">self</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Timestamp:</span>
                <span class="detail-value">6/17/2025, 2:52:42 AM</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Mode:</span>
                <span class="detail-value mode-indicator">Mock Data</span>
            </div>
        </div>
        
        <div class="card-actions">
            <button class="btn-secondary btn-sm" data-action="view-raw">
                🔍 Raw Attestation Data
            </button>
        </div>
    </div>
</div>
```

### **Status Badge Variants**
- **FAILED** (Red): Real attestation failed to load
- **SUCCESS** (Green): Real attestation loaded successfully  
- **ERROR** (Red): Connection or parsing error
- **LOADING** (Blue): Currently fetching attestation
- **MOCK** (Orange): Using fallback mock data

### **Self Attestation Card**
- **Title**: "Self Attestation"
- **Description**: attest_ai VM attestation status
- **Always attempts real data** from localhost:29343
- **Shows specific error messages** when real data fails
- **Machine ID format**: `secretvm-{environment}-{id}`

### **Secret AI Attestation Card**  
- **Title**: "Secret AI Attestation"
- **Description**: Available Secret AI instances
- **Falls back gracefully** to mock when unavailable
- **Error state**: "Failed to load attestation"
- **Action button**: "Raw Attestation Data" expands details

---

## **Chat Interface Design**

### **Chat Container**
```html
<section class="chat-section">
    <div class="chat-header">
        <h2>AI Chat Interface</h2>
        <div class="chat-status">
            <span class="status-indicator active"></span>
            <span>Connected to Secret AI</span>
        </div>
    </div>
    
    <div class="chat-messages" id="chatMessages">
        <!-- Message bubbles -->
    </div>
    
    <div class="chat-input-container">
        <div class="input-group">
            <textarea 
                class="chat-input" 
                placeholder="Type your message here..."
                id="messageInput"
            ></textarea>
            <button class="btn-primary send-btn" id="sendMessage">
                Send
            </button>
        </div>
        
        <div class="chat-options">
            <label class="checkbox-label">
                <input type="checkbox" id="captureAttestation" checked>
                <span>Capture attestation with response</span>
            </label>
        </div>
    </div>
</section>
```

### **Message Bubble Design**
```html
<!-- User Message -->
<div class="message message-user">
    <div class="message-content">
        <p>Should I invest in SCRT tokens?</p>
    </div>
    <div class="message-meta">
        <span class="message-time">2:53 PM</span>
    </div>
</div>

<!-- AI Response -->
<div class="message message-ai">
    <div class="message-content">
        <p>Based on my analysis of the Secret Network ecosystem...</p>
    </div>
    <div class="message-meta">
        <span class="message-time">2:53 PM</span>
        <span class="attestation-indicator">🛡️ Attested</span>
    </div>
</div>
```

---

## **Proof Generation Section**

### **Generate Proof Interface**
```html
<section class="proof-section">
    <div class="section-header">
        <h2>Generate Proof</h2>
        <p class="section-description">
            Create an encrypted, verifiable proof of your conversation
        </p>
    </div>
    
    <div class="proof-options">
        <div class="encryption-method">
            <h3>Encryption Method</h3>
            <div class="radio-group">
                <label class="radio-label">
                    <input type="radio" name="encryption" value="password" checked>
                    <span>Password Protection</span>
                </label>
                <label class="radio-label">
                    <input type="radio" name="encryption" value="auto">
                    <span>Auto-Generated Key</span>
                </label>
            </div>
        </div>
        
        <div class="password-input" id="passwordInput">
            <label for="proofPassword">Custom Password (Optional)</label>
            <input 
                type="password" 
                id="proofPassword" 
                placeholder="Leave blank for auto-generation"
                class="form-input"
            >
        </div>
    </div>
    
    <div class="proof-actions">
        <button class="btn-primary btn-lg" id="generateProof">
            Generate Proof
        </button>
        <div class="proof-status" id="proofStatus">
            <span class="status-text">Ready to generate proof</span>
        </div>
    </div>
</section>
```

### **Proof Generation States**
- **Ready**: "Ready to generate proof"
- **Generating**: "Generating encrypted proof..." (with spinner)
- **Success**: "Proof generated successfully - Download ready"
- **Error**: "Failed to generate proof: {error message}"

---

## **Responsive Design Requirements**

### **Desktop Layout (≥1024px)**
- **Two-column attestation cards** side by side
- **Fixed chat height** with scrollable messages
- **Expanded proof options** with inline controls

### **Tablet Layout (768px - 1023px)**
- **Stacked attestation cards** in single column
- **Collapsible sections** for better space usage
- **Touch-friendly button sizes**

### **Mobile Layout (≤767px)**
- **Stacked layout** for all sections
- **Simplified attestation cards** with collapsed details
- **Bottom-fixed chat input** for better UX
- **Full-width buttons** for easy tapping

---

## **Interactive Features**

### **Real-time Updates**
- **Attestation status polling** every 30 seconds
- **Live chat status indicator** (connected/disconnected)
- **Automatic proof expiry countdown** for downloaded files

### **Expandable Content**
- **"Raw Attestation Data" button** opens modal with JSON data
- **Message timestamps** show full date on hover
- **Error details** expandable for debugging

### **User Feedback**
- **Toast notifications** for actions (proof generated, download ready)
- **Loading spinners** during attestation retrieval
- **Progress indicators** for file generation and download

---

## **Implementation Plan Integration**

### **Phase 5.1: Core UI Structure (Week 3)**
1. **Implement base layout** with header, sections, and grid
2. **Create attestation card components** with status variants  
3. **Build chat interface** with message bubbles
4. **Add responsive breakpoints** and mobile layout

### **Phase 5.2: Interactive Features (Week 4)**
1. **Connect attestation polling** to status cards
2. **Implement chat functionality** with real-time updates
3. **Add proof generation workflow** with encryption options
4. **Create expandable/collapsible content areas**

### **Phase 5.3: Polish & Testing (Week 4)**
1. **Add loading states and transitions**
2. **Implement toast notifications** and user feedback
3. **Test responsive design** across devices
4. **Validate accessibility** with keyboard navigation

---

## **Assets & Dependencies**

### **CSS Framework**
- **Tailwind CSS** for utility classes and responsive design
- **Custom CSS** for specific component styling and animations
- **CSS Grid/Flexbox** for layout structure

### **Icons & Graphics**
- **Lucide Icons** for UI elements (🔍, 🛡️, ⚠️, ✅)
- **Custom status indicators** for attestation states
- **Animated loading spinners** for async operations

### **Fonts**
- **Inter** for primary UI text (clean, modern)
- **JetBrains Mono** for code/data display (attestation details)

---

## **Success Metrics**

### **Visual Design**
- [ ] **Consistent dark theme** across all components
- [ ] **Clear status communication** with color-coded indicators
- [ ] **Professional appearance** suitable for enterprise use
- [ ] **Smooth animations** and transitions

### **User Experience**
- [ ] **Intuitive workflow** from chat to proof generation
- [ ] **Clear error messaging** when attestation fails
- [ ] **Responsive design** works on mobile and desktop
- [ ] **Accessible interface** with keyboard navigation

### **Functional Integration**
- [ ] **Real-time attestation updates** reflect actual status
- [ ] **Chat interface** connects to Secret AI backend
- [ ] **Proof generation** produces downloadable files
- [ ] **Mock mode indicators** clearly show fallback data

This UI design specification transforms the application into a professional cryptographic attestation interface that matches your provided mockup while maintaining all the functional requirements from the original build plan.
