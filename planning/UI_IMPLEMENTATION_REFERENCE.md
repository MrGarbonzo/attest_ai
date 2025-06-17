# **UI Implementation Quick Reference**

## **Overview**
This document provides quick reference for implementing the new "Attest AI" interface design across the build plan phases.

---

## **Design Integration Summary**

### **What Changed:**
- **OLD**: Basic HTML panels with simple styling
- **NEW**: Professional "Attest AI" interface with dark cryptographic theme
- **Added**: Status card layout, responsive design, real-time updates
- **Enhanced**: Chat interface, proof generation workflow, error handling

### **Key Design Files:**
- **Main Build Plan**: `NEW_MVP_BUILD_PLAN.md` - Updated Phase 5 with UI tasks
- **Design Specifications**: `UI_DESIGN_SPECIFICATIONS.md` - Complete design system
- **Original Mockup**: `ui.png` - Reference image for target design

---

## **Implementation Phases**

### **Week 3: Core UI Structure (Task 5.1-5.3)**
```html
<!-- Target Layout Structure -->
<header class="app-header">Attest AI [MOCK MODE]</header>
<section class="attestation-section">
    <div class="attestation-grid">
        <div class="attestation-card self-attestation">...</div>
        <div class="attestation-card secretai-attestation">...</div>
    </div>
</section>
<section class="chat-section">...</section>
<section class="proof-section">...</section>
```

### **Week 3: Styling System (Task 5.4)**
```css
/* Primary Color Variables */
--primary-bg: #1a1f3a;      /* Dark navy */
--secondary-bg: #2d3553;    /* Card backgrounds */
--accent-blue: #4a9eff;     /* Attest AI branding */
--status-success: #10b981;  /* Green badges */
--status-error: #ef4444;    /* Red badges */
```

### **Week 4: Interactive Features (Task 5.5)**
- **Status card polling** every 30 seconds
- **Real-time mode indicators** (MOCK/LIVE)
- **Chat status updates** (Connected/Disconnected)
- **Proof generation states** (Ready/Generating/Success/Error)

### **Week 4: Testing & Polish (Task 5.7)**
- **Responsive breakpoints**: 768px (mobile), 1024px (desktop)
- **Accessibility**: Keyboard navigation, ARIA labels
- **Visual consistency**: Dark theme, typography hierarchy

---

## **Status Card Implementation**

### **Card States & Colors**
```javascript
// Status mapping for attestation cards
const STATUS_CONFIG = {
    'loading': { badge: 'CHECKING...', color: '#3b82f6', icon: '⏳' },
    'success': { badge: 'SUCCESS', color: '#10b981', icon: '✅' },
    'failed':  { badge: 'FAILED', color: '#ef4444', icon: '❌' },
    'error':   { badge: 'ERROR', color: '#ef4444', icon: '⚠️' },
    'mock':    { badge: 'MOCK DATA', color: '#f59e0b', icon: '🔄' }
};
```

### **Self Attestation Card**
- **Always attempts real data** from localhost:29343
- **Shows specific errors** when connection fails
- **Machine ID format**: `secretvm-{environment}-{id}`
- **Timestamp format**: `6/17/2025, 2:52:42 AM`

### **Secret AI Attestation Card**
- **Real data when available**, graceful fallback to mock
- **Connection status** indicator for Secret AI instances
- **Model information** when connected successfully
- **"Failed to load attestation"** error state

---

## **Chat Interface Features**

### **Message Bubble Design**
```html
<!-- User Message -->
<div class="message message-user">
    <div class="message-content">Should I invest in SCRT?</div>
    <div class="message-meta">2:53 PM</div>
</div>

<!-- AI Response with Attestation -->
<div class="message message-ai">
    <div class="message-content">Based on my analysis...</div>
    <div class="message-meta">
        <span>2:53 PM</span>
        <span class="attestation-indicator">🛡️ Attested</span>
    </div>
</div>
```

### **Chat Status Indicator**
- **Green dot + "Connected to Secret AI"** when online
- **Red dot + "Disconnected"** when offline
- **Yellow dot + "Connecting..."** during connection attempts

---

## **Proof Generation Workflow**

### **Encryption Options**
```html
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
```

### **Generation States**
- **Ready**: "Ready to generate proof" (default)
- **Generating**: "Generating encrypted proof..." + spinner
- **Success**: "Proof generated successfully - Download ready" + download button
- **Error**: "Failed to generate proof: {specific error message}"

---

## **Responsive Design Breakpoints**

### **Desktop (≥1024px)**
- **Two-column attestation grid** side by side
- **Fixed chat height** with scrollable message area
- **Expanded proof options** with inline radio buttons

### **Tablet (768px-1023px)**
- **Single column stacked cards** for attestation
- **Collapsible sections** for better space usage
- **Touch-friendly button sizes** (min 44px)

### **Mobile (≤767px)**
- **Full-width stacked layout** for all sections
- **Simplified attestation cards** with collapsed details by default
- **Bottom-fixed chat input** for better mobile UX
- **Full-width buttons** for easy thumb tapping

---

## **Development Checklist**

### **Week 3 Deliverables:**
- [ ] **Header with mode indicator** ([MOCK MODE] / [LIVE MODE])
- [ ] **Status card grid layout** with proper spacing
- [ ] **Chat interface structure** with message bubbles
- [ ] **Proof generation form** with encryption options
- [ ] **CSS color system** and typography implemented
- [ ] **Basic responsive breakpoints** functional

### **Week 4 Deliverables:**
- [ ] **Real-time attestation polling** updates status cards
- [ ] **Chat functionality** with AI response display
- [ ] **Mode indicators** correctly show real vs mock data
- [ ] **Proof generation workflow** completes end-to-end
- [ ] **Error handling** with user-friendly messages
- [ ] **Mobile responsive** layout tested and working
- [ ] **Accessibility features** (keyboard nav, ARIA labels)

---

## **Integration with Backend**

### **API Response Format for UI**
```javascript
// Expected format for attestation status updates
{
    "status": "success|failed|error|loading|mock",
    "data": {
        "machine_id": "secretvm-mock-1234",
        "timestamp": "2025-06-17T02:52:42Z",
        "mode": "mock|real",
        "details": { /* attestation data */ }
    },
    "error": "Connection timeout" // if status is error/failed
}
```

### **Real-time Updates**
- **Polling interval**: 30 seconds for attestation status
- **WebSocket option**: Consider for real-time chat status
- **Error retry logic**: Exponential backoff for failed requests

---

## **File Structure**

### **Expected Static Files**
```
static/
├── css/
│   ├── main.css          # Core styling system
│   ├── components.css    # Component-specific styles
│   └── responsive.css    # Media queries
├── js/
│   ├── app.js           # Main application logic
│   ├── attestation.js   # Status card updates
│   ├── chat.js          # Chat interface
│   └── proof.js         # Proof generation
└── fonts/
    ├── Inter/           # Primary UI font
    └── JetBrainsMono/   # Monospace for code/data
```

### **HTML Template Structure**
```html
<!DOCTYPE html>
<html lang="en" class="dark-theme">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attest AI - Privacy-Preserving AI Chat</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <div class="app-container">
        <!-- Header, attestation cards, chat, proof sections -->
    </div>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

This design system transforms the application into a professional cryptographic attestation interface while maintaining all functional requirements from the original build plan.
