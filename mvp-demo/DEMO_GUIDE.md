# ProvenSense MVP Demo Guide

## 5-Minute Demo Script

### Pre-Demo Setup (2 minutes)
1. **Hardware Check**: Verify camera and accelerometer are connected
2. **Start System**: Run `./start-demo.sh` and wait for services to start
3. **Open Browser**: Navigate to `http://your-pi-ip:3000`
4. **Confirm Status**: Dashboard shows all hardware as "Ready"

---

### Demo Flow

#### **Minute 1: Introduction**
*"Today I'll show you ProvenSense - a secure sensor data capture system with cryptographic provenance."*

**What to show:**
- Open the dashboard
- Point out the system status indicators
- Highlight "0 Total Captures" to start

**Key talking points:**
- "This solves the data integrity problem for IoT and robotics"
- "Every sensor reading gets cryptographically signed"
- "Tamper-evident proof that data is authentic"

#### **Minute 2: Live Capture Demo**
*"Watch this - when I tap the accelerometer, it automatically triggers a photo capture."*

**What to do:**
1. **Tap the sensor** (or use manual capture if needed)
2. **Watch the dashboard update** in real-time
3. **Show the new photo** appearing instantly

**Key talking points:**
- "Interrupt-driven capture - motion triggers the event"
- "Sub-2 second response time from sensor to signed photo"
- "All data linked together with precise timestamps"

#### **Minute 3: Gallery & Data**
*"Let's look at what was captured and the associated sensor data."*

**What to show:**
1. **Click on Gallery** tab
2. **Click the captured photo** to open details
3. **Show accelerometer data** and metadata
4. **Point out the signature** and verification status

**Key talking points:**
- "Complete audit trail of every capture"
- "Sensor readings linked to visual evidence"
- "Cryptographic signatures prove authenticity"

#### **Minute 4: Verification**
*"Now let's verify the cryptographic integrity of our data."*

**What to do:**
1. **Go to Verify** tab
2. **Click "Verify All"** to check all signatures
3. **Show 100% success rate** and green checkmarks
4. **Click individual verification** to show technical details

**Key talking points:**
- "Hardware-backed cryptographic verification"
- "Tamper detection - any changes would break signatures"
- "Legal-grade evidence of data authenticity"

#### **Minute 5: Value Proposition**
*"This demonstrates the complete solution for secure sensor data."*

**What to highlight:**
- **Real-time monitoring** via web interface
- **Automatic capture** triggered by physical events
- **Cryptographic provenance** for every data point
- **Compliance ready** for auditing and regulations

**Business benefits:**
- "Solves data integrity problems for IoT deployments"
- "Reduces audit costs with automated verification"
- "Enables new use cases requiring provable sensor data"

---

## Interactive Demo Scenarios

### Scenario A: Security Audit
*"Imagine you're being audited and need to prove your sensor data is authentic..."*

1. Show multiple captures from different times
2. Verify all signatures successfully
3. Export verification report
4. Demonstrate tamper detection

### Scenario B: IoT Deployment
*"Picture thousands of these sensors deployed in the field..."*

1. Show real-time monitoring capabilities
2. Demonstrate remote capture triggering
3. Display system health monitoring
4. Show data export for analysis

### Scenario C: Compliance Use Case
*"For industries requiring data integrity..."*

1. Show timestamp accuracy with RTC
2. Demonstrate signature verification
3. Show complete audit trail
4. Export compliance-ready reports

---

## Demo Troubleshooting

### Common Issues & Quick Fixes

#### No captures appearing
- **Check**: Manual capture button works first
- **Fix**: Increase accelerometer sensitivity in code
- **Backup**: Use manual capture for demo

#### Camera not working
- **Check**: `/dev/video0` exists
- **Fix**: Reconnect USB camera or enable Pi camera
- **Backup**: System will work with mock photos

#### Web interface not loading
- **Check**: Both backend and frontend services running
- **Fix**: Restart with `./start-demo.sh`
- **Backup**: Use direct API endpoints for demo

#### Signatures failing verification
- **Check**: Secure element initialization in logs
- **Fix**: Restart system to reinitialize
- **Backup**: Mock signatures will show verification

### Demo Recovery Strategies

#### If hardware fails:
1. Switch to "simulated mode" in backend
2. Use manual capture exclusively
3. Focus on web interface and verification features

#### If captures are slow:
1. Pre-capture some photos before demo
2. Use manual capture button
3. Show existing data in gallery

#### If verification fails:
1. Use the bulk "Verify All" first
2. Focus on successful verifications
3. Explain the security benefit of catching failures

---

## Demo Checklist

### Before Starting
- Hardware connected and tested
- Services started with `./start-demo.sh`
- Web interface accessible
- At least one test capture successful
- Verification working

### During Demo
- System status shows all green
- Sensor tap triggers capture
- Photos load in gallery
- Verification shows success
- Explained key value propositions

### After Demo
- Answer technical questions
- Show API documentation
- Discuss integration possibilities
- Provide next steps

---

## Key Talking Points

### Technical Differentiators
- **Hardware-backed security** using secure elements
- **Interrupt-driven capture** for real-time response
- **Multi-sensor fusion** with synchronized timestamps
- **Edge computing** with local cryptographic verification

### Business Value
- **Compliance ready** for regulated industries
- **Audit automation** reduces manual verification costs
- **Data integrity** enables new IoT use cases
- **Tamper detection** provides legal-grade evidence

### Market Positioning
- **First-to-market** power-based provenance
- **Developer-friendly** with complete SDKs
- **Enterprise ready** with security certifications
- **Robotics focused** with ROS integration

---

## Audience-Specific Variations

### For Developers
- Show API documentation
- Demonstrate WebSocket real-time updates
- Explain SDK integration
- Focus on technical architecture

### For Business Leaders
- Emphasize ROI and compliance benefits
- Show audit trail capabilities
- Discuss market opportunities
- Focus on competitive advantages

### For Security Teams
- Deep dive into cryptographic verification
- Show signature technical details
- Explain tamper detection
- Discuss threat model

### For IoT Engineers
- Show sensor integration
- Explain interrupt handling
- Demonstrate data correlation
- Focus on deployment scenarios

---

## Success Metrics

### Demo Effectiveness
- Audience engaged throughout 5 minutes
- All key features demonstrated successfully
- Technical questions answered confidently
- Next steps identified

### Follow-up Actions
- Contact information exchanged
- Demo code shared
- Integration discussion scheduled
- Pilot opportunity identified

---

**Remember: The goal is to show the complete value proposition in 5 minutes while leaving room for deeper technical discussion afterward!**